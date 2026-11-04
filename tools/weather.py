try:
    import truststore
    truststore.inject_into_ssl()  # use the Windows certificate store
except ImportError:
    pass
import requests

GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather(city: str) -> dict:
    """Get today's weather for a city (temperatures in Celsius). Never raises."""
    try:
        if not isinstance(city, str) or not city.strip():
            return {"error": "City name is required"}

        geo = requests.get(GEO_URL, params={"name": city.strip(), "count": 1}, timeout=10)
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return {"error": f"Could not find a city named '{city}'"}
        place = results[0]

        forecast = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": "temperature_2m",
                "daily": "temperature_2m_max,temperature_2m_min",
                "timezone": "auto",
                "forecast_days": 1,
            },
            timeout=10,
        )
        forecast.raise_for_status()
        data = forecast.json()

        return {
            "city": place["name"],
            "country": place.get("country"),
            "current_temp_c": data["current"]["temperature_2m"],
            "high_c": data["daily"]["temperature_2m_max"][0],
            "low_c": data["daily"]["temperature_2m_min"][0],
        }
    except requests.Timeout:
        return {"error": "Weather service timed out. Try again."}
    except requests.RequestException as e:
        return {"error": f"Weather service unavailable: {e}"}
    except (KeyError, IndexError, ValueError):
        return {"error": "Unexpected response from weather service"}