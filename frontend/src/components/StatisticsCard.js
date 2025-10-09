import React from 'react';

const StatisticsCard = ({ statistics }) => {
  if (!statistics) return null;

  return (
    <div className="card">
      <h3>
        <i className="fas fa-chart-bar"></i>
        Weather Statistics (7 Days)
      </h3>
      
      <div className="weather-info">
        <div className="info-item">
          <i className="fas fa-thermometer-half"></i>
          <div className="label">Avg Temperature</div>
          <div className="value">{statistics.avg_temp?.toFixed(1)}°C</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-arrow-up"></i>
          <div className="label">Max Temperature</div>
          <div className="value">{statistics.max_temp?.toFixed(1)}°C</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-arrow-down"></i>
          <div className="label">Min Temperature</div>
          <div className="value">{statistics.min_temp?.toFixed(1)}°C</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-tint"></i>
          <div className="label">Avg Humidity</div>
          <div className="value">{statistics.avg_humidity?.toFixed(1)}%</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-tachometer-alt"></i>
          <div className="label">Avg Pressure</div>
          <div className="value">{statistics.avg_pressure?.toFixed(1)} hPa</div>
        </div>
        
        <div className="info-item">
          <i className="fas fa-wind"></i>
          <div className="label">Avg Wind Speed</div>
          <div className="value">{statistics.avg_wind_speed?.toFixed(1)} m/s</div>
        </div>
      </div>
    </div>
  );
};

export default StatisticsCard;
