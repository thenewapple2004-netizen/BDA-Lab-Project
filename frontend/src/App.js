import React, { useState, useEffect } from 'react';
import axios from 'axios';
import WeatherCard from './components/WeatherCard';
import TemperatureChart from './components/TemperatureChart';
import HumidityPressureChart from './components/HumidityPressureChart';
import StatisticsCard from './components/StatisticsCard';
import './index.css';

const API_BASE_URL = 'http://localhost:5000/api';

function App() {
  const [currentWeather, setCurrentWeather] = useState(null);
  const [selectedCity, setSelectedCity] = useState('London');
  const [cities, setCities] = useState(['London']);
  const [temperatureData, setTemperatureData] = useState([]);
  const [humidityPressureData, setHumidityPressureData] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Fetch available cities
  useEffect(() => {
    fetchCities();
  }, []);

  // Fetch weather data when city changes
  useEffect(() => {
    if (selectedCity) {
      fetchCurrentWeather();
      fetchTemperatureTrends();
      fetchHumidityPressure();
      fetchStatistics();
    }
  }, [selectedCity]);

  const fetchCities = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/weather/cities`);
      if (response.data.length > 0) {
        setCities(response.data);
      }
    } catch (error) {
      console.error('Error fetching cities:', error);
    }
  };

  const fetchCurrentWeather = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/weather/current`, {
        params: { city: selectedCity }
      });
      setCurrentWeather(response.data);
    } catch (error) {
      setError('Failed to fetch current weather data');
      console.error('Error fetching current weather:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTemperatureTrends = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/analytics/temperature-trends`, {
        params: { city: selectedCity, days: 7 }
      });
      setTemperatureData(response.data);
    } catch (error) {
      console.error('Error fetching temperature trends:', error);
    }
  };

  const fetchHumidityPressure = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/analytics/humidity-pressure`, {
        params: { city: selectedCity, days: 7 }
      });
      setHumidityPressureData(response.data);
    } catch (error) {
      console.error('Error fetching humidity pressure data:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/analytics/statistics`, {
        params: { city: selectedCity, days: 7 }
      });
      setStatistics(response.data);
    } catch (error) {
      console.error('Error fetching statistics:', error);
    }
  };

  const collectBulkData = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const response = await axios.post(`${API_BASE_URL}/weather/bulk-collect`, {
        cities: ['London', 'New York', 'Tokyo', 'Paris', 'Sydney', 'Berlin', 'Moscow', 'Cairo', 'Mumbai', 'Beijing']
      });
      
      setSuccess(response.data.message);
      // Refresh cities list
      fetchCities();
    } catch (error) {
      setError('Failed to collect bulk weather data');
      console.error('Error collecting bulk data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCityChange = (e) => {
    setSelectedCity(e.target.value);
  };

  return (
    <div className="container">
      <div className="header">
        <h1><i className="fas fa-cloud-sun"></i> Weather Analytics Dashboard</h1>
        <p>Real-time weather data analysis and visualization</p>
      </div>

      {error && <div className="error">{error}</div>}
      {success && <div className="success">{success}</div>}

      <div className="controls">
        <div className="select-wrapper">
          <select value={selectedCity} onChange={handleCityChange} disabled={loading}>
            {cities.map(city => (
              <option key={city} value={city}>
                {city.charAt(0).toUpperCase() + city.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <button 
          className="btn" 
          onClick={fetchCurrentWeather} 
          disabled={loading}
        >
          <i className="fas fa-sync-alt"></i> Refresh Weather
        </button>
        <button 
          className="btn" 
          onClick={collectBulkData} 
          disabled={loading}
        >
          <i className="fas fa-download"></i> Collect Bulk Data
        </button>
      </div>

      {loading && (
        <div className="loading">
          <i className="fas fa-spinner"></i>
          <span style={{ marginLeft: '10px' }}>Loading...</span>
        </div>
      )}

      {currentWeather && !loading && (
        <div className="dashboard">
          <WeatherCard weather={currentWeather} />
          {statistics && <StatisticsCard statistics={statistics} />}
        </div>
      )}

      <div className="chart-container">
        <h3><i className="fas fa-chart-line"></i> Temperature Trends (7 Days)</h3>
        {temperatureData.length > 0 ? (
          <TemperatureChart data={temperatureData} />
        ) : (
          <div className="loading">
            <i className="fas fa-chart-line"></i>
            <span style={{ marginLeft: '10px' }}>No temperature data available</span>
          </div>
        )}
      </div>

      <div className="chart-container">
        <h3><i className="fas fa-chart-area"></i> Humidity & Pressure Trends (7 Days)</h3>
        {humidityPressureData.length > 0 ? (
          <HumidityPressureChart data={humidityPressureData} />
        ) : (
          <div className="loading">
            <i className="fas fa-chart-area"></i>
            <span style={{ marginLeft: '10px' }}>No humidity/pressure data available</span>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
