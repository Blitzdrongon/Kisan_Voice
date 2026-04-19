"""
Weather service for RaithaMithra
"""

import os
import json
from typing import Optional, Dict, Any
from datetime import datetime

import httpx
from loguru import logger

from core.config import get_settings


class WeatherService:
    """Service for OpenWeather API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.openweather_api_key
        self.base_url = self.settings.openweather_base_url
        
    async def get_current_weather(
        self, 
        city: str, 
        country_code: str = "IN",
        language: str = "kn"
    ) -> Optional[Dict[str, Any]]:
        """Get current weather for a city"""
        
        try:
            # Language mapping for OpenWeather
            lang_map = {"kn": "hi", "en": "en"}  # Kannada -> Hindi (closest available)
            lang = lang_map.get(language, "en")
            
            params = {
                "q": f"{city},{country_code}",
                "appid": self.api_key,
                "units": "metric",  # Celsius
                "lang": lang
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/weather",
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    weather_data = response.json()
                    return self._format_weather_data(weather_data, language)
                else:
                    logger.error(f"OpenWeather API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
            return None
    
    async def get_weather_forecast(
        self, 
        city: str, 
        country_code: str = "IN",
        days: int = 5,
        language: str = "kn"
    ) -> Optional[Dict[str, Any]]:
        """Get weather forecast for a city"""
        
        try:
            lang_map = {"kn": "hi", "en": "en"}
            lang = lang_map.get(language, "en")
            
            params = {
                "q": f"{city},{country_code}",
                "appid": self.api_key,
                "units": "metric",
                "lang": lang,
                "cnt": days
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/forecast",
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    forecast_data = response.json()
                    return self._format_forecast_data(forecast_data, language)
                else:
                    logger.error(f"OpenWeather forecast API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {e}")
            return None
    
    def _format_weather_data(self, data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Format weather data for response"""
        
        try:
            main = data.get("main", {})
            weather = data.get("weather", [{}])[0]
            wind = data.get("wind", {})
            
            # Language-specific descriptions
            if language == "kn":
                description = self._translate_weather_description(weather.get("description", ""))
                city_name = data.get("name", "Unknown City")
            else:
                description = weather.get("description", "")
                city_name = data.get("name", "Unknown City")
            
            formatted_data = {
                "city": city_name,
                "temperature": {
                    "current": round(main.get("temp", 0), 1),
                    "feels_like": round(main.get("feels_like", 0), 1),
                    "min": round(main.get("temp_min", 0), 1),
                    "max": round(main.get("temp_max", 0), 1)
                },
                "humidity": main.get("humidity", 0),
                "pressure": main.get("pressure", 0),
                "description": description,
                "wind_speed": wind.get("speed", 0),
                "timestamp": data.get("dt", 0)
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"Error formatting weather data: {e}")
            return {}
    
    def _format_forecast_data(self, data: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Format forecast data for response"""
        
        try:
            city = data.get("city", {})
            forecasts = []
            
            for item in data.get("list", []):
                main = item.get("main", {})
                weather = item.get("weather", [{}])[0]
                
                if language == "kn":
                    description = self._translate_weather_description(weather.get("description", ""))
                else:
                    description = weather.get("description", "")
                
                forecast = {
                    "datetime": item.get("dt", 0),
                    "temperature": {
                        "current": round(main.get("temp", 0), 1),
                        "min": round(main.get("temp_min", 0), 1),
                        "max": round(main.get("temp_max", 0), 1)
                    },
                    "description": description,
                    "humidity": main.get("humidity", 0)
                }
                forecasts.append(forecast)
            
            return {
                "city": city.get("name", "Unknown City"),
                "forecasts": forecasts
            }
            
        except Exception as e:
            logger.error(f"Error formatting forecast data: {e}")
            return {}
    
    def _translate_weather_description(self, description: str) -> str:
        """Translate weather description to Kannada"""
        
        translations = {
            "clear sky": "ಸ್ಪಷ್ಟ ಆಕಾಶ",
            "few clouds": "ಕೆಲವು ಮೋಡಗಳು",
            "scattered clouds": "ಚದುರಿದ ಮೋಡಗಳು",
            "broken clouds": "ಮುರಿದ ಮೋಡಗಳು",
            "overcast clouds": "ಮೋಡಗಳಿಂದ ಆವೃತ",
            "light rain": "ಸ್ವಲ್ಪ ಮಳೆ",
            "moderate rain": "ಮಧ್ಯಮ ಮಳೆ",
            "heavy rain": "ಭಾರಿ ಮಳೆ",
            "thunderstorm": "ಗುಡುಗು ಮಳೆ",
            "snow": "ಹಿಮ",
            "mist": "ಮಂಜು",
            "fog": "ಮಂಜು",
            "haze": "ಮಂಜು"
        }
        
        return translations.get(description.lower(), description)


# Global service instance
weather_service = WeatherService()


def get_weather_service() -> WeatherService:
    """Get weather service instance"""
    return weather_service

