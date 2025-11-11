"""
Weather Data Analytics Backend
FastAPI server with HDFS storage support using Open-Meteo APIs
"""
from datetime import datetime, timedelta, date
from statistics import mean
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests

from storage import get_storage_adapter

app = FastAPI(title="Weather Analytics API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/era5"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"

# Initialize storage adapter (HDFS or local fallback)
storage = get_storage_adapter()

WEATHER_CODE_MAP = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "depositing rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    56: "freezing drizzle",
    57: "dense freezing drizzle",
    61: "slight rain",
    63: "moderate rain",
    65: "heavy rain",
    66: "light freezing rain",
    67: "heavy freezing rain",
    71: "slight snowfall",
    73: "moderate snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "slight rain showers",
    81: "moderate rain showers",
    82: "violent rain showers",
    85: "slight snow showers",
    86: "heavy snow showers",
    95: "thunderstorm",
    96: "thunderstorm with slight hail",
    99: "thunderstorm with heavy hail",
}


# Data Models
class WeatherRecord(BaseModel):
    city: str
    timestamp: str  # ISO format
    tempC: float
    humidity: float
    windKph: float
    conditions: str


class IngestRequest(BaseModel):
    records: List[WeatherRecord]


def geocode_city(city: str) -> Tuple[float, float, str]:
    """Lookup latitude/longitude for a city using Open-Meteo geocoding API"""
    try:
        response = requests.get(
            GEOCODE_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Geocoding service error: {exc}")

    payload = response.json()
    results = payload.get("results", [])
    if not results:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    location = results[0]
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    resolved_name = location.get("name", city)

    if latitude is None or longitude is None:
        raise HTTPException(status_code=404, detail=f"City '{city}' not found")

    return float(latitude), float(longitude), resolved_name


def describe_weather_code(code: Optional[int]) -> str:
    if code is None:
        return "unknown conditions"
    return WEATHER_CODE_MAP.get(code, f"weather code {code}")


def build_record(
    city: str,
    timestamp: str,
    temperature: Optional[float],
    humidity: Optional[float],
    wind: Optional[float],
    conditions: str,
) -> Dict[str, Any]:
    """Create a record dictionary in the storage format"""
    return {
        "city": city.lower(),
        "timestamp": timestamp,
        "tempC": round(temperature, 2) if temperature is not None else None,
        "humidity": round(humidity, 2) if humidity is not None else None,
        "windKph": round(wind, 2) if wind is not None else None,
        "conditions": conditions,
    }


def fetch_current_weather(city: str) -> Dict[str, Any]:
    latitude, longitude, resolved_name = geocode_city(city)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,wind_speed_10m,relative_humidity_2m,weather_code",
    }

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Forecast service error: {exc}")

    current = response.json().get("current", {})
    return build_record(
        resolved_name,
        current.get("time", datetime.utcnow().isoformat()),
        current.get("temperature_2m"),
        current.get("relative_humidity_2m"),
        current.get("wind_speed_10m"),
        describe_weather_code(current.get("weather_code")),
    )


