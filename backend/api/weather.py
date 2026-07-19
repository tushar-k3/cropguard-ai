# import requests
# import logging

# logger = logging.getLogger(__name__)

# GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
# WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# def get_coordinates(city_name):
#     """
#     Converts a city name to latitude and longitude.
#     Adds an India country bias for better Indian city and small-town results.
#     If no result is found, retries without the India bias.
#     """
#     try:
#         # Add India bias for better Indian city coverage
#         search_name = city_name

#         if "india" not in city_name.lower():
#             search_name = f"{city_name}, India"

#         # First attempt: search with India bias
#         response = requests.get(
#             GEOCODING_URL,
#             params={
#                 "name": search_name,
#                 "count": 1,
#                 "language": "en",
#                 "format": "json",
#                 "countryCode": "IN",
#             },
#             timeout=10,
#         )

#         response.raise_for_status()
#         data = response.json()

#         results = data.get("results")

#         # Second attempt: search original city name without country restriction
#         if not results:
#             response = requests.get(
#                 GEOCODING_URL,
#                 params={
#                     "name": city_name,
#                     "count": 1,
#                     "language": "en",
#                     "format": "json",
#                 },
#                 timeout=10,
#             )

#             response.raise_for_status()
#             data = response.json()

#             results = data.get("results")

#         if not results:
#             return (
#                 None,
#                 None,
#                 f"City '{city_name}' not found. "
#                 "Try adding the district or state name.",
#             )

#         result = results[0]

#         return (
#             result["latitude"],
#             result["longitude"],
#             result.get("name", city_name),
#         )

#     except requests.exceptions.Timeout:
#         return None, None, "Geocoding request timed out."

#     except requests.exceptions.RequestException as e:
#         logger.error(f"Geocoding API error: {e}")
#         return None, None, f"Could not connect to geocoding service: {e}"

#     except Exception as e:
#         logger.error(f"Geocoding error: {e}")
#         return None, None, str(e)


# def get_weather(latitude, longitude):
#     """
#     Fetches current weather and 7-day forecast from Open-Meteo.
#     No API key is required.
#     """
#     try:
#         params = {
#             "latitude": latitude,
#             "longitude": longitude,
#             "current": [
#                 "temperature_2m",
#                 "relative_humidity_2m",
#                 "apparent_temperature",
#                 "precipitation",
#                 "rain",
#                 "wind_speed_10m",
#                 "wind_direction_10m",
#                 "weather_code",
#                 "cloud_cover",
#                 "surface_pressure",
#             ],
#             "daily": [
#                 "temperature_2m_max",
#                 "temperature_2m_min",
#                 "precipitation_sum",
#                 "weather_code",
#                 "wind_speed_10m_max",
#             ],
#             "timezone": "Asia/Kolkata",
#             "forecast_days": 7,
#         }

#         response = requests.get(
#             WEATHER_URL,
#             params=params,
#             timeout=15,
#         )

#         response.raise_for_status()

#         return response.json(), None

#     except requests.exceptions.Timeout:
#         return None, "Weather request timed out."

#     except requests.exceptions.RequestException as e:
#         logger.error(f"Weather API request error: {e}")
#         return None, f"Could not connect to weather service: {e}"

#     except Exception as e:
#         logger.error(f"Weather API error: {e}")
#         return None, str(e)


# def get_weather_description(code):
#     """
#     Converts WMO weather codes to human-readable descriptions
#     and matching icons.
#     """

#     WMO_CODES = {
#         0: ("Clear sky", "☀️"),
#         1: ("Mainly clear", "🌤️"),
#         2: ("Partly cloudy", "⛅"),
#         3: ("Overcast", "☁️"),
#         45: ("Foggy", "🌫️"),
#         48: ("Icy fog", "🌫️"),
#         51: ("Light drizzle", "🌦️"),
#         53: ("Moderate drizzle", "🌦️"),
#         55: ("Dense drizzle", "🌧️"),
#         61: ("Slight rain", "🌧️"),
#         63: ("Moderate rain", "🌧️"),
#         65: ("Heavy rain", "🌧️"),
#         71: ("Slight snow", "🌨️"),
#         73: ("Moderate snow", "🌨️"),
#         75: ("Heavy snow", "❄️"),
#         80: ("Slight showers", "🌦️"),
#         81: ("Moderate showers", "🌧️"),
#         82: ("Violent showers", "⛈️"),
#         95: ("Thunderstorm", "⛈️"),
#         96: ("Thunderstorm + hail", "⛈️"),
#         99: ("Thunderstorm + hail", "⛈️"),
#     }

