# Weather Data Analytics Project

A mid-level weather data analytics application for Big Data Analytics course project.

## Project Structure
```
big data project/
├── backend/
│   ├── app.py                 # Flask API server
│   ├── requirements.txt       # Python dependencies
│   ├── data_collector.py      # Weather data collection script
│   └── env_example.txt        # Environment variables example
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── App.js            # Main React app
│   │   ├── index.js          # React entry point
│   │   └── index.css         # Global styles
│   └── package.json          # Node.js dependencies
└── README.md
```

## Features
- **Real-time Weather Data**: Fetch current weather for any city
- **Historical Analysis**: View 7-day weather trends and statistics
- **Interactive Charts**: Temperature, humidity, and pressure visualizations
- **Multi-city Support**: Compare weather across different cities
- **Bulk Data Collection**: Collect weather data for multiple cities at once
- **Responsive Design**: Modern UI with mobile support

## Prerequisites
- Python 3.7+
- Node.js 14+
- MongoDB (local or cloud)
- OpenWeatherMap API key (free at openweathermap.org)

## Setup Instructions

### 1. Backend Setup

1. **Navigate to backend folder:**
   ```bash
   cd backend
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Copy `env_example.txt` to `.env`
   - Add your OpenWeatherMap API key:
     ```
     OPENWEATHER_API_KEY=your_actual_api_key_here
     MONGO_URI=mongodb://localhost:27017/
     ```

5. **Set up MongoDB:**
   - Install MongoDB locally or use MongoDB Atlas (cloud)
   - Make sure MongoDB is running on port 27017

6. **Run the Flask server:**
   ```bash
   python app.py
   ```
   Server will start on http://localhost:5000

### 2. Frontend Setup

1. **Navigate to frontend folder:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```
   App will open in browser at http://localhost:3000

### 3. Initial Data Collection

To populate the database with sample data:

1. **Run the data collector script:**
   ```bash
   cd backend
   python data_collector.py
   ```

2. **Or use the bulk collection feature in the web interface**

## API Endpoints

### Weather Data
- `GET /api/weather/current?city=London` - Get current weather
- `GET /api/weather/history?city=London&days=7` - Get historical data
- `GET /api/weather/cities` - Get available cities
- `POST /api/weather/bulk-collect` - Collect data for multiple cities

### Analytics
- `GET /api/analytics/temperature-trends?city=London&days=7` - Temperature trends
- `GET /api/analytics/humidity-pressure?city=London&days=7` - Humidity/pressure data
- `GET /api/analytics/statistics?city=London&days=7` - Weather statistics

## Usage Guide

### Getting Started
1. Start both backend and frontend servers
2. Open http://localhost:3000 in your browser
3. Select a city from the dropdown
4. View current weather and analytics

### Features Overview
- **Current Weather**: Real-time weather information with icons
- **Statistics Card**: 7-day averages and extremes
- **Temperature Chart**: Line chart showing temperature trends
- **Humidity/Pressure Chart**: Dual-axis chart for humidity and pressure
- **Bulk Data Collection**: Collect data for multiple cities

### Data Collection
- Weather data is cached for 10 minutes to avoid API rate limits
- Use "Collect Bulk Data" button to populate database with multiple cities
- Historical data builds up over time as you collect more data

## Technologies Used
- **Backend**: Python, Flask, PyMongo, Requests
- **Frontend**: React.js, Chart.js, Axios
- **Database**: MongoDB
- **API**: OpenWeatherMap API
- **Styling**: CSS3 with modern design patterns

## Project Features for Big Data Analytics Course

This project demonstrates several big data analytics concepts:

1. **Data Collection**: Real-time data ingestion from external APIs
2. **Data Storage**: NoSQL database (MongoDB) for flexible data structure
3. **Data Processing**: Aggregation pipelines for statistics calculation
4. **Data Visualization**: Interactive charts and dashboards
5. **Analytics**: Trend analysis, statistical calculations, and data comparison

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error:**
   - Ensure MongoDB is running
   - Check connection string in `.env` file

2. **API Key Error:**
   - Verify OpenWeatherMap API key is correct
   - Check if you have API quota remaining

3. **CORS Issues:**
   - Backend has CORS enabled for localhost:3000
   - If using different port, update CORS settings

4. **No Data Showing:**
   - Run the data collector script first
   - Check browser console for errors
   - Verify backend is running on port 5000

## Future Enhancements

- User authentication and personal dashboards
- Weather alerts and notifications
- Machine learning predictions
- More detailed analytics and comparisons
- Export data functionality
- Mobile app development
