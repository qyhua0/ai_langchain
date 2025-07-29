import requests

def get_coordinates_by_city(city_name: str):
    """
    使用 Open-Meteo 的地理编码接口根据城市名获取经纬度
    """
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": city_name,
        "count": 1,
        "language": "en",
        "format": "json"
    }
    resp = requests.get(url, params=params)
    data = resp.json()

    if "results" not in data or len(data["results"]) == 0:
        raise ValueError(f"找不到城市：{city_name}")

    location = data["results"][0]
    return location["latitude"], location["longitude"]