def fetch_past_weather(city: str, days: int) -> List[Dict[str, Any]]:
    latitude, longitude, resolved_name = geocode_city(city)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "past_days": max(1, min(days, 92)),
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
    }

    try:
        response = requests.get(FORECAST_URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Past weather service error: {exc}")

    payload = response.json()
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    wind = hourly.get("wind_speed_10m", [])
    codes = hourly.get("weather_code", [])

    records: List[Dict[str, Any]] = []
    for idx, timestamp in enumerate(times):
        temp = temps[idx] if idx < len(temps) else None
        hum = humidity[idx] if idx < len(humidity) else None
        wind_speed = wind[idx] if idx < len(wind) else None
        code = codes[idx] if idx < len(codes) else None
        records.append(
            build_record(
                resolved_name,
                timestamp,
                temp,
                hum,
                wind_speed,
                describe_weather_code(code),
            )
        )
    return records


def fetch_historical_weather(city: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    latitude, longitude, resolved_name = geocode_city(city)
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
    }

    try:
        response = requests.get(HISTORICAL_URL, params=params, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(
            status_code=503, detail=f"Historical weather service error: {exc}"
        )

    payload = response.json()
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    humidity = hourly.get("relative_humidity_2m", [])
    wind = hourly.get("wind_speed_10m", [])

    records: List[Dict[str, Any]] = []
    for idx, timestamp in enumerate(times):
        temp = temps[idx] if idx < len(temps) else None
        hum = humidity[idx] if idx < len(humidity) else None
        wind_speed = wind[idx] if idx < len(wind) else None
        records.append(
            build_record(
                resolved_name,
                timestamp,
                temp,
                hum,
                wind_speed,
                "historical (ERA5)",
            )
        )
    return records


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "storage": storage.get_storage_type(),
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/ingest")
async def ingest_weather(data: IngestRequest):
    """
    Ingest weather records into storage (HDFS or local)
    Accepts array of WeatherRecord objects
    """
    if not data.records:
        raise HTTPException(status_code=400, detail="No records provided")

    try:
        stored_count = 0
        for record in data.records:
            storage.write_record(record.dict())
            stored_count += 1

        return {
            "message": f"Successfully ingested {stored_count} records",
            "count": stored_count,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/weather")
async def get_weather(
    city: str = Query(..., description="City name"),
    mode: str = Query(
        "current",
        description="Retrieval mode: current, past, historical",
        regex="^(current|past|historical)$",
    ),
    days: int = Query(10, description="Past days (mode=past, max 92)"),
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD (historical)"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD (historical)"),
):
    """
    Retrieve weather data from Open-Meteo APIs and store results.
    """
    try:
        if mode == "current":
            record = fetch_current_weather(city)
            storage.write_record(record)
            return {"city": record["city"], "record": record, "mode": "current"}

        if mode == "past":
            records = fetch_past_weather(city, days)
            for record in records:
                storage.write_record(record)
            return {"city": city.lower(), "stored": len(records), "mode": "past"}

        if mode == "historical":
            if not start or not end:
                raise HTTPException(
                    status_code=400,
                    detail="Start and end dates are required for historical mode",
                )
            records = fetch_historical_weather(city, start, end)
            for record in records:
                storage.write_record(record)
            return {
                "city": city.lower(),
                "stored": len(records),
                "mode": "historical",
                "start": start,
                "end": end,
            }

        raise HTTPException(status_code=400, detail="Unsupported mode")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/stats")
async def get_stats(
    city: Optional[str] = Query(None, description="Filter by city"),
    days: int = Query(7, description="Number of days to analyze"),
):
    """
    Get statistics (averages, min, max) for stored records.
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        records = storage.read_records(city=city, since=start_date)

        if not records:
            return {
                "city": city or "all",
                "period_days": days,
                "record_count": 0,
                "avg_tempC": None,
                "avg_humidity": None,
                "avg_windKph": None,
                "min_tempC": None,
                "max_tempC": None,
            }

        temps = [r.get("tempC") for r in records if isinstance(r.get("tempC"), (int, float))]
        hums = [r.get("humidity") for r in records if isinstance(r.get("humidity"), (int, float))]
        winds = [r.get("windKph") for r in records if isinstance(r.get("windKph"), (int, float))]

        def avg(values: List[float]) -> Optional[float]:
            return sum(values) / len(values) if values else None

        return {
            "city": city or "all",
            "period_days": days,
            "record_count": len(records),
            "avg_tempC": round(avg(temps), 2) if temps else None,
            "avg_humidity": round(avg(hums), 2) if hums else None,
            "avg_windKph": round(avg(winds), 2) if winds else None,
            "min_tempC": round(min(temps), 2) if temps else None,
            "max_tempC": round(max(temps), 2) if temps else None,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/history")
async def get_history(
    city: Optional[str] = Query(None, description="Filter by city"),
    days: int = Query(7, description="Number of days of history"),
):
    """
    Get stored weather records.
    """
    try:
        start_date = datetime.now() - timedelta(days=days)
        records = storage.read_records(city=city, since=start_date)
        records.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return {
            "city": city or "all",
            "days": days,
            "count": len(records),
            "records": records,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


def _parse_iso_date(ts: str) -> Optional[date]:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
    except Exception:
        return None


def _linear_forecast(values: List[float], periods: int) -> List[float]:
    """Simple linear regression extrapolation."""
    if not values:
        return [None] * periods

    if len(values) == 1:
        return [round(values[0], 2)] * periods

    xs = list(range(len(values)))
    mean_x = sum(xs) / len(xs)
    mean_y = sum(values) / len(values)
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        slope = 0.0
    else:
        slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values)) / denom
    intercept = mean_y - slope * mean_x

    forecasts: List[float] = []
    for idx in range(len(values), len(values) + periods):
        value = intercept + slope * idx
        forecasts.append(round(value, 2))
    return forecasts


def generate_forecast(city: str, days: int, lookback: int) -> Dict[str, Any]:
    since = datetime.now() - timedelta(days=max(lookback, days) + 5)
    records = storage.read_records(city=city, since=since)
    if not records:
        raise HTTPException(status_code=404, detail="No stored data available for forecast")

    daily_map: Dict[date, Dict[str, List[float]]] = {}
    for rec in records:
        ts = rec.get("timestamp")
        record_date = _parse_iso_date(ts) if isinstance(ts, str) else None
        if not record_date:
            continue
        daily = daily_map.setdefault(record_date, {"temp": [], "humid": [], "wind": []})
        if isinstance(rec.get("tempC"), (int, float)):
            daily["temp"].append(float(rec["tempC"]))
        if isinstance(rec.get("humidity"), (int, float)):
            daily["humid"].append(float(rec["humidity"]))
        if isinstance(rec.get("windKph"), (int, float)):
            daily["wind"].append(float(rec["windKph"]))

    if not daily_map:
        raise HTTPException(status_code=404, detail="Insufficient numeric data for forecast")

    daily_dates = sorted(daily_map.keys())
    daily_dates = daily_dates[-lookback:]

    temp_series: List[float] = []
    humid_series: List[float] = []
    wind_series: List[float] = []
    for d in daily_dates:
        entry = daily_map[d]
        if entry["temp"]:
            temp_series.append(round(mean(entry["temp"]), 2))
        if entry["humid"]:
            humid_series.append(round(mean(entry["humid"]), 2))
        if entry["wind"]:
            wind_series.append(round(mean(entry["wind"]), 2))

    if len(temp_series) < 2 and len(humid_series) < 2 and len(wind_series) < 2:
        raise HTTPException(status_code=400, detail="Need at least two days of data for forecasting")

    # Forecast always starts from tomorrow (today + 1)
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    future_dates = [tomorrow + timedelta(days=i) for i in range(days)]

    temp_forecast = _linear_forecast(temp_series, days) if temp_series else [None] * days
    humid_forecast = _linear_forecast(humid_series, days) if humid_series else [None] * days
    wind_forecast = _linear_forecast(wind_series, days) if wind_series else [None] * days

    forecast = []
    for idx, day_date in enumerate(future_dates):
        forecast.append(
            {
                "date": day_date.isoformat(),
                "tempC": temp_forecast[idx],
                "humidity": humid_forecast[idx],
                "windKph": wind_forecast[idx],
            }
        )

    return {
        "city": city.lower(),
        "generated_at": datetime.now().isoformat(),
        "lookback_days": len(daily_dates),
        "forecast_days": days,
        "data": forecast,
    }


@app.get("/forecast")
async def get_forecast(
    city: str = Query(..., description="City to forecast"),
    days: int = Query(7, description="Days ahead to forecast (2-7)"),
    lookback: int = Query(14, description="Lookback days to learn from"),
):
    """
    Predict upcoming days using simple linear regression on stored records.
    """
    if days < 2 or days > 7:
        raise HTTPException(status_code=400, detail="Days must be between 2 and 7")
    if lookback < 3:
        raise HTTPException(status_code=400, detail="Lookback should be at least 3 days")
    try:
        return generate_forecast(city, days, lookback)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
