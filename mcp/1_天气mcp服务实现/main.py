from mcp_context import MCPContext
from geo_utils import get_coordinates_by_city
from weather_service import get_weather
import json

def handle_weather_query(context: MCPContext):
    """
    MCP 风格统一处理天气查询
    """
    if context.model != "weather" or context.operation != "query":
        raise ValueError("不支持的模型或操作")

    city = context.params.get("city")
    if not city:
        raise ValueError("缺少 city 参数")

    # 获取经纬度
    latitude, longitude = get_coordinates_by_city(city)

    # 获取天气信息
    weather = get_weather(latitude, longitude)

    return {
        "city": city,
        "latitude": latitude,
        "longitude": longitude,
        "weather": weather
    }

if __name__ == "__main__":
    # 测试效果
    context = MCPContext(
        model="weather",
        operation="query",
        params={"city": "Shanghai"}
    )

    try:
        result = handle_weather_query(context)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print("查询失败:", str(e))
