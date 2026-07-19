import requests
import logging

logger = logging.getLogger(__name__)

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL   = "https://api.open-meteo.com/v1/forecast"


def get_coordinates(city_name):
    """
    Converts a city name to latitude and longitude.
    Uses India country bias for better small-city coverage.
    """
    try:
        # Try with India country code first
        response = requests.get(
            GEOCODING_URL,
            params={
                "name":        city_name,
                "count":       1,
                "language":    "en",
                "format":      "json",
                "countryCode": "IN",
            },
            timeout=10,
        )
        response.raise_for_status()
        data    = response.json()
        results = data.get("results")

        # If not found with India bias, try globally
        if not results:
            response = requests.get(
                GEOCODING_URL,
                params={
                    "name":     city_name,
                    "count":    1,
                    "language": "en",
                    "format":   "json",
                },
                timeout=10,
            )
            response.raise_for_status()
            data    = response.json()
            results = data.get("results")

        if not results:
            return None, None, f"City '{city_name}' not found. Try adding the district or state name."

        result = results[0]
        return result["latitude"], result["longitude"], result.get("name", city_name)

    except requests.exceptions.Timeout:
        return None, None, "Geocoding request timed out."
    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None, None, str(e)


def get_weather(latitude, longitude):
    """
    Fetches current weather and 7-day forecast from Open-Meteo.
    No API key required.
    """
    try:
        params = {
            "latitude":  latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "wind_speed_10m",
                "wind_direction_10m",
                "weather_code",
                "cloud_cover",
                "surface_pressure",
            ],
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "weather_code",
                "wind_speed_10m_max",
            ],
            "timezone":       "Asia/Kolkata",
            "forecast_days":  7,
        }

        response = requests.get(WEATHER_URL, params=params, timeout=15)
        response.raise_for_status()
        return response.json(), None

    except requests.exceptions.Timeout:
        return None, "Weather request timed out."
    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None, str(e)


def get_weather_description(code):
    """Converts WMO weather code to description and emoji."""
    WMO_CODES = {
        0:  ("Clear sky",           "☀️"),
        1:  ("Mainly clear",        "🌤️"),
        2:  ("Partly cloudy",       "⛅"),
        3:  ("Overcast",            "☁️"),
        45: ("Foggy",               "🌫️"),
        48: ("Icy fog",             "🌫️"),
        51: ("Light drizzle",       "🌦️"),
        53: ("Moderate drizzle",    "🌦️"),
        55: ("Dense drizzle",       "🌧️"),
        61: ("Slight rain",         "🌧️"),
        63: ("Moderate rain",       "🌧️"),
        65: ("Heavy rain",          "🌧️"),
        71: ("Slight snow",         "🌨️"),
        73: ("Moderate snow",       "🌨️"),
        75: ("Heavy snow",          "❄️"),
        80: ("Slight showers",      "🌦️"),
        81: ("Moderate showers",    "🌧️"),
        82: ("Violent showers",     "⛈️"),
        95: ("Thunderstorm",        "⛈️"),
        96: ("Thunderstorm + hail", "⛈️"),
        99: ("Thunderstorm + hail", "⛈️"),
    }
    desc, icon = WMO_CODES.get(code, ("Unknown", "🌡️"))
    return desc, icon


def generate_farming_advice(weather_data):
    """Generates farming-specific advice from current weather conditions."""
    current  = weather_data.get("current", {})
    temp     = current.get("temperature_2m", 25)
    humidity = current.get("relative_humidity_2m", 60)
    rain     = current.get("rain", 0)
    wind     = current.get("wind_speed_10m", 0)
    code     = current.get("weather_code", 0)

    advice = []

    if temp > 38:
        advice.append({
            "icon": "🌡️", "type": "warning",
            "text": "Extreme heat — irrigate in early morning or evening. Avoid pesticide spraying.",
        })
    elif temp > 32:
        advice.append({
            "icon": "☀️", "type": "caution",
            "text": "High temperature — increase irrigation frequency. Mulching helps retain moisture.",
        })
    elif temp < 10:
        advice.append({
            "icon": "🌡️", "type": "warning",
            "text": "Cold conditions — protect sensitive crops from frost. Delay transplanting seedlings.",
        })
    else:
        advice.append({
            "icon": "✅", "type": "good",
            "text": "Temperature is suitable for most field operations.",
        })

    if rain > 20 or code in (65, 82, 95, 96, 99):
        advice.append({
            "icon": "🌧️", "type": "warning",
            "text": "Heavy rain — avoid fertilizer or pesticide application. Check field drainage.",
        })
    elif rain > 5 or code in (61, 63, 80, 81):
        advice.append({
            "icon": "🌦️", "type": "caution",
            "text": "Moderate rain — skip irrigation today. Monitor for fungal disease development.",
        })
    elif code in (0, 1):
        advice.append({
            "icon": "☀️", "type": "good",
            "text": "Clear conditions — good day for spraying, harvesting, or field work.",
        })

    if humidity > 85:
        advice.append({
            "icon": "💧", "type": "caution",
            "text": "High humidity — risk of fungal diseases like blight and mildew. Monitor crops closely.",
        })
    elif humidity < 30:
        advice.append({
            "icon": "🏜️", "type": "caution",
            "text": "Low humidity — crops may experience moisture stress. Increase irrigation.",
        })

    if wind > 40:
        advice.append({
            "icon": "💨", "type": "warning",
            "text": "Strong winds — do not spray pesticides. Risk of lodging for tall crops.",
        })
    elif wind > 20:
        advice.append({
            "icon": "🌬️", "type": "caution",
            "text": "Moderate wind — avoid aerial spraying. Check support structures for tall crops.",
        })

    return advice