#     description, icon = WMO_CODES.get(
#         code,
#         ("Unknown", "🌡️"),
#     )

#     return description, icon


# def generate_farming_advice(weather_data):
#     """
#     Generates farming-specific advice based on current weather.
#     Returns a list of advice dictionaries.
#     """

#     current = weather_data.get("current", {})

#     temp = current.get("temperature_2m", 25)
#     humidity = current.get("relative_humidity_2m", 60)
#     rain = current.get("rain", 0)
#     wind = current.get("wind_speed_10m", 0)
#     code = current.get("weather_code", 0)

#     advice = []

#     # -----------------------------------------
#     # Temperature advice
#     # -----------------------------------------

#     if temp > 38:
#         advice.append({
#             "icon": "🌡️",
#             "type": "warning",
#             "text": (
#                 "Extreme heat — irrigate crops in early morning "
#                 "or evening to reduce stress. Avoid spraying pesticides."
#             ),
#         })

#     elif temp > 32:
#         advice.append({
#             "icon": "☀️",
#             "type": "caution",
#             "text": (
#                 "High temperature — increase irrigation frequency. "
#                 "Mulching is recommended to retain soil moisture."
#             ),
#         })

#     elif temp < 10:
#         advice.append({
#             "icon": "🌡️",
#             "type": "warning",
#             "text": (
#                 "Cold conditions — protect sensitive crops from frost. "
#                 "Delay transplanting of seedlings."
#             ),
#         })

#     else:
#         advice.append({
#             "icon": "✅",
#             "type": "good",
#             "text": (
#                 "Temperature is suitable for most field operations."
#             ),
#         })

#     # -----------------------------------------
#     # Rain / weather advice
#     # -----------------------------------------

#     if rain > 20 or code in (65, 82, 95, 96, 99):
#         advice.append({
#             "icon": "🌧️",
#             "type": "warning",
#             "text": (
#                 "Heavy rain — avoid fertilizer or pesticide application. "
#                 "Check field drainage to prevent waterlogging."
#             ),
#         })

#     elif rain > 5 or code in (61, 63, 80, 81):
#         advice.append({
#             "icon": "🌦️",
#             "type": "caution",
#             "text": (
#                 "Moderate rain expected — skip irrigation today. "
#                 "Monitor for fungal disease development."
#             ),
#         })

#     elif code in (0, 1):
#         advice.append({
#             "icon": "☀️",
#             "type": "good",
#             "text": (
#                 "Clear conditions — good day for spraying, "
#                 "harvesting, or field work."
#             ),
#         })

#     # -----------------------------------------
#     # Humidity advice
#     # -----------------------------------------

#     if humidity > 85:
#         advice.append({
#             "icon": "💧",
#             "type": "caution",
#             "text": (
#                 "High humidity — risk of fungal diseases like blight "
#                 "and mildew. Monitor crops closely."
#             ),
#         })

#     elif humidity < 30:
#         advice.append({
#             "icon": "🏜️",
#             "type": "caution",
#             "text": (
#                 "Low humidity — crops may experience moisture stress. "
#                 "Increase irrigation."
#             ),
#         })

#     # -----------------------------------------
#     # Wind advice
#     # -----------------------------------------

#     if wind > 40:
#         advice.append({
#             "icon": "💨",
#             "type": "warning",
#             "text": (
#                 "Strong winds — do not spray pesticides or fertilizers. "
#                 "Risk of lodging for tall crops."
#             ),
#         })

#     elif wind > 20:
#         advice.append({
#             "icon": "🌬️",
#             "type": "caution",
#             "text": (
#                 "Moderate wind — avoid aerial spraying. "
#                 "Check support structures for tall crops."
#             ),
#         })

#     return advice


# def fetch_weather_for_city(city_name):
#     """
#     Gets weather information for a city name.

#     Process:
#     1. Convert city name to coordinates.
#     2. Fetch weather using coordinates.
#     3. Generate weather descriptions.
#     4. Build 7-day forecast.
#     5. Generate farming advice.

#     Returns:
#         (data, error)
#     """

#     # Get coordinates
#     lat, lon, resolved_city = get_coordinates(city_name)

#     if lat is None:
#         # resolved_city contains the error message in this case
#         return None, resolved_city

#     # Get weather
#     weather_data, error = get_weather(lat, lon)

