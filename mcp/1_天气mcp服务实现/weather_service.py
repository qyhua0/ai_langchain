import requests

def get_weather(latitude: float, longitude: float):
    """
    查询实时天气数据
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,weather_code,wind_speed_10m",
        "timezone": "auto"
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if "current" not in data:
        raise ValueError("未能获取到天气数据")

    current = data["current"]
    return {
        "temperature": current.get("temperature_2m"),
        "weather_code": current.get("weather_code"),
        "wind_speed": current.get("wind_speed_10m"),
        "time": current.get("time")
    }
