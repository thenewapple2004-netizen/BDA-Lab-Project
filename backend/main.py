"""
Weather Data Analytics Backend (offline-first)
Serves data from local storage/HDFS without calling external weather APIs.
"""
from datetime import datetime, timedelta, date
from statistics import mean
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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

# Initialize storage adapter (HDFS or local fallback)
storage = get_storage_adapter()


# Data Models
class WeatherRecord(BaseModel):
    city: str
    timestamp: str  # ISO format
    tempC: Optional[float] = None
    humidity: Optional[float] = None
    windKph: Optional[float] = None
    conditions: Optional[str] = None


class IngestRequest(BaseModel):
    records: List[WeatherRecord]


def _parse_timestamp(ts: str) -> Optional[datetime]:
    """Parse ISO timestamps while tolerating missing timezone suffixes."""
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return None


def _filter_by_range(
    records: List[Dict[str, Any]],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Filter records by optional inclusive start/end dates (YYYY-MM-DD)."""
    if not start_date and not end_date:
    return records

    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) + timedelta(days=1) if end_date else None

    filtered: List[Dict[str, Any]] = []
    for rec in records:
        ts = rec.get("timestamp")
        parsed = _parse_timestamp(ts) if isinstance(ts, str) else None
        if not parsed:
            continue
        if start_dt and parsed < start_dt:
            continue
        if end_dt and parsed >= end_dt:
            continue
        filtered.append(rec)
    return filtered


def _read_records(
    city: Optional[str],
    days: Optional[int] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Centralized record retrieval with optional city/days/date-range filtering."""
    since = datetime.now() - timedelta(days=days) if days else None
    records = storage.read_records(city=city, since=since)
    records = _filter_by_range(records, start_date=start, end_date=end)
    return records


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "storage": storage.get_storage_type(),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/cities")
async def list_cities():
    """Return unique city names from stored records."""
    records = storage.read_records(city=None, since=None)
    cities = sorted({str(rec.get("city", "")).lower() for rec in records if rec.get("city")})
    return {"count": len(cities), "cities": cities}


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
    days: int = Query(365, description="Past days (mode=past)"),
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD (historical)"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD (historical)"),
):
    """
    Retrieve weather data from locally stored records (no external API calls).
    - current: returns the most recent stored record for the city
    - past: returns records within the last N days
    - historical: returns records within an explicit date range
    """
    try:
        if mode == "current":
            records = _read_records(city=city, days=None)
            if not records:
                raise HTTPException(status_code=404, detail="No stored records for this city")
            latest = sorted(records, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
            return {"city": city.lower(), "record": latest, "mode": "current"}

        if mode == "past":
            records = _read_records(city=city, days=max(1, days))
            if not records:
                raise HTTPException(status_code=404, detail="No stored records for requested window")
            return {"city": city.lower(), "stored": len(records), "mode": "past", "records": records}

        if mode == "historical":
            if not start or not end:
                raise HTTPException(
                    status_code=400,
                    detail="Start and end dates are required for historical mode",
                )
            records = _read_records(city=city, start=start, end=end)
            if not records:
                raise HTTPException(status_code=404, detail="No stored records in this date range")
            return {
                "city": city.lower(),
                "stored": len(records),
                "mode": "historical",
                "start": start,
                "end": end,
                "records": records,
            }

        raise HTTPException(status_code=400, detail="Unsupported mode")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/stats")
async def get_stats(
    city: Optional[str] = Query(None, description="Filter by city"),
    days: Optional[int] = Query(365, description="Number of days to analyze; omit for all"),
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    """
    Get statistics (averages, min, max) for stored records.
    """
    try:
        records = _read_records(city=city, days=days, start=start, end=end)

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
    days: Optional[int] = Query(365, description="Number of days of history; omit for all"),
    start: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
):
    """
    Get stored weather records.
    """
    try:
        records = _read_records(city=city, days=days, start=start, end=end)
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
    parsed = _parse_timestamp(ts)
    return parsed.date() if parsed else None


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
    slope = 0.0 if denom == 0 else sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, values)) / denom
    intercept = mean_y - slope * mean_x

    forecasts: List[float] = []
    for idx in range(len(values), len(values) + periods):
        value = intercept + slope * idx
        forecasts.append(round(value, 2))
    return forecasts


def generate_forecast(city: str, days: int, lookback: int) -> Dict[str, Any]:
    records = storage.read_records(city=city, since=None)
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
    days: int = Query(5, description="Days ahead to forecast (2-7)", ge=2, le=7),
    lookback: int = Query(30, description="Lookback days to learn from", ge=3),
):
    """
    Predict upcoming days using simple linear regression on stored records.
    """
    try:
        return generate_forecast(city, days, lookback)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