#     if weather_data is None:
#         return None, error

#     current = weather_data.get("current", {})
#     daily = weather_data.get("daily", {})

#     code = current.get("weather_code", 0)

#     description, icon = get_weather_description(code)

#     # -----------------------------------------
#     # Build 7-day forecast
#     # -----------------------------------------

#     forecast = []

#     days = daily.get("time", [])
#     weather_codes = daily.get("weather_code", [])
#     temp_max_values = daily.get("temperature_2m_max", [])
#     temp_min_values = daily.get("temperature_2m_min", [])
#     precipitation_values = daily.get("precipitation_sum", [])
#     wind_values = daily.get("wind_speed_10m_max", [])

#     for i, day in enumerate(days):

#         day_code = (
#             weather_codes[i]
#             if i < len(weather_codes)
#             else 0
#         )

#         day_desc, day_icon = get_weather_description(
#             day_code
#         )

#         forecast.append({
#             "date": day,

#             "temp_max": (
#                 temp_max_values[i]
#                 if i < len(temp_max_values)
#                 else None
#             ),

#             "temp_min": (
#                 temp_min_values[i]
#                 if i < len(temp_min_values)
#                 else None
#             ),

#             "precipitation": (
#                 precipitation_values[i]
#                 if i < len(precipitation_values)
#                 else 0
#             ),

#             "wind_max": (
#                 wind_values[i]
#                 if i < len(wind_values)
#                 else 0
#             ),

#             "description": day_desc,
#             "icon": day_icon,
#         })

#     # Generate farming recommendations
#     farming_advice = generate_farming_advice(
#         weather_data
#     )

#     # -----------------------------------------
#     # Final API response
#     # -----------------------------------------

#     return {
#         "city": resolved_city,
#         "latitude": lat,
#         "longitude": lon,

#         "current": {
#             "temperature": current.get(
#                 "temperature_2m"
#             ),

#             "feels_like": current.get(
#                 "apparent_temperature"
#             ),

#             "humidity": current.get(
#                 "relative_humidity_2m"
#             ),

#             "rain": current.get(
#                 "rain",
#                 0,
#             ),

#             "precipitation": current.get(
#                 "precipitation",
#                 0,
#             ),

#             "wind_speed": current.get(
#                 "wind_speed_10m"
#             ),

#             "wind_direction": current.get(
#                 "wind_direction_10m"
#             ),

#             "cloud_cover": current.get(
#                 "cloud_cover"
#             ),

#             "pressure": current.get(
#                 "surface_pressure"
#             ),

#             "description": description,

#             "icon": icon,

#             "weather_code": code,
#         },

#         "forecast": forecast,

#         "farming_advice": farming_advice,

#     }, None

import requests
import logging

logger = logging.getLogger(__name__)

# Open-Meteo APIs
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

# OpenStreetMap Nominatim for reverse geocoding
REVERSE_GEOCODING_URL = "https://nominatim.openstreetmap.org/reverse"


