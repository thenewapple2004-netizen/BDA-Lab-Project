import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './index.css';

const API_BASE = 'http://localhost:5000';

function App() {
  const [tab, setTab] = useState('home');
  const [city, setCity] = useState('London');
  const [currentRecord, setCurrentRecord] = useState(null);
  const [stats, setStats] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [forecastDays, setForecastDays] = useState(7);
  const [history, setHistory] = useState([]);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [storageType, setStorageType] = useState('unknown');

  useEffect(() => {
    const loadHealth = async () => {
      try {
        const res = await axios.get(`${API_BASE}/health`);
        setStorageType(res.data.storage);
      } catch {
        setStorageType('unavailable');
      }
    };
    loadHealth();
  }, []);

  const setStatus = (msg, err = null) => {
    setMessage(msg);
    setError(err);
  };

  const fetchWeather = async (mode, extraParams = {}) => {
    if (!city.trim()) {
      setStatus(null, 'Please enter a city name.');
      return;
    }

    setLoading(true);
    setStatus(null, null);

    try {
      const res = await axios.get(`${API_BASE}/weather`, {
        params: { city, mode, ...extraParams },
      });

      if (mode === 'current') {
        setCurrentRecord(res.data.record);
        setStatus('Current weather stored successfully.');
      } else {
        setCurrentRecord(null);
        setStatus(
          `${res.data.stored} records stored for ${mode === 'past' ? 'past days' : 'historical range'}.`,
        );
      }
    } catch (err) {
      setStatus(null, err.response?.data?.detail || 'Failed to fetch weather data.');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    setLoading(true);
    setStatus(null, null);
    try {
      const res = await axios.get(`${API_BASE}/stats`, {
        params: { city: city || null, days: 7 },
      });
      setStats(res.data);
      setStatus('Statistics refreshed.');
    } catch (err) {
      setStatus(null, err.response?.data?.detail || 'Failed to load statistics.');
    } finally {
      setLoading(false);
    }
  };

  const loadForecast = async () => {
    setLoading(true);
    setStatus(null, null);
    try {
      const res = await axios.get(`${API_BASE}/forecast`, {
        params: { city: city || null, days: forecastDays },
      });
      setForecast(res.data);
      setStatus(`Forecast generated for ${forecastDays} days.`);
    } catch (err) {
      setStatus(null, err.response?.data?.detail || 'Failed to generate forecast.');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    setLoading(true);
    setStatus(null, null);
    try {
      const res = await axios.get(`${API_BASE}/history`, {
        params: { city: city || null, days: 30 },
      });
      setHistory(res.data.records || []);
      setStatus(`Loaded ${res.data.count} records from storage.`);
    } catch (err) {
      setStatus(null, err.response?.data?.detail || 'Failed to load history.');
    } finally {
      setLoading(false);
    }
  };

  const handleHistoricalFetch = () => {
    if (!startDate || !endDate) {
      setStatus(null, 'Please select both start and end dates.');
      return;
    }
    fetchWeather('historical', { start: startDate, end: endDate });
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Weather Data Analytics</h1>
        <p>Powered by Open-Meteo • Stored in HDFS/Local</p>
        <div className="storage-indicator">
          Storage backend: <strong>{storageType}</strong>
        </div>
      </header>

      <nav className="nav">
        {['home', 'dashboard', 'history'].map((key) => (
          <button
            key={key}
            className={tab === key ? 'nav-btn active' : 'nav-btn'}
            onClick={() => setTab(key)}
          >
            {key.charAt(0).toUpperCase() + key.slice(1)}
          </button>
        ))}
      </nav>

      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}

      {tab === 'home' && (
        <section className="card">
          <h2>Fetch & Store Weather</h2>
          <div className="form-group">
            <label>City Name</label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="e.g., Lahore, London"
              disabled={loading}
            />
          </div>

          <div className="actions">
            <button
              className="btn"
              onClick={() => fetchWeather('current')}
              disabled={loading}
            >
              Current Weather
            </button>
            <button
              className="btn"
              onClick={() => fetchWeather('past', { days: 10 })}
              disabled={loading}
            >
              Past 10 Days (Hourly)
            </button>
          </div>

          <div className="form-inline">
            <div>
              <label>Start Date</label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <label>End Date</label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                disabled={loading}
              />
            </div>
            <button className="btn" onClick={handleHistoricalFetch} disabled={loading}>
              Historical Range
            </button>
          </div>

          {currentRecord && (
            <div className="record-preview">
              <h3>Latest Record</h3>
              <p><strong>City:</strong> {currentRecord.city}</p>
              <p><strong>Temperature:</strong> {currentRecord.tempC ?? 'N/A'} °C</p>
              <p><strong>Humidity:</strong> {currentRecord.humidity ?? 'N/A'} %</p>
              <p><strong>Wind Speed:</strong> {currentRecord.windKph ?? 'N/A'} km/h</p>
              <p><strong>Conditions:</strong> {currentRecord.conditions}</p>
              <p><strong>Timestamp:</strong> {new Date(currentRecord.timestamp).toLocaleString()}</p>
            </div>
          )}
        </section>
      )}

      {tab === 'dashboard' && (
        <section className="card">
          <h2>Statistics</h2>
          <div className="form-group">
            <label>Filter by City (optional)</label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Leave empty for all data"
              disabled={loading}
            />
          </div>
          <button className="btn" onClick={loadStats} disabled={loading}>
            Load Stats (Last 7 Days)
          </button>
          <div className="form-inline" style={{ marginTop: '15px' }}>
            <div className="form-group">
              <label>Forecast Days (2-7)</label>
              <select
                value={forecastDays}
                onChange={(e) => setForecastDays(Number(e.target.value))}
                disabled={loading}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #ddd' }}
              >
                {[2, 3, 4, 5, 6, 7].map((d) => (
                  <option key={d} value={d}>
                    {d} {d === 1 ? 'day' : 'days'}
                  </option>
                ))}
              </select>
            </div>
            <button className="btn secondary" onClick={loadForecast} disabled={loading}>
              Generate {forecastDays}-Day Forecast
            </button>
          </div>

          {stats && (
            <div className="stats-grid">
              <StatCard label="Records" value={stats.record_count} />
              <StatCard label="Avg Temp (°C)" value={formatValue(stats.avg_tempC)} />
              <StatCard label="Min Temp (°C)" value={formatValue(stats.min_tempC)} />
              <StatCard label="Max Temp (°C)" value={formatValue(stats.max_tempC)} />
              <StatCard label="Avg Humidity (%)" value={formatValue(stats.avg_humidity)} />
              <StatCard label="Avg Wind (km/h)" value={formatValue(stats.avg_windKph)} />
            </div>
          )}

          {stats && stats.record_count === 0 && (
            <div className="empty-state">No records found for this period.</div>
          )}

          {forecast && (
            <div className="forecast-container">
              <h3>Forecast ({forecast.forecast_days} days)</h3>
              <table className="history-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Temp (°C)</th>
                    <th>Humidity (%)</th>
                    <th>Wind (km/h)</th>
                  </tr>
                </thead>
                <tbody>
                  {forecast.data.map((entry) => (
                    <tr key={entry.date}>
                      <td>{entry.date}</td>
                      <td>{formatValue(entry.tempC)}</td>
                      <td>{formatValue(entry.humidity)}</td>
                      <td>{formatValue(entry.windKph)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="generated-at">
                Generated: {new Date(forecast.generated_at).toLocaleString()}
              </div>
            </div>
          )}
        </section>
      )}

      {tab === 'history' && (
        <section className="card">
          <h2>Stored Records</h2>
          <div className="form-group">
            <label>Filter by City (optional)</label>
            <input
              type="text"
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Leave empty for all data"
              disabled={loading}
            />
          </div>
          <button className="btn" onClick={loadHistory} disabled={loading}>
            Load 30-Day History
          </button>

          {loading && <div className="loading">Loading...</div>}

          {!loading && history.length > 0 && (
            <div className="table-container">
              <table className="history-table">
                <thead>
                  <tr>
                    <th>City</th>
                    <th>Timestamp</th>
                    <th>Temp (°C)</th>
                    <th>Humidity (%)</th>
                    <th>Wind (km/h)</th>
                    <th>Conditions</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((record, idx) => (
                    <tr key={`${record.timestamp}-${idx}`}>
                      <td>{record.city}</td>
                      <td>{new Date(record.timestamp).toLocaleString()}</td>
                      <td>{formatValue(record.tempC)}</td>
                      <td>{formatValue(record.humidity)}</td>
                      <td>{formatValue(record.windKph)}</td>
                      <td>{record.conditions}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {!loading && history.length === 0 && (
            <div className="empty-state">No stored records yet. Fetch some weather data first.</div>
          )}
        </section>
      )}
    </div>
  );
}

const StatCard = ({ label, value }) => (
  <div className="stat-card">
    <div className="stat-label">{label}</div>
    <div className="stat-value">{value}</div>
  </div>
);

const formatValue = (value) => {
  if (value === null || value === undefined) {
    return 'N/A';
  }
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value : value.toFixed(1);
  }
  return value;
};

export default App;
