"""
Views for the app.

This file contains the view functions that handle requests and responses
"""
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from .models import Organization, Auditor, Audit, Measurement
from rest_framework.decorators import api_view, permission_classes
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
import earthaccess
import hashlib
import json
import logging
import numpy as np
import os
import redis
import xarray as xr
from datetime import datetime, timezone, timedelta

# Utility: parse request body safely
def parse_body(request):
    if request.body:
        try:
            return json.loads(request.body.decode("utf-8"))
        except Exception:
            return {}
    return {}

# ---------------- USER ----------------
@api_view(["POST"])
@permission_classes([AllowAny])
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is not None:
        token, _ = Token.objects.get_or_create(user=user)
        
        role = None
        if hasattr(user, 'organization'):
            role = 'organization'
        elif hasattr(user, 'auditor'):
            role = 'auditor'

        return Response({
            "success": True,
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role
        })
    else:
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(["POST"])
@permission_classes([AllowAny])  # allow anyone to register
def signup_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    email = request.data.get("email")
    role = request.data.get("role")  # must be "organization" or "auditor"

    if not username or not password or not role:
        return Response(
            {"error": "username, password, and role are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if role not in ["organization", "auditor"]:
        return Response(
            {"error": "role must be either 'organization' or 'auditor'"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already taken"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Create the user
    user = User.objects.create_user(username=username, password=password, email=email)

    # Attach the user to exactly one role
    if role == "organization":
        Organization.objects.create(user=user)
    elif role == "auditor":
        Auditor.objects.create(user=user)

    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {
            "success": True,
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role,
        },
        status=status.HTTP_201_CREATED,
    )

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # You can also add custom claims here if you want
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        # Add extra responses here
        data["user_id"] = self.user.id
        data["username"] = self.user.username
        data["email"] = self.user.email
        return data

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

# ---------------- ORGANIZATION ----------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def organization_list(request):
    if request.method == "GET":
        data = list(Organization.objects.values("id", "user_id"))
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        user = get_object_or_404(User, id=body.get("user_id"))
        org = Organization.objects.create(user=user)
        return JsonResponse({"id": org.id, "user_id": org.user.id})


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def organization_detail(request, pk):
    org = get_object_or_404(Organization, pk=pk)

    if request.method == "GET":
        return JsonResponse({"id": org.id, "user_id": org.user.id})

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "user_id" in body:
            org.user = get_object_or_404(User, id=body["user_id"])
        org.save()
        return JsonResponse({"id": org.id, "user_id": org.user.id})

    elif request.method == "DELETE":
        org.delete()
        return JsonResponse({"deleted": True})


# ---------------- AUDITOR ----------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def auditor_list(request):
    if request.method == "GET":
        data = list(Auditor.objects.values("id", "user_id"))
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        user = get_object_or_404(User, id=body.get("user_id"))
        auditor = Auditor.objects.create(user=user)
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def auditor_detail(request, pk):
    auditor = get_object_or_404(Auditor, pk=pk)

    if request.method == "GET":
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "user_id" in body:
            auditor.user = get_object_or_404(User, id=body["user_id"])
        auditor.save()
        return JsonResponse({"id": auditor.id, "user_id": auditor.user.id})

    elif request.method == "DELETE":
        auditor.delete()
        return JsonResponse({"deleted": True})

from .models import Site, Region

# ---------------- SITE ----------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def site_list(request):
    if request.method == "GET":
        # Return all sites as JSON
        data = [
            {
                "id": s.id,
                "organization_id": s.organization_id,
                "region": {"lat": s.region.lat, "lon": s.region.lon} if s.region else None,
            }
            for s in Site.objects.all()
        ]
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        region_data = body.get("region")
        if not region_data or "lat" not in region_data or "lon" not in region_data:
            return JsonResponse({"error": "region with lat and lon is required"}, status=400)
        
        region, _ = Region.objects.get_or_create(
            lat=region_data["lat"],
            lon=region_data["lon"]
        )

        site = Site.objects.create(
            region=region,
            organization_id=body.get("organization_id"),
        )
        return JsonResponse({"id": site.id})
    

@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def site_detail(request, pk):
    site = get_object_or_404(Site, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": site.id,
            "organization_id": site.organization_id,
            "region": {"lat": site.region.lat, "lon": site.region.lon} if site.region else None,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        if "organization_id" in body:
            site.organization_id = body["organization_id"]
        if "region" in body:
            region_data = body.get("region")
            if region_data and "lat" in region_data and "lon" in region_data:
                region, _ = Region.objects.get_or_create(
                    lat=region_data["lat"],
                    lon=region_data["lon"]
                )
                site.region = region
        site.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        site.delete()
        return JsonResponse({"deleted": True})


# ---------------- AUDIT ----------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def audit_list(request):
    if request.method == "GET":
        data = list(Audit.objects.values())
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        audit = Audit.objects.create(
            score=body.get("score"),
            max_score=body.get("max_score"),
            is_passing=body.get("is_passing", False),
            notes=body.get("notes", ""),
            organization_id=body.get("organization_id"),
            auditor_id=body.get("auditor_id"),
        )
        return JsonResponse({"id": audit.id})


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def audit_detail(request, pk):
    audit = get_object_or_404(Audit, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": audit.id,
            "score": audit.score,
            "max_score": audit.max_score,
            "is_passing": audit.is_passing,
            "notes": audit.notes,
            "organization_id": audit.organization_id,
            "auditor_id": audit.auditor_id,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        for field in ["score", "max_score", "is_passing", "notes", "organization_id", "auditor_id"]:
            if field in body:
                setattr(audit, field, body[field])
        audit.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        audit.delete()
        return JsonResponse({"deleted": True})


# ---------------- MEASUREMENT ----------------
@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def measurement_list(request):
    if request.method == "GET":
        data = list(Measurement.objects.values())
        return JsonResponse(data, safe=False)

    elif request.method == "POST":
        body = parse_body(request)
        region_data = body.get("region")
        if not region_data or "lat" not in region_data or "lon" not in region_data:
            return JsonResponse({"error": "region with lat and lon is required"}, status=400)

        region, _ = Region.objects.get_or_create(
            lat=region_data["lat"],
            lon=region_data["lon"]
        )
        measurement = Measurement.objects.create(
            start_time=body.get("start_time"),
            end_time=body.get("end_time"),
            region=region,
            organization_id=body.get("organization_id"),
        )
        return JsonResponse({"id": measurement.id})


@api_view(["GET", "POST", "DELETE"])
@permission_classes([IsAuthenticated])
def measurement_detail(request, pk):
    measurement = get_object_or_404(Measurement, pk=pk)

    if request.method == "GET":
        return JsonResponse({
            "id": measurement.id,
            "start_time": measurement.start_time,
            "end_time": measurement.end_time,
            "region": {"lat": measurement.region.lat, "lon": measurement.region.lon} if measurement.region else None,
            "organization_id": measurement.organization_id,
        })

    elif request.method == "POST":  # update
        body = parse_body(request)
        for field in ["start_time", "end_time", "organization_id"]:
            if field in body:
                setattr(measurement, field, body[field])
        if "region" in body:
            region_data = body.get("region")
            if region_data and "lat" in region_data and "lon" in region_data:
                region, _ = Region.objects.get_or_create(
                    lat=region_data["lat"],
                    lon=region_data["lon"]
                )
                measurement.region = region
        measurement.save()
        return JsonResponse({"updated": True})

    elif request.method == "DELETE":
        measurement.delete()
        return JsonResponse({"deleted": True})
    
# --- NASA EARTHDATA API PROXY ---
# --- Configuration ---
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
CACHE_EXPIRY = int(os.environ.get('CACHE_EXPIRY', 3600))  # 1 hour default

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
auth = earthaccess.login()
if not auth.authenticated:
    auth = earthaccess.login(strategy='netrc')

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

def fetch_tempo_data(lat_bounds, lon_bounds, start_date, end_date):
    """Fetch TEMPO NO2, HCHO, and O3 data for given bounds and time range"""
    
    logger.info(f"Searching for TEMPO data...")
    logger.info(f"  Time range: {start_date} to {end_date}")
    logger.info(f"  Lat bounds: {lat_bounds}")
    logger.info(f"  Lon bounds: {lon_bounds}")
    
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

def extract_map_data(data_array):
    """Extract map data as 3D array with [longitude, latitude, quantity] format"""
    # Get the data values and coordinates
    data_values = data_array.values
    lat_coords = data_array.coords['latitude'].values
    lon_coords = data_array.coords['longitude'].values
    
    # Create a 3D array: each element is [longitude, latitude, quantity]
    result = []
    
    # Iterate through the data array
    # Handle both 1D and 2D data arrays
    if len(data_values.shape) == 1:
        # 1D array - single dimension (either lat or lon)
        for i, val in enumerate(data_values):
            if i < len(lat_coords) and i < len(lon_coords):
                lon = float(lon_coords[i]) if i < len(lon_coords) else float(lon_coords[0])
                lat = float(lat_coords[i]) if i < len(lat_coords) else float(lat_coords[0])
                quantity = None if np.isnan(val) else float(val)
                result.append([lon, lat, quantity])
    else:
        # 2D array - lat x lon grid
        for i, lat in enumerate(lat_coords):
            for j, lon in enumerate(lon_coords):
                # Access the data value at this grid point
                if i < data_values.shape[0] and j < data_values.shape[1]:
                    val = data_values[i, j]
                    quantity = None if np.isnan(val) else float(val)
                    result.append([float(lon), float(lat), quantity])
    
    return result

# --- API Endpoints ---

@api_view(['GET'])
@permission_classes([])
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'redis_connected': cache is not None and cache.ping(),
        'earthdata_authenticated': auth.authenticated
    })

@api_view(['GET'])
@permission_classes([])
def get_current_map(request):
    """
    Get a map of NO2 data for a 10km radius around given coordinates for the current day.
    
    Query parameters:
    - lat: Latitude (required)
    - lon: Longitude (required)
    """
    try:
        lat_str = request.GET.get('lat')
        lon_str = request.GET.get('lon')
        
        if lat_str is None or lon_str is None:
            return JsonResponse({'error': 'lat and lon parameters are required'}, status=400)
        
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return JsonResponse({'error': 'lat and lon must be valid numbers'}, status=400)
        
        if not (-90 <= lat <= 90):
            return JsonResponse({'error': 'lat must be between -90 and 90'}, status=400)
        
        if not (-180 <= lon <= 180):
            return JsonResponse({'error': 'lon must be between -180 and 180'}, status=400)
        
        # Define time range: from this day a year ago
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=365)
        end_date = now - timedelta(days=364)
        
        # Calculate bounds
        lat_bounds, lon_bounds = lat_lon_to_bounds(lat, lon, radius_km=10)
        
        # Generate cache key (using date only, without time)
        cache_params = {
            'lat': lat,
            'lon': lon,
            'start': start_date.strftime("%Y-%m-%d"),
            'end': end_date.strftime("%Y-%m-%d"),
            'endpoint': 'current_map'
        }
        cache_key = generate_cache_key(cache_params)
        
        # Try to get data from cache
        cached_data = get_from_cache(cache_key)
        if cached_data:
            return JsonResponse(cached_data)
        
        # If not in cache, fetch from NASA Earthdata
        lat_bounds, lon_bounds = lat_lon_to_bounds(lat, lon)
        
        # Fetch data
        logger.info(f"Fetching data for lat={lat}, lon={lon}, date range={start_date} to {end_date}")
        all_datasets = fetch_tempo_data(
            lat_bounds, lon_bounds,
            start_date.strftime("%Y-%m-%d %H:%M"),
            end_date.strftime("%Y-%m-%d %H:%M")
        )
        
        if all_datasets is None or len(all_datasets) == 0:
            return JsonResponse({'error': 'No data found for the specified parameters'}, status=404)
        
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
            return JsonResponse({'error': 'No valid data variables found in datasets'}, status=404)
        
        # Extract map data for all products
        map_data = {}
        for product_name, dataset in all_datasets.items():
            logger.info(f"Extracting map data for {product_name}...")
            temporal_mean_ds = dataset.mean(dim="time")
            
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
                map_data[product_name] = extract_map_data(mean_column)
                logger.info(f"Map data extracted successfully for {product_name}")
        
        # Prepare response
        response_data = {
            'latitude': lat,
            'longitude': lon,
            'radius_km': 10,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'map_data': map_data,
            'products': product_data
        }
        
        # Cache the response
        save_to_cache(cache_key, response_data)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_current_map: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([])
def get_data_range(request):
    """
    Get NO2 data for a 10km radius around given coordinates for a date range.
    
    Query parameters:
    - lat: Latitude (required)
    - lon: Longitude (required)
    - start_date: Start date in ISO format YYYY-MM-DD (required)
    - end_date: End date in ISO format YYYY-MM-DD (required)
    """
    try:
        lat_str = request.GET.get('lat')
        lon_str = request.GET.get('lon')
        start_date_str = request.GET.get('start_date')
        end_date_str = request.GET.get('end_date')
        
        if lat_str is None or lon_str is None or start_date_str is None or end_date_str is None:
            return JsonResponse({'error': 'lat, lon, start_date, and end_date parameters are required'}, status=400)
        
        try:
            lat = float(lat_str)
            lon = float(lon_str)
        except ValueError:
            return JsonResponse({'error': 'lat and lon must be valid numbers'}, status=400)
        
        if not (-90 <= lat <= 90):
            return JsonResponse({'error': 'lat must be between -90 and 90'}, status=400)
        
        if not (-180 <= lon <= 180):
            return JsonResponse({'error': 'lon must be between -180 and 180'}, status=400)
        
        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid date format. Use ISO format YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS'}, status=400)
        
        if start_date > end_date:
            return JsonResponse({'error': 'start_date must be before end_date'}, status=400)
        
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
            return JsonResponse(cached_data)
        
        # Fetch data
        logger.info(f"Fetching data for lat={lat}, lon={lon}, date range={start_date} to {end_date}")
        all_datasets = fetch_tempo_data(
            lat_bounds, lon_bounds,
            start_date.strftime("%Y-%m-%d %H:%M"),
            end_date.strftime("%Y-%m-%d %H:%M")
        )
        
        if all_datasets is None or len(all_datasets) == 0:
            return JsonResponse({'error': 'No data found for the specified parameters'}, status=404)
        
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
            return JsonResponse({'error': 'No valid data variables found in datasets'}, status=404)
        
        # Extract map data for all products
        map_data = {}
        for product_name, dataset in all_datasets.items():
            logger.info(f"Extracting map data for {product_name}...")
            temporal_mean_ds = dataset.mean(dim="time")
            
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
                map_data[product_name] = extract_map_data(mean_column)
                logger.info(f"Map data extracted successfully for {product_name}")
        
        # Prepare response
        response_data = {
            'latitude': lat,
            'longitude': lon,
            'radius_km': 10,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'map_data': map_data,
            'products': product_data
        }
        
        # Cache the response
        save_to_cache(cache_key, response_data)
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in get_data_range: {e}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