def _build_forecast(daily):
    """Builds the 7-day forecast list from Open-Meteo daily data."""
    forecast = []
    days = daily.get("time", [])
    for i, day in enumerate(days):
        day_code = daily.get("weather_code", [0] * 7)
        day_desc, day_icon = get_weather_description(
            day_code[i] if i < len(day_code) else 0
        )
        forecast.append({
            "date":          day,
            "temp_max":      daily.get("temperature_2m_max", [])[i] if i < len(daily.get("temperature_2m_max", [])) else None,
            "temp_min":      daily.get("temperature_2m_min", [])[i] if i < len(daily.get("temperature_2m_min", [])) else None,
            "precipitation": daily.get("precipitation_sum", [])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
            "wind_max":      daily.get("wind_speed_10m_max", [])[i] if i < len(daily.get("wind_speed_10m_max", [])) else 0,
            "description":   day_desc,
            "icon":          day_icon,
        })
    return forecast


def fetch_weather_for_city(city_name):
    """
    Main function for city-based weather lookup.
    Called by views.py for ?city= queries.
    """
    lat, lon, resolved_city = get_coordinates(city_name)
    if lat is None:
        return None, resolved_city

    weather_data, error = get_weather(lat, lon)
    if weather_data is None:
        return None, error

    current = weather_data.get("current", {})
    code    = current.get("weather_code", 0)
    description, icon = get_weather_description(code)

    return {
        "city":      resolved_city,
        "latitude":  lat,
        "longitude": lon,
        "current": {
            "temperature":    current.get("temperature_2m"),
            "feels_like":     current.get("apparent_temperature"),
            "humidity":       current.get("relative_humidity_2m"),
            "rain":           current.get("rain", 0),
            "precipitation":  current.get("precipitation", 0),
            "wind_speed":     current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "cloud_cover":    current.get("cloud_cover"),
            "pressure":       current.get("surface_pressure"),
            "description":    description,
            "icon":           icon,
            "weather_code":   code,
        },
        "forecast":       _build_forecast(weather_data.get("daily", {})),
        "farming_advice": generate_farming_advice(weather_data),
    }, None


def fetch_weather_for_coordinates(latitude, longitude):
    """
    Fetches weather using GPS coordinates.
    Does reverse geocoding to get the actual city name.
    """
    # Reverse geocode to get city name
    try:
        response = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={
                "lat":    latitude,
                "lon":    longitude,
                "format": "json",
            },
            headers={"User-Agent": "CropGuardAI/1.0"},
            timeout=5,
        )
        data = response.json()
        address = data.get("address", {})
        city_name = (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("county")
            or "Current Location"
        )
    except Exception:
        city_name = "Current Location"

    weather_data, error = get_weather(latitude, longitude)
    if weather_data is None:
        return None, error

    current = weather_data.get("current", {})
    code    = current.get("weather_code", 0)
    description, icon = get_weather_description(code)

    return {
        "city":      city_name,
        "latitude":  latitude,
        "longitude": longitude,
        "current": {
            "temperature":    current.get("temperature_2m"),
            "feels_like":     current.get("apparent_temperature"),
            "humidity":       current.get("relative_humidity_2m"),
            "rain":           current.get("rain", 0),
            "precipitation":  current.get("precipitation", 0),
            "wind_speed":     current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "cloud_cover":    current.get("cloud_cover"),
            "pressure":       current.get("surface_pressure"),
            "description":    description,
            "icon":           icon,
            "weather_code":   code,
        },
        "forecast":       _build_forecast(weather_data.get("daily", {})),
        "farming_advice": generate_farming_advice(weather_data),
    }, None