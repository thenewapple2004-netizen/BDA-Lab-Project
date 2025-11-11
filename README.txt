Weather Data Analytics - Big Data Project
==========================================

Simple weather analytics app with HDFS storage support.

PROJECT STRUCTURE
-----------------
BDA-Lab-Project/
  backend/
    main.py          # FastAPI server
    storage.py       # Storage abstraction (HDFS + local)
  frontend/
    src/
      App.js         # React app
      index.css      # Styles
  requirements.txt   # Python dependencies
  data/              # Local storage fallback (auto-created)

SETUP
-----

1. Backend Setup:
   cd BDA-Lab-Project
   python -m venv .venv
   .venv\Scripts\activate    # Windows
   # source .venv/bin/activate  # Linux/Mac
   pip install -r requirements.txt

2. Frontend Setup:
   cd frontend
   npm install

3. Environment Variables (optional - for HDFS clusters):
   - HDFS_NAMENODE=http://localhost:9870
   - HDFS_USER=hadoop
   - HDFS_BASE_DIR=/apps/weather

RUN
---

1. Start Backend:
   cd BDA-Lab-Project
   .venv\Scripts\activate
   uvicorn main:app --app-dir backend --reload
   # Server runs on http://localhost:5000

2. Start Frontend:
   cd frontend
   npm start
   # Opens http://localhost:3000

API ENDPOINTS
-------------

GET  /health              - Health check, shows storage type
POST /ingest              - Ingest weather records (JSON array)
GET  /weather?city=X&mode=current      - Fetch current weather
GET  /weather?city=X&mode=past&days=10 - Fetch hourly past data (max 92 days)
GET  /weather?city=X&mode=historical&start=YYYY-MM-DD&end=YYYY-MM-DD - Fetch ERA5 archive
GET  /forecast?city=X&days=7&lookback=14 - Predict upcoming days (2-7 days, default 7)
GET  /stats?city=X&days=7 - Get statistics (averages, min/max)
GET  /history?city=X&days=30 - Get historical records

SAMPLE CURL REQUESTS
--------------------

# Health check
curl http://localhost:5000/health

# Fetch current weather (no API key required)
curl "http://localhost:5000/weather?city=Lahore&mode=current"

# Fetch past 10 days (hourly) and store
curl "http://localhost:5000/weather?city=Lahore&mode=past&days=10"

# Fetch historical range (ERA5 archive)
curl "http://localhost:5000/weather?city=Lahore&mode=historical&start=2022-01-01&end=2022-01-31"

# Generate forecast (2-7 days, default 7) using stored data
curl "http://localhost:5000/forecast?city=Lahore&days=7&lookback=14"

# Get statistics
curl "http://localhost:5000/stats?city=London&days=7"

# Get history
curl "http://localhost:5000/history?city=London&days=30"

# Ingest records
curl -X POST http://localhost:5000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {
        "city": "london",
        "timestamp": "2024-01-15T10:00:00",
        "tempC": 15.5,
        "humidity": 65,
        "windKph": 12.3,
        "conditions": "clear sky"
      }
    ]
  }'

STORAGE
-------

- If HDFS is available (configured via env vars), data is stored in:
  /apps/weather/ingest/date=YYYY-MM-DD/city.jsonl

- If HDFS is unavailable, automatically falls back to:
  data/apps/weather/ingest/date=YYYY-MM-DD/city.jsonl

DATA MODEL
----------

WeatherRecord:
  - city: string
  - timestamp: ISO 8601 string
  - tempC: float (temperature in Celsius)
  - humidity: float (percentage)
  - windKph: float (wind speed in km/h)
  - conditions: string (weather description)

NOTES
-----

- No MongoDB required - uses HDFS or local filesystem
- Automatic HDFS fallback if cluster unavailable
- Date-partitioned storage for efficient queries
- Simple, student-friendly codebase

