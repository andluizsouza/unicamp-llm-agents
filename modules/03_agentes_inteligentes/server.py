import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GeoWeatherServer")

@mcp.tool()
def geocodificar(local: str) -> dict:
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": local, "format": "json", "limit": 1}
    headers = {"User-Agent": "FastMCP-LangChain-Agent/1.0"}

    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()

    if data:
        return {"latitude": float(data[0]["lat"]), "longitude": float(data[0]["lon"])}
    return {"error": "Local não encontrado."}

@mcp.tool()
def prever_clima(latitude: float, longitude: float, data_inicio: str, data_fim: str) -> dict:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude, "longitude": longitude,
        "start_date": data_inicio, "end_date": data_fim,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_sum"],
        "timezone": "auto"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json().get("daily", {})

if __name__ == "__main__":
    mcp.run(transport='stdio')
