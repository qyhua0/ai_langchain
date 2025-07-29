from fastapi import FastAPI, Request
from pydantic import BaseModel
from mcp_context import MCPContext
from geo_utils import get_coordinates_by_city
from weather_service import get_weather

app = FastAPI()

@app.post("/mcp")
async def mcp_handler(request: Request):
    try:
        body = await request.json()
        context = MCPContext(**body)

        if context.model != "weather" or context.operation != "query":
            return {"code": 400, "message": "不支持的模型或操作", "data": None}

        city = context.params.get("city")
        if not city:
            return {"code": 400, "message": "缺少 city 参数", "data": None}

        latitude, longitude = get_coordinates_by_city(city)
        weather = get_weather(latitude, longitude)

        return {
            "code": 200,
            "message": "success",
            "data": {
                "city": city,
                "latitude": latitude,
                "longitude": longitude,
                "weather": weather
            }
        }

    except Exception as e:
        return {"code": 500, "message": str(e), "data": None}
    # pip install fastapi uvicorn
    # 运行测试
    #uvicorn server:app --host 0.0.0.0 --port 8000