def get_coordinates(city_name):
    """
    Converts a city name to latitude and longitude.
    Adds India as a country bias for better Indian city results.
    If no result is found, retries without the India bias.
    """
    try:
        search_name = city_name

        if "india" not in city_name.lower():
            search_name = f"{city_name}, India"

        # First attempt with India bias
        response = requests.get(
            GEOCODING_URL,
            params={
                "name": search_name,
                "count": 1,
                "language": "en",
                "format": "json",
                "countryCode": "IN",
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        results = data.get("results")

        # Retry without India restriction
        if not results:
            response = requests.get(
                GEOCODING_URL,
                params={
                    "name": city_name,
                    "count": 1,
                    "language": "en",
                    "format": "json",
                },
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()
            results = data.get("results")

        if not results:
            return (
                None,
                None,
                f"City '{city_name}' not found. "
                "Try adding the district or state name.",
            )

        result = results[0]

        return (
            result["latitude"],
            result["longitude"],
            result.get("name", city_name),
        )

    except requests.exceptions.Timeout:
        return None, None, "Geocoding request timed out."

    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding API error: {e}")
        return None, None, f"Could not connect to geocoding service: {e}"

    except Exception as e:
        logger.error(f"Geocoding error: {e}")
        return None, None, str(e)


def get_location_name(latitude, longitude):
    """
    Reverse geocoding:
    Converts latitude and longitude into a human-readable location name.

    Tries to return:
    village -> town -> city -> municipality -> county/district

    Falls back to 'Current Location' if reverse geocoding fails.
    """
    try:
        response = requests.get(
            REVERSE_GEOCODING_URL,
            params={
                "lat": latitude,
                "lon": longitude,
                "format": "jsonv2",
                "addressdetails": 1,
                "accept-language": "en",
            },
            headers={
                "User-Agent": "CropGuardAI/1.0"
            },
            timeout=10,
        )

        response.raise_for_status()
        data = response.json()

        address = data.get("address", {})

        # Prefer the most local available place name
        location_name = (
            address.get("village")
            or address.get("hamlet")
            or address.get("town")
            or address.get("city")
            or address.get("municipality")
            or address.get("suburb")
            or address.get("county")
            or address.get("state_district")
        )

        if location_name:
            return location_name

        # Fallback to display name
        display_name = data.get("display_name")

        if display_name:
            return display_name.split(",")[0].strip()

        return "Current Location"

    except requests.exceptions.Timeout:
        logger.warning("Reverse geocoding request timed out.")
        return "Current Location"

    except requests.exceptions.RequestException as e:
        logger.error(f"Reverse geocoding API error: {e}")
        return "Current Location"

    except Exception as e:
        logger.error(f"Reverse geocoding error: {e}")
        return "Current Location"


def get_weather(latitude, longitude):
    """
    Fetches current weather and 7-day forecast from Open-Meteo.
    No API key required.
    """
    try:
        params = {
            "latitude": latitude,
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

            "timezone": "Asia/Kolkata",
            "forecast_days": 7,
        }

        response = requests.get(
            WEATHER_URL,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        return response.json(), None

    except requests.exceptions.Timeout:
        return None, "Weather request timed out."

    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request error: {e}")
        return None, f"Could not connect to weather service: {e}"

    except Exception as e:
        logger.error(f"Weather API error: {e}")
        return None, str(e)


def get_weather_description(code):
    """
    Converts WMO weather codes into readable descriptions and icons.
    """
    WMO_CODES = {
        0: ("Clear sky", "☀️"),
        1: ("Mainly clear", "🌤️"),
        2: ("Partly cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"),
        48: ("Icy fog", "🌫️"),
        51: ("Light drizzle", "🌦️"),
        53: ("Moderate drizzle", "🌦️"),
        55: ("Dense drizzle", "🌧️"),
        61: ("Slight rain", "🌧️"),
        63: ("Moderate rain", "🌧️"),
        65: ("Heavy rain", "🌧️"),
        71: ("Slight snow", "🌨️"),
        73: ("Moderate snow", "🌨️"),
        75: ("Heavy snow", "❄️"),
        80: ("Slight showers", "🌦️"),
        81: ("Moderate showers", "🌧️"),
        82: ("Violent showers", "⛈️"),
        95: ("Thunderstorm", "⛈️"),
        96: ("Thunderstorm + hail", "⛈️"),
        99: ("Thunderstorm + hail", "⛈️"),
    }

    return WMO_CODES.get(
        code,
        ("Unknown", "🌡️"),
    )


def generate_farming_advice(weather_data):
    """
    Generates farming-specific advice based on current weather.
    """
    current = weather_data.get("current", {})

    temp = current.get("temperature_2m", 25)
    humidity = current.get("relative_humidity_2m", 60)
    rain = current.get("rain", 0)
    wind = current.get("wind_speed_10m", 0)
    code = current.get("weather_code", 0)

    advice = []

    # Temperature
    if temp > 38:
        advice.append({
            "icon": "🌡️",
            "type": "warning",
            "text": (
                "Extreme heat — irrigate crops in early morning or evening "
                "to reduce stress. Avoid spraying pesticides."
            ),
        })

    elif temp > 32:
        advice.append({
            "icon": "☀️",
            "type": "caution",
            "text": (
                "High temperature — increase irrigation frequency. "
                "Mulching is recommended to retain soil moisture."
            ),
        })

    elif temp < 10:
        advice.append({
            "icon": "🌡️",
            "type": "warning",
            "text": (
                "Cold conditions — protect sensitive crops from frost. "
                "Delay transplanting of seedlings."
            ),
        })

    else:
        advice.append({
            "icon": "✅",
            "type": "good",
            "text": "Temperature is suitable for most field operations.",
        })

    # Rain
    if rain > 20 or code in (65, 82, 95, 96, 99):
        advice.append({
            "icon": "🌧️",
            "type": "warning",
            "text": (
                "Heavy rain — avoid fertilizer or pesticide application. "
                "Check field drainage to prevent waterlogging."
            ),
        })

    elif rain > 5 or code in (61, 63, 80, 81):
        advice.append({
            "icon": "🌦️",
            "type": "caution",
            "text": (
                "Moderate rain expected — skip irrigation today. "
                "Monitor for fungal disease development."
            ),
        })

    elif code in (0, 1):
        advice.append({
            "icon": "☀️",
            "type": "good",
            "text": (
                "Clear conditions — good day for spraying, "
                "harvesting, or field work."
            ),
        })

    # Humidity
    if humidity > 85:
        advice.append({
            "icon": "💧",
            "type": "caution",
            "text": (
                "High humidity — risk of fungal diseases like blight "
                "and mildew. Monitor crops closely."
            ),
        })

    elif humidity < 30:
        advice.append({
            "icon": "🏜️",
            "type": "caution",
            "text": (
                "Low humidity — crops may experience moisture stress. "
                "Increase irrigation."
            ),
        })

    # Wind
    if wind > 40:
        advice.append({
            "icon": "💨",
            "type": "warning",
            "text": (
                "Strong winds — do not spray pesticides or fertilizers. "
                "Risk of lodging for tall crops."
            ),
        })

    elif wind > 20:
        advice.append({
            "icon": "🌬️",
            "type": "caution",
            "text": (
                "Moderate wind — avoid aerial spraying. "
                "Check support structures for tall crops."
            ),
        })

    return advice


def build_weather_response(
    weather_data,
    city,
    latitude,
    longitude,
):
    """
    Builds the common weather API response structure.
    Used for both searched cities and current GPS location.
    """
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    code = current.get("weather_code", 0)

    description, icon = get_weather_description(code)

    forecast = []

    days = daily.get("time", [])
    weather_codes = daily.get("weather_code", [])
    temp_max_values = daily.get("temperature_2m_max", [])
    temp_min_values = daily.get("temperature_2m_min", [])
    precipitation_values = daily.get("precipitation_sum", [])
    wind_values = daily.get("wind_speed_10m_max", [])

    for i, day in enumerate(days):

        day_code = (
            weather_codes[i]
            if i < len(weather_codes)
            else 0
        )

        day_desc, day_icon = get_weather_description(day_code)

        forecast.append({
            "date": day,

            "temp_max": (
                temp_max_values[i]
                if i < len(temp_max_values)
                else None
            ),

            "temp_min": (
                temp_min_values[i]
                if i < len(temp_min_values)
                else None
            ),

            "precipitation": (
                precipitation_values[i]
                if i < len(precipitation_values)
                else 0
            ),

            "wind_max": (
                wind_values[i]
                if i < len(wind_values)
                else 0
            ),

            "description": day_desc,
            "icon": day_icon,
        })

    return {
        "city": city,
        "latitude": latitude,
        "longitude": longitude,

        "current": {
            "temperature": current.get("temperature_2m"),
            "feels_like": current.get("apparent_temperature"),
            "humidity": current.get("relative_humidity_2m"),
            "rain": current.get("rain", 0),
            "precipitation": current.get("precipitation", 0),
            "wind_speed": current.get("wind_speed_10m"),
            "wind_direction": current.get("wind_direction_10m"),
            "cloud_cover": current.get("cloud_cover"),
            "pressure": current.get("surface_pressure"),
            "description": description,
            "icon": icon,
            "weather_code": code,
        },

        "forecast": forecast,

        "farming_advice": generate_farming_advice(
            weather_data
        ),
    }


def fetch_weather_for_city(city_name):
    """
    Gets weather for a searched city.
    """
    lat, lon, resolved_city = get_coordinates(city_name)

    if lat is None:
        return None, resolved_city

    weather_data, error = get_weather(lat, lon)

    if weather_data is None:
        return None, error

    data = build_weather_response(
        weather_data=weather_data,
        city=resolved_city,
        latitude=lat,
        longitude=lon,
    )

    return data, None


def fetch_weather_for_coordinates(latitude, longitude):
    """
    Gets weather for the user's current GPS coordinates
    and automatically determines the location name.
    """
    weather_data, error = get_weather(
        latitude,
        longitude,
    )

    if weather_data is None:
        return None, error

    location_name = get_location_name(
        latitude,
        longitude,
    )

    data = build_weather_response(
        weather_data=weather_data,
        city=location_name,
        latitude=latitude,
        longitude=longitude,
    )

    return data, None