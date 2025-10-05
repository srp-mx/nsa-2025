# TEMPO Air Quality Data API

This API provides access to NASA's TEMPO (Tropospheric Emissions: Monitoring of Pollution) satellite data for air quality monitoring. It delivers data for three key pollutants: NO2 (Nitrogen Dioxide), HCHO (Formaldehyde), and O3 (Ozone).

## Base URL

```
http://16.144.69.113:8000
```

## Django API Endpoints

These endpoints are for user management and other application-specific data.

### Authentication

#### Signup

Create a new user account.

**Endpoint:** `POST /auth/signup/`

**Request Body:**
```json
{
  "username": "newuser",
  "password": "securepassword123",
  "email": "user@example.com",
  "role": "organization" 
}
```
*`role` can be "organization" or "auditor".*

**Example Response:**
```json
{
  "success": true,
  "token": "your_auth_token",
  "user_id": 1,
  "username": "newuser",
  "email": "user@example.com",
  "role": "organization"
}
```

#### Login

Authenticate and receive a token.

**Endpoint:** `POST /auth/login/`

**Request Body:**
```json
{
  "username": "testuser",
  "password": "password"
}
```

**Example Response:**
```json
{
    "success": true,
    "token": "your_auth_token",
    "user_id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "role": "organization"
}
```

#### Refresh Token

Obtain a new access token using a refresh token.

**Endpoint:** `POST /auth/refresh/`

**Request Body:**
```json
{
  "refresh": "your_refresh_token"
}
```

**Example Response:**
```json
{
  "access": "new_access_token"
}
```

#### Logout

Blacklist a refresh token to log out.

**Endpoint:** `POST /auth/logout/`

**Request Body:**
```json
{
  "refresh": "your_refresh_token"
}
```
*On success, this returns a `204 No Content` response.*

---

### Organizations

Endpoints for managing organizations. Authentication is required.

- **`GET /organizations/`**: List all organizations.
- **`POST /organizations/`**: Create a new organization.
  - **Body**: `{ "user_id": <user_id> }`
- **`GET /organizations/<id>/`**: Retrieve a specific organization.
- **`POST /organizations/<id>/`**: Update an organization.
  - **Body**: `{ "user_id": <new_user_id> }`
- **`DELETE /organizations/<id>/`**: Delete an organization.

---

### Auditors

Endpoints for managing auditors. Authentication is required.

- **`GET /auditors/`**: List all auditors.
- **`POST /auditors/`**: Create a new auditor.
  - **Body**: `{ "user_id": <user_id> }`
- **`GET /auditors/<id>/`**: Retrieve a specific auditor.
- **`POST /auditors/<id>/`**: Update an auditor.
  - **Body**: `{ "user_id": <new_user_id> }`
- **`DELETE /auditors/<id>/`**: Delete an auditor.

---

### Sites

Endpoints for managing sites. Authentication is required.

- **`GET /sites/`**: List all sites.
- **`POST /sites/`**: Create a new site.
  - **Body**: `{ "organization_id": <org_id>, "region": { "lat": 34.05, "lon": -118.24 } }`
- **`GET /sites/<id>/`**: Retrieve a specific site.
- **`POST /sites/<id>/`**: Update a site.
  - **Body**: `{ "organization_id": <new_org_id>, "region": { "lat": 35.00, "lon": -119.00 } }`
- **`DELETE /sites/<id>/`**: Delete a site.

---

### Audits

Endpoints for managing audits. Authentication is required.

- **`GET /audits/`**: List all audits.
- **`POST /audits/`**: Create a new audit.
  - **Body**: `{ "score": 95, "max_score": 100, "is_passing": true, "notes": "Good", "organization_id": 1, "auditor_id": 1 }`
- **`GET /audits/<id>/`**: Retrieve a specific audit.
- **`POST /audits/<id>/`**: Update an audit.
- **`DELETE /audits/<id>/`**: Delete an audit.

---

### Measurements

Endpoints for managing measurements. Authentication is required.

- **`GET /measurements/`**: List all measurements.
- **`POST /measurements/`**: Create a new measurement.
  - **Body**: `{ "start_time": "2024-01-01T00:00:00Z", "end_time": "2024-01-01T01:00:00Z", "region": { "lat": 34.05, "lon": -118.24 }, "organization_id": 1 }`
- **`GET /measurements/<id>/`**: Retrieve a specific measurement.
- **`POST /measurements/<id>/`**: Update a measurement.
- **`DELETE /measurements/<id>/`**: Delete a measurement.

---

## NASA Earthdata API Endpoints

These endpoints provide access to NASA's TEMPO satellite data.

### Health Check

Check if the API is running and connected to required services.

**Endpoint:** `GET /health`

**Example Request:**
```bash
curl http://16.144.69.113:5000/health
```

**Example Response:**
```json
{
  "status": "healthy",
  "redis_connected": true,
  "earthdata_authenticated": true
}
```

---

### Map Data

#### Current Map Data

Get air quality map data for a 50km radius around specified coordinates for the current day (actually fetches data from one year ago due to TEMPO data availability).

**Endpoint:** `GET /api/map/current`

**Query Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lon` (required): Longitude (-180 to 180)

**Example Request:**
```bash
curl "http://16.144.69.113:5000/api/map/current?lat=34.0522&lon=-118.2437"
```

**Example Response:**
```json
{
  "latitude": 34.0522,
  "longitude": -118.2437,
  "radius_km": 50,
  "start_date": "2024-10-05T00:00:00Z",
  "end_date": "2024-10-06T00:00:00Z",
  "map_data": {
    "NO2": {
      "data": [[...]],
      "latitude": [...],
      "longitude": [...],
      "shape": [10, 10]
    },
    "HCHO": { ... },
    "O3": { ... }
  },
  "products": {
    "NO2": {
      "mean_value": 1.5e15,
      "min_value": 1.0e15,
      "max_value": 2.0e15,
      "data_points": 24,
      "units": "molecules/cm^2"
    },
    "HCHO": { ... },
    "O3": { ... }
  }
}
```

---

### Time-Series Data

#### Date Range Data

Get air quality data for a 10km radius around specified coordinates for a custom date range, including time series data.

**Endpoint:** `GET /api/data/range`

**Query Parameters:**
- `lat` (required): Latitude (-90 to 90)
- `lon` (required): Longitude (-180 to 180)
- `start_date` (required): Start date in ISO format (YYYY-MM-DD)
- `end_date` (required): End date in ISO format (YYYY-MM-DD)

**Example Request:**
```bash
curl "http://16.144.69.113:5000/api/data/range?lat=34.0522&lon=-118.2437&start_date=2024-08-01&end_date=2024-08-03"
```

**Example Response:**
```json
{
  "latitude": 34.0522,
  "longitude": -118.2437,
  "radius_km": 10,
  "start_date": "2024-08-01",
  "end_date": "2024-08-03",
  "map_data": {
    "NO2": {
      "data": [[...]],
      "latitude": [...],
      "longitude": [...],
      "shape": [10, 10]
    },
    "HCHO": { ... },
    "O3": { ... }
  },
  "products": {
    "NO2": {
      "temporal_mean": 1.5e15,
      "temporal_min": 1.0e15,
      "temporal_max": 2.0e15,
      "data_points": 48,
      "time_series": [
        {
          "time": "2024-08-01T12:00:00",
          "mean_value": 1.4e15,
          "min_value": 1.0e15,
          "max_value": 1.8e15
        },
        ...
      ],
      "units": "molecules/cm^2"
    },
    "HCHO": { ... },
    "O3": { ... }
  }
}
```

---

## Data Products

The API provides data for three pollutants:

1. **NO2 (Nitrogen Dioxide)**
   - Variable: `vertical_column_troposphere`
   - Primary indicator of air pollution from vehicles and industrial sources

2. **HCHO (Formaldehyde)**
   - Variable: `vertical_column`
   - Indicator of volatile organic compound emissions

3. **O3 (Ozone)**
   - Variable: `vertical_column_troposphere`
   - Important for air quality and human health monitoring

All measurements are in `molecules/cm^2`.

---

## Example Use Cases

### Python Example

```python
import requests

# Get current map data for Los Angeles
response = requests.get(
    'http://16.144.69.113:5000/api/map/current',
    params={
        'lat': 34.0522,
        'lon': -118.2437
    }
)

data = response.json()
print(f"NO2 mean value: {data['products']['NO2']['mean_value']}")
```

### JavaScript Example

```javascript
// Get date range data
fetch('http://16.144.69.113:5000/api/data/range?lat=34.0522&lon=-118.2437&start_date=2024-08-01&end_date=2024-08-03')
  .then(response => response.json())
  .then(data => {
    console.log('NO2 time series:', data.products.NO2.time_series);
  });
```

### curl Example - Major Cities

```bash
# New York City
curl "http://16.144.69.113:5000/api/map/current?lat=40.7128&lon=-74.0060"

# London
curl "http://16.144.69.113:5000/api/map/current?lat=51.5074&lon=-0.1278"

# Tokyo
curl "http://16.144.69.113:5000/api/map/current?lat=35.6762&lon=139.6503"
```

---

## Response Format

### Map Data Structure

The `map_data` object contains gridded spatial data for visualization:

- `data`: 2D array of pollutant concentrations (null values indicate no data)
- `latitude`: Array of latitude coordinates
- `longitude`: Array of longitude coordinates
- `shape`: Dimensions of the data array [rows, columns]

### Product Data Structure

The `products` object contains statistical summaries for each pollutant:

- `mean_value` / `temporal_mean`: Average concentration
- `min_value` / `temporal_min`: Minimum concentration
- `max_value` / `temporal_max`: Maximum concentration
- `data_points`: Number of temporal observations
- `time_series`: Array of time-stamped measurements (range endpoint only)
- `units`: Measurement units (molecules/cm^2)

---

## Error Responses

The API returns appropriate HTTP status codes and error messages:

**400 Bad Request:**
```json
{
  "error": "lat and lon parameters are required"
}
```

**404 Not Found:**
```json
{
  "error": "No data found for the specified parameters"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Error description"
}
```

---

## Caching

The API implements Redis caching to improve performance:
- Cache expiry: 1 hour (default)
- Cached responses are returned immediately
- Cache keys are based on location and date parameters

---

## Rate Limiting & Best Practices

1. **Use appropriate date ranges**: TEMPO data is available from August 2023 onwards
2. **Cache responses**: The API caches results, but you should also cache on your end
3. **Geographic coverage**: TEMPO covers North America, but check data availability for your region
4. **Reasonable requests**: Avoid excessive requests in short time periods

---

## Technical Details

- **Data Source**: NASA TEMPO Level 3 data products (Version V03)
- **Spatial Resolution**: Varies by product (~10km at nadir)
- **Temporal Resolution**: Hourly observations during daylight
- **Geographic Coverage**: Primarily North America
- **Quality Filtering**: Only data with `main_data_quality_flag == 0` is returned

---

## Support & Issues

For questions or issues with the API, please check:
- TEMPO data availability for your region and time period
- Parameter validity (latitude/longitude ranges, date formats)
- Network connectivity to the API endpoint

---

## License & Attribution

This API uses data from NASA's TEMPO mission. Please cite appropriately when using this data in publications or applications.

**Data Citation:**
NASA TEMPO Level 3 Products, Version 3 (V03), accessed via Earthdata Cloud.
