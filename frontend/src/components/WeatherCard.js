import React from 'react';

const WeatherCard = ({ weather }) => {
  if (!weather) return null;

  const getWeatherIcon = (description) => {
    const desc = description.toLowerCase();
    if (desc.includes('clear')) return 'fas fa-sun';
    if (desc.includes('cloud')) return 'fas fa-cloud';
    if (desc.includes('rain')) return 'fas fa-cloud-rain';
    if (desc.includes('snow')) return 'fas fa-snowflake';
    if (desc.includes('storm')) return 'fas fa-bolt';
    if (desc.includes('mist') || desc.includes('fog')) return 'fas fa-smog';
    return 'fas fa-cloud-sun';
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <div className="card">
      <h3>
        <i className={getWeatherIcon(weather.description)}></i>
        {weather.city.charAt(0).toUpperCase() + weather.city.slice(1)} Weather
      </h3>
      
      <div className="weather-info">
        <div className="info-item">
          <i className="fas fa-thermometer-half"></i>
          <div className="label">Temperature</div>
          <div className="value">{weather.temperature.toFixed(1)}°C</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-tint"></i>
          <div className="label">Humidity</div>
          <div className="value">{weather.humidity}%</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-tachometer-alt"></i>
          <div className="label">Pressure</div>
          <div className="value">{weather.pressure} hPa</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-wind"></i>
          <div className="label">Wind Speed</div>
          <div className="value">{weather.wind_speed} m/s</div>
        </div>
      </div>
      
      <div style={{ marginTop: '15px', textAlign: 'center' }}>
        <div style={{ 
          fontSize: '1.1rem', 
          color: '#667eea', 
          fontWeight: 'bold',
          marginBottom: '5px'
        }}>
          {weather.description.charAt(0).toUpperCase() + weather.description.slice(1)}
        </div>
        <div style={{ fontSize: '0.9rem', color: '#666' }}>
          {weather.country} • Updated: {formatTimestamp(weather.timestamp)}
        </div>
      </div>
    </div>
  );
};

export default WeatherCard;
