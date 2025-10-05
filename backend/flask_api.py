import base64
import cartopy.crs as ccrs
import earthaccess
import hashlib
import io
import json
import logging
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import os
import redis
import xarray as xr
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from matplotlib import rcParams

rcParams["figure.dpi"] = 80
matplotlib.use('Agg')  # Use non-interactive backend for API

# --- Configuration ---
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
CACHE_EXPIRY = int(os.environ.get('CACHE_EXPIRY', 3600))  # 1 hour default

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Flask App ---
app = Flask(__name__)

# --- Initialization ---
# Connect to Redis instance
try:
    cache = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    cache.ping()
    logger.info("Successfully connected to Redis")
except Exception as e:
    logger.warning(f"Could not connect to Redis: {e}. Caching will be disabled.")
    cache = None

# Earth Access for NASA TEMPO data
auth = earthaccess.login(strategy='environment')
# auth = earthaccess.login()
# if not auth.authenticated:
    # auth = earthaccess.login(strategy='netrc')

if not auth.authenticated:
    raise RuntimeError("Authentication failed. Please check your Earthdata credentials.")

# --- Helper Functions ---

def generate_cache_key(params):
    """Generate a unique cache key from parameters"""
    # Round floating point numbers to avoid cache misses due to precision
    rounded_params = {}
    for key, value in params.items():
        if isinstance(value, float):
            rounded_params[key] = round(value, 6)
        else:
            rounded_params[key] = value
    params_str = json.dumps(rounded_params, sort_keys=True)
    return hashlib.md5(params_str.encode()).hexdigest()

def get_from_cache(key):
    """Retrieve data from Redis cache"""
    if cache is None:
        logger.debug("Cache is disabled (Redis not connected)")
        return None
    try:
        data = cache.get(key)
        if data:
            logger.info(f"Cache HIT for key: {key}")
            return json.loads(data)
        else:
            logger.info(f"Cache MISS for key: {key}")
    except Exception as e:
        logger.error(f"Error reading from cache: {e}")
    return None

def save_to_cache(key, data, expiry=CACHE_EXPIRY):
    """Save data to Redis cache"""
    if cache is None:
        return
    try:
        # Check the size of the data before caching
        json_data = json.dumps(data)
        data_size = len(json_data)
        logger.info(f"Attempting to cache {data_size} bytes with key: {key}")
        
        # Redis has a max value size (default 512MB, but large values are slow)
        # Warn if data is large
        if data_size > 10_000_000:  # 10MB
            logger.warning(f"Cache data is very large ({data_size} bytes), this may be slow")
        
        cache.setex(key, expiry, json_data)
        logger.info(f"Successfully saved to cache with key: {key}")
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")

def lat_lon_to_bounds(lat, lon, radius_km=10):
    """
    Convert lat/lon and radius to bounding box.
    Approximation: 1 degree latitude ≈ 111 km, longitude varies by latitude
    """
    lat_offset = radius_km / 111.0
    lon_offset = radius_km / (111.0 * np.cos(np.radians(lat)))
    
    lat_bounds = (lat - lat_offset, lat + lat_offset)
    lon_bounds = (lon - lon_offset, lon + lon_offset)
    
    return lat_bounds, lon_bounds

def fetch_tempo_data(lat_bounds, lon_bounds, start_date, end_date, count=10):
    """Fetch TEMPO NO2, HCHO, and O3 data for given bounds and time range"""
    
    logger.info(f"Searching for TEMPO data...")
    logger.info(f"  Time range: {start_date} to {end_date}")
    logger.info(f"  Lat bounds: {lat_bounds}")
    logger.info(f"  Lon bounds: {lon_bounds}")
    logger.info(f"  Max granules: {count}")
    
    products = {
        "NO2": "TEMPO_NO2_L3",
        "HCHO": "TEMPO_HCHO_L3",
        "O3": "TEMPO_O3_L3"
    }
    
    all_datasets = {}
    
    open_options = {
        "access": "indirect",  # access to cloud data (faster in AWS with "direct")
        "load": True,  # Load metadata immediately (required for indexing)
        "concat_dim": "time",  # Concatenate files along the time dimension
        "data_vars": "minimal",  # Only load data variables that include the concat_dim
        "coords": "minimal",  # Only load coordinate variables that include the concat_dim
        "compat": "override",  # Avoid coordinate conflicts by picking the first
        "combine_attrs": "override",  # Avoid attribute conflicts by picking the first
    }
    
    for product_name, short_name in products.items():
        logger.info(f"Processing {product_name} ({short_name})...")
        
        # Search data granules
        results = earthaccess.search_data(
            short_name=short_name,
            version="V03",
            temporal=(start_date, end_date),
            count=count,
        )
        
        logger.info(f"  Number of {product_name} granules found: {len(results)}")
        
        if len(results) == 0:
            logger.warning(f"No {product_name} granules found for the specified parameters")
            continue
        
        logger.info(f"  Opening {product_name} datasets...")
        
        logger.info(f"    Opening {product_name} root dataset...")
        result_root = earthaccess.open_virtual_mfdataset(granules=results, **open_options)
        
        logger.info(f"    Opening {product_name} product dataset...")
        result_product = earthaccess.open_virtual_mfdataset(
            granules=results, group="product", **open_options
        )
        
        logger.info(f"    Opening {product_name} geolocation dataset...")
        result_geolocation = earthaccess.open_virtual_mfdataset(
            granules=results, group="geolocation", **open_options
        )
        
        # Merge datasets
        logger.info(f"  Merging {product_name} datasets...")
        result_merged = xr.merge([result_root, result_product, result_geolocation])
        
        # Subset by location
        logger.info(f"  Subsetting {product_name} by location and quality...")
        subset_ds = result_merged.sel(
            {
                "longitude": slice(lon_bounds[0], lon_bounds[1]),
                "latitude": slice(lat_bounds[0], lat_bounds[1]),
            }
        ).where(result_merged["main_data_quality_flag"] == 0)
        
        logger.info(f"  {product_name} subset complete. Data shape: {subset_ds.dims}")
        all_datasets[product_name] = subset_ds
    
    if len(all_datasets) == 0:
        logger.warning("No datasets found for any product")
        return None
    
    return all_datasets

