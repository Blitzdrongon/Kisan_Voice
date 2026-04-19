# 📄 `app/services/weather_service.py` — OpenWeather API Service

> **Back to:** [APP_DOCUMENTATION.md](../../APP_DOCUMENTATION.md)

---

## Overview

`weather_service.py` provides current weather data and 5-day forecasts using the **OpenWeatherMap API**. It includes Kannada translation for common weather descriptions.

---

## Class: `WeatherService`

### Initialization

```python
self.api_key  = settings.openweather_api_key
self.base_url = settings.openweather_base_url  # https://api.openweathermap.org/data/2.5
```

---

## Methods

### `get_current_weather(city, country_code, language) → dict | None`

Fetches real-time weather for a city.

**Default call in pipeline:** `city="hubli"`, `country_code="IN"`

**Parameters:**
- `units`: `"metric"` (Celsius)
- `lang`: Maps `"kn"` → `"hi"` (OpenWeather has no Kannada support; Hindi is closest)

**Returns a formatted dict:**
```python
{
    "city": "Hubli",
    "temperature": {
        "current": 32.1,
        "feels_like": 34.0,
        "min": 28.5,
        "max": 35.2
    },
    "humidity": 65,
    "pressure": 1008,
    "description": "ಸ್ಪಷ್ಟ ಆಕಾಶ",  # Translated to Kannada
    "wind_speed": 4.2,
    "timestamp": 1713270000
}
```

---

### `get_weather_forecast(city, country_code, days, language) → dict | None`

Fetches a multi-day weather forecast (up to 5 days by default).

**Returns:**
```python
{
    "city": "Hubli",
    "forecasts": [
        {
            "datetime": 1713270000,
            "temperature": {"current": 32.1, "min": 28.5, "max": 35.2},
            "description": "ಮಧ್ಯಮ ಮಳೆ",
            "humidity": 70
        },
        ...
    ]
}
```

---

## Kannada Translations

The `_translate_weather_description()` method maps OpenWeather descriptions to Kannada:

| English | ಕನ್ನಡ |
|---|---|
| clear sky | ಸ್ಪಷ್ಟ ಆಕಾಶ |
| few clouds | ಕೆಲವು ಮೋಡಗಳು |
| scattered clouds | ಚದುರಿದ ಮೋಡಗಳು |
| broken clouds | ಮುರಿದ ಮೋಡಗಳು |
| overcast clouds | ಮೋಡಗಳಿಂದ ಆವೃತ |
| light rain | ಸ್ವಲ್ಪ ಮಳೆ |
| moderate rain | ಮಧ್ಯಮ ಮಳೆ |
| heavy rain | ಭಾರಿ ಮಳೆ |
| thunderstorm | ಗುಡುಗು ಮಳೆ |
| snow | ಹಿಮ |
| mist / fog / haze | ಮಂಜು |

If a description is not in the translation map, it is returned as-is.

---

## How It Appears to the User

From `_handle_weather_query()` in `conversation_nodes.py`:

```
Kannada: "hubli ನಲ್ಲಿ ಇಂದಿನ ಹವಾಮಾನ: ಸ್ಪಷ್ಟ ಆಕಾಶ, ತಾಪಮಾನ: 32.1°C"
English: "Current weather in hubli: clear sky, Temperature: 32.1°C"
```

---

## Known Limitation

The city is **hardcoded to "Hubli"** in `conversation_nodes.py`:
```python
city = "hubli"
country_code = "IN"
```

To support dynamic city extraction, the user's message would need NER (Named Entity Recognition) processing.

---

## Global Instance

```python
weather_service = WeatherService()

def get_weather_service() -> WeatherService:
    return weather_service
```

---

## Related Files

| File | Role |
|---|---|
| [core/config.py](../core/config.md) | Provides `openweather_api_key` and base URL |
| [nodes/conversation_nodes.py](../nodes/conversation_nodes.md) | Calls this in `_handle_weather_query()` |
