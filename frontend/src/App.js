import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
} from 'chart.js';
import './index.css';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:5000';

function App() {
  const [city, setCity] = useState('');
  const [cities, setCities] = useState([]);
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [latest, setLatest] = useState(null);
  const [forecastDays, setForecastDays] = useState(5);
  const [lookback, setLookback] = useState(30);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [storageType, setStorageType] = useState('unknown');

  useEffect(() => {
    loadHealth();
  }, []);

  useEffect(() => {
    const init = async () => {
      await loadCities();
    };
    init();
  }, [loadCities]);

  useEffect(() => {
    if (city !== undefined) {
      refreshData();
    }
  }, [city, refreshData]);

  const setStatus = (msg, err = null) => {
    setMessage(msg);
    setError(err);
  };

  const buildParams = () => {
    const params = { city: city || undefined, days: 365 };
    if (startDate) params.start = startDate;
    if (endDate) params.end = endDate;
    return params;
  };

  const loadHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/health`);
      setStorageType(res.data.storage);
    } catch {
      setStorageType('unavailable');
    }
  };

  const loadCities = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/cities`);
      setCities(res.data.cities || []);
      if (!city && res.data.cities?.length) {
        setCity(res.data.cities[0]);
      }
    } catch {
      // keep silent; city list is optional
    }
  }, [city]);

  const loadHistory = useCallback(async () => {
    setStatus(null, null);
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/history`, { params: buildParams() });
      setHistory(res.data.records || []);
      setStatus(`Loaded ${res.data.count} records from storage.`);
    } catch (err) {
      setStatus(null, err.response?.data?.detail || 'Failed to load history.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadStats = useCallback(async () => {
    setStatus(null, null);
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/stats`, { params: buildParams() });
      setStats(res.data);
      setStatus('Statistics refreshed.');
    } catch (err) {
      setStatus(null, err.response?.data?.detail || 'Failed to load statistics.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadLatest = useCallback(async () => {
    if (!city) return;
    setStatus(null, null);
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/weather`, {
        params: { city, mode: 'current' },
      });
      setLatest(res.data.record);
      setStatus('Latest record loaded.');
    } catch (err) {
      setLatest(null);
      setStatus(null, err.response?.data?.detail || 'No latest record found.');
    } finally {
      setLoading(false);
    }
  }, [city]);

  const loadForecast = useCallback(async () => {
    if (!city) {
      setStatus(null, 'Select a city to forecast.');
      return;
    }
    setStatus(null, null);
    setLoading(true);
    try {
      const res = await axios.get(`${API_BASE}/forecast`, {
        params: { city, days: forecastDays, lookback },
      });
      setForecast(res.data);
      setStatus(`Forecast generated for ${forecastDays} days.`);
    } catch (err) {
      setStatus(null, err.response?.data?.detail || 'Failed to generate forecast.');
    } finally {
      setLoading(false);
    }
  }, [city, forecastDays, lookback]);

  const refreshData = useCallback(async () => {
    await loadHistory();
    await loadStats();
    await loadLatest();
  }, [loadHistory, loadLatest, loadStats]);

  const chartData = useMemo(() => {
    const sorted = [...history].sort(
      (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
    );
    const labels = sorted.map((r) => new Date(r.timestamp).toLocaleString());
    return {
      labels,
      temp: sorted.map((r) => r.tempC ?? null),
      humidity: sorted.map((r) => r.humidity ?? null),
      wind: sorted.map((r) => r.windKph ?? null),
    };
  }, [history]);

  const makeLineConfig = (label, data, color) => ({
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label,
          data,
          borderColor: color,
          backgroundColor: `${color}33`,
          tension: 0.3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: true },
        tooltip: { mode: 'index', intersect: false },
      },
      interaction: { mode: 'nearest', intersect: false },
      scales: {
        x: { ticks: { maxRotation: 45, minRotation: 0 }, grid: { display: false } },
        y: { grid: { color: '#eee' } },
      },
    },
  });

  return (
    <div className="container">
      <header className="header">
        <h1>Weather Data Analytics</h1>
        <p>Offline/local dataset • HDFS or local storage</p>
        <div className="storage-indicator">
          Storage backend: <strong>{storageType}</strong>
        </div>
      </header>

      {error && <div className="error">{error}</div>}
      {message && <div className="success">{message}</div>}

        <section className="card">
        <h2>Filters & Actions</h2>
        <div className="controls">
          <div className="select-wrapper">
            <select value={city} onChange={(e) => setCity(e.target.value)}>
              <option value="">All cities</option>
              {cities.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="form-inline">
            <div>
              <label>Start date</label>
              <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} />
            </div>
            <div>
              <label>End date</label>
              <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} />
            </div>
          </div>
            </div>

        <div className="actions">
          <button className="btn" onClick={refreshData} disabled={loading}>
            Refresh data
          </button>
          <button className="btn secondary" onClick={loadForecast} disabled={loading || !city}>
            Forecast ({forecastDays} days)
          </button>
        </div>

        <div className="form-inline">
          <div>
            <label>Forecast days (2-7)</label>
              <select
                value={forecastDays}
                onChange={(e) => setForecastDays(Number(e.target.value))}
                disabled={loading}
              >
                {[2, 3, 4, 5, 6, 7].map((d) => (
                  <option key={d} value={d}>
                  {d} days
                  </option>
                ))}
              </select>
            </div>
          <div>
            <label>Lookback days</label>
            <input
              type="number"
              min="3"
              value={lookback}
              onChange={(e) => setLookback(Number(e.target.value))}
              disabled={loading}
            />
          </div>
        </div>
      </section>

      <section className="dashboard">
        <div className="card">
          <h3>Latest record</h3>
          {latest ? (
            <div className="record-preview">
              <p><strong>City:</strong> {latest.city}</p>
              <p><strong>Timestamp:</strong> {new Date(latest.timestamp).toLocaleString()}</p>
              <p><strong>Temp:</strong> {formatValue(latest.tempC)} °C</p>
              <p><strong>Humidity:</strong> {formatValue(latest.humidity)} %</p>
              <p><strong>Wind:</strong> {formatValue(latest.windKph)} km/h</p>
              <p><strong>Conditions:</strong> {latest.conditions || 'N/A'}</p>
            </div>
          ) : (
            <div className="empty-state">No latest record for this filter.</div>
          )}
          </div>

        <div className="card">
          <h3>Summary</h3>
          {stats ? (
            <div className="stats-grid">
              <StatCard label="Records" value={stats.record_count} />
              <StatCard label="Avg Temp (°C)" value={formatValue(stats.avg_tempC)} />
              <StatCard label="Min Temp (°C)" value={formatValue(stats.min_tempC)} />
              <StatCard label="Max Temp (°C)" value={formatValue(stats.max_tempC)} />
              <StatCard label="Avg Humidity (%)" value={formatValue(stats.avg_humidity)} />
              <StatCard label="Avg Wind (km/h)" value={formatValue(stats.avg_windKph)} />
            </div>
          ) : (
            <div className="empty-state">Load data to view stats.</div>
          )}
        </div>
      </section>

      <section className="chart-container">
        <h3>Trends</h3>
        {history.length === 0 && <div className="empty-state">No data to chart.</div>}
        {history.length > 0 && (
          <>
            <Line {...makeLineConfig('Temperature (°C)', chartData.temp, '#667eea')} />
            <Line {...makeLineConfig('Humidity (%)', chartData.humidity, '#10b981')} />
            <Line {...makeLineConfig('Wind (km/h)', chartData.wind, '#f59e0b')} />
          </>
        )}
      </section>

      <section className="card">
        <h2>Forecast</h2>
        {forecast && forecast.data?.length ? (
            <div className="forecast-container">
            <h3>{forecast.city} • next {forecast.forecast_days} days</h3>
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
              Generated: {new Date(forecast.generated_at).toLocaleString()} • lookback {forecast.lookback_days} days
            </div>
          </div>
        ) : (
          <div className="empty-state">Generate a forecast to see results.</div>
          )}
        </section>

        <section className="card">
        <h2>History</h2>
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
          <div className="empty-state">No stored records for this filter.</div>
          )}
        </section>
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