def create_map_image(data_array, lat_bounds, lon_bounds):
    """Create a map visualization and return as base64 encoded PNG"""
    fig, ax = plt.subplots(figsize=(10, 8), subplot_kw={"projection": ccrs.PlateCarree()})
    
    data_array.squeeze().plot.contourf(ax=ax, cmap='YlOrRd', levels=15)
    
    # Add geographic features
    ax.coastlines()
    ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
    
    # Set extent
    ax.set_extent([lon_bounds[0], lon_bounds[1], lat_bounds[0], lat_bounds[1]])
    
    plt.title('TEMPO NO2 Tropospheric Column')
    
    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    buf.seek(0)
    plt.close(fig)
    
    # Encode as base6
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return img_base64

# --- API Endpoints ---

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'redis_connected': cache is not None and cache.ping(),
        'earthdata_authenticated': auth.authenticated
    })

@app.route('/api/map/current', methods=['GET'])
def get_current_map():
    """
    Get a map of NO2 data for a 50km radius around given coordinates for the current day.
    
    Query parameters:
    - lat: Latitude (required)
    - lon: Longitude (required)
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        if lat is None or lon is None:
            return jsonify({'error': 'lat and lon parameters are required'}), 400
        
        if not (-90 <= lat <= 90):
            return jsonify({'error': 'lat must be between -90 and 90'}), 400
        
        if not (-180 <= lon <= 180):
            return jsonify({'error': 'lon must be between -180 and 180'}), 400
        
        # Define time range: from this day a year ago
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=365)
        end_date = now - timedelta(days=364)
        
        # Calculate bounds
        lat_bounds, lon_bounds = lat_lon_to_bounds(lat, lon, radius_km=50)
        
        # Generate cache key (using date only, without time)
        cache_params = {
            'lat': lat,
            'lon': lon,
            'start': start_date.strftime("%Y-%m-%d"),
            'end': end_date.strftime("%Y-%m-%d"),
            'endpoint': 'current_map'
        }
        cache_key = generate_cache_key(cache_params)
        
        # Check cache
        cached_data = get_from_cache(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Fetch data
        logger.info(f"Fetching data for lat={lat}, lon={lon}, date range={start_date} to {end_date}")
        all_datasets = fetch_tempo_data(
            lat_bounds, lon_bounds,
            start_date.strftime("%Y-%m-%d %H:%M"),
            end_date.strftime("%Y-%m-%d %H:%M")
        )
        
        if all_datasets is None or len(all_datasets) == 0:
            return jsonify({'error': 'No data found for the specified parameters'}), 404
        
        # Process each product
        logger.info("Computing temporal means for all products...")
        product_data = {}
        
        for product_name, subset_ds in all_datasets.items():
            logger.info(f"Processing {product_name}...")
            temporal_mean_ds = subset_ds.mean(dim="time")
            
            # Get the appropriate variable name for each product
            if product_name == "NO2":
                var_name = "vertical_column_troposphere"
            elif product_name == "HCHO":
                var_name = "vertical_column"
            elif product_name == "O3":
                var_name = "vertical_column_troposphere"
            else:
                continue
            
            if var_name in temporal_mean_ds:
                mean_column = temporal_mean_ds[var_name].compute()
                
                product_data[product_name] = {
                    'mean_value': float(mean_column.mean().values),
                    'min_value': float(mean_column.min().values),
                    'max_value': float(mean_column.max().values),
                    'data_points': int(subset_ds.sizes.get('time', 0)),
                    'units': 'molecules/cm^2'
                }
        
        if len(product_data) == 0:
            return jsonify({'error': 'No valid data variables found in datasets'}), 404
        
        # Create map image for NO2 (default) if available
        img_base64 = None
        if "NO2" in all_datasets:
            logger.info("Creating map image for NO2...")
            no2_ds = all_datasets["NO2"]
            temporal_mean_ds = no2_ds.mean(dim="time")
            mean_vertical_column = temporal_mean_ds["vertical_column_troposphere"].compute()
            img_base64 = create_map_image(mean_vertical_column, lat_bounds, lon_bounds)
            logger.info("Map image created successfully")
        
        # Prepare response
        response_data = {
            'latitude': lat,
            'longitude': lon,
            'radius_km': 50,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'map_image': img_base64,
            'products': product_data
        }
        
        # Cache the response
        save_to_cache(cache_key, response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_current_map: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/range', methods=['GET'])
def get_data_range():
    """
    Get NO2 data for a 10km radius around given coordinates for a date range.
    
    Query parameters:
    - lat: Latitude (required)
    - lon: Longitude (required)
    - start_date: Start date in ISO format YYYY-MM-DD (required)
    - end_date: End date in ISO format YYYY-MM-DD (required)
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if lat is None or lon is None or start_date_str is None or end_date_str is None:
            return jsonify({'error': 'lat, lon, start_date, and end_date parameters are required'}), 400
        
        if not (-90 <= lat <= 90):
            return jsonify({'error': 'lat must be between -90 and 90'}), 400
        
        if not (-180 <= lon <= 180):
            return jsonify({'error': 'lon must be between -180 and 180'}), 400
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use ISO format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS'}), 400
        
        if start_date > end_date:
            return jsonify({'error': 'start_date must be before end_date'}), 400
        
        # Calculate bounds
        lat_bounds, lon_bounds = lat_lon_to_bounds(lat, lon, radius_km=10)
        
        # Generate cache key (using date only, without time)
        cache_params = {
            'lat': lat,
            'lon': lon,
            'start': start_date.strftime("%Y-%m-%d"),
            'end': end_date.strftime("%Y-%m-%d"),
            'endpoint': 'data_range'
        }
        cache_key = generate_cache_key(cache_params)
        
        # Check cache
        cached_data = get_from_cache(cache_key)
        if cached_data:
            return jsonify(cached_data)
        
        # Fetch data
        logger.info(f"Fetching data for lat={lat}, lon={lon}, date range={start_date} to {end_date}")
        all_datasets = fetch_tempo_data(
            lat_bounds, lon_bounds,
            start_date.strftime("%Y-%m-%d %H:%M"),
            end_date.strftime("%Y-%m-%d %H:%M")
        )
        
        if all_datasets is None or len(all_datasets) == 0:
            return jsonify({'error': 'No data found for the specified parameters'}), 404
        
        # Process each product
        logger.info("Computing temporal means and time series for all products...")
        product_data = {}
        
        for product_name, subset_ds in all_datasets.items():
            logger.info(f"Processing {product_name}...")
            
            # Get the appropriate variable name for each product
            if product_name == "NO2":
                var_name = "vertical_column_troposphere"
            elif product_name == "HCHO":
                var_name = "vertical_column"
            elif product_name == "O3":
                var_name = "vertical_column_troposphere"
            else:
                continue
            
            if var_name not in subset_ds:
                logger.warning(f"Variable {var_name} not found in {product_name} dataset")
                continue
            
            # Calculate temporal mean
            temporal_mean_ds = subset_ds.mean(dim="time")
            mean_column = temporal_mean_ds[var_name].compute()
            
            # Extract time series data
            time_series_data = []
            if 'time' in subset_ds.dims:
                for t in subset_ds.time.values:
                    time_slice = subset_ds.sel(time=t)[var_name].compute()
                    time_series_data.append({
                        'time': str(t),
                        'mean_value': float(time_slice.mean().values),
                        'min_value': float(time_slice.min().values),
                        'max_value': float(time_slice.max().values)
                    })
            
            product_data[product_name] = {
                'temporal_mean': float(mean_column.mean().values),
                'temporal_min': float(mean_column.min().values),
                'temporal_max': float(mean_column.max().values),
                'data_points': int(subset_ds.sizes.get('time', 0)),
                'time_series': time_series_data,
                'units': 'molecules/cm^2'
            }
        
        if len(product_data) == 0:
            return jsonify({'error': 'No valid data variables found in datasets'}), 404
        
        # Create map image for NO2 (default) if available
        img_base64 = None
        if "NO2" in all_datasets:
            logger.info("Creating map image for NO2...")
            no2_ds = all_datasets["NO2"]
            temporal_mean_ds = no2_ds.mean(dim="time")
            mean_vertical_column = temporal_mean_ds["vertical_column_troposphere"].compute()
            img_base64 = create_map_image(mean_vertical_column, lat_bounds, lon_bounds)
            logger.info("Map image created successfully")
        
        # Prepare response
        response_data = {
            'latitude': lat,
            'longitude': lon,
            'radius_km': 10,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'map_image': img_base64,
            'products': product_data
        }
        
        # Cache the response
        save_to_cache(cache_key, response_data)
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_data_range: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

# --- Run Server ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
