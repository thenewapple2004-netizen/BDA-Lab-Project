from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB connection
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
client = MongoClient(MONGO_URI)
db = client.weather_analytics

# Collections
weather_collection = db.weather_data
cities_collection = db.cities

# OpenWeatherMap API configuration
API_KEY = os.getenv('OPENWEATHER_API_KEY', 'your_api_key_here')
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

@app.route('/api/weather/current', methods=['GET'])
def get_current_weather():
    """Get current weather for a specific city"""
    city = request.args.get('city', 'London')
    
    try:
        # Try to get from database first
        cached_data = weather_collection.find_one(
            {"city": city.lower()},
            sort=[("timestamp", -1)]
        )
        
        # If data is less than 10 minutes old, return cached data
        if cached_data and (datetime.now() - cached_data['timestamp']).seconds < 600:
            return jsonify(cached_data)
        
        # Fetch new data from API
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric'
        }
        
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            
            weather_data = {
                'city': city.lower(),
                'timestamp': datetime.now(),
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'description': data['weather'][0]['description'],
                'wind_speed': data['wind']['speed'],
                'country': data['sys']['country'],
                'coordinates': {
                    'lat': data['coord']['lat'],
                    'lon': data['coord']['lon']
                }
            }
            
            # Save to database
            weather_collection.insert_one(weather_data)
            
            return jsonify(weather_data)
        else:
            return jsonify({'error': 'Failed to fetch weather data'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather/history', methods=['GET'])
def get_weather_history():
    """Get historical weather data for a city"""
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 7))
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        data = list(weather_collection.find({
            'city': city.lower(),
            'timestamp': {'$gte': start_date}
        }).sort('timestamp', 1))
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather/cities', methods=['GET'])
def get_cities():
    """Get list of available cities"""
    try:
        cities = weather_collection.distinct('city')
        return jsonify(cities)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/temperature-trends', methods=['GET'])
def get_temperature_trends():
    """Get temperature trends for analytics"""
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 7))
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        data = list(weather_collection.find({
            'city': city.lower(),
            'timestamp': {'$gte': start_date}
        }, {'temperature': 1, 'timestamp': 1, '_id': 0}).sort('timestamp', 1))
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/humidity-pressure', methods=['GET'])
def get_humidity_pressure():
    """Get humidity and pressure data for analytics"""
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 7))
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        data = list(weather_collection.find({
            'city': city.lower(),
            'timestamp': {'$gte': start_date}
        }, {'humidity': 1, 'pressure': 1, 'timestamp': 1, '_id': 0}).sort('timestamp', 1))
        
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/statistics', methods=['GET'])
def get_weather_statistics():
    """Get weather statistics for a city"""
    city = request.args.get('city', 'London')
    days = int(request.args.get('days', 7))
    
    try:
        start_date = datetime.now() - timedelta(days=days)
        
        pipeline = [
            {
                '$match': {
                    'city': city.lower(),
                    'timestamp': {'$gte': start_date}
                }
            },
            {
                '$group': {
                    '_id': None,
                    'avg_temp': {'$avg': '$temperature'},
                    'max_temp': {'$max': '$temperature'},
                    'min_temp': {'$min': '$temperature'},
                    'avg_humidity': {'$avg': '$humidity'},
                    'avg_pressure': {'$avg': '$pressure'},
                    'avg_wind_speed': {'$avg': '$wind_speed'}
                }
            }
        ]
        
        result = list(weather_collection.aggregate(pipeline))
        
        if result:
            return jsonify(result[0])
        else:
            return jsonify({'error': 'No data found'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/weather/bulk-collect', methods=['POST'])
def bulk_collect_weather():
    """Collect weather data for multiple cities"""
    cities = request.json.get('cities', ['London', 'New York', 'Tokyo', 'Paris'])
    
    try:
        collected_data = []
        
        for city in cities:
            params = {
                'q': city,
                'appid': API_KEY,
                'units': 'metric'
            }
            
            response = requests.get(BASE_URL, params=params)
            if response.status_code == 200:
                data = response.json()
                
                weather_data = {
                    'city': city.lower(),
                    'timestamp': datetime.now(),
                    'temperature': data['main']['temp'],
                    'humidity': data['main']['humidity'],
                    'pressure': data['main']['pressure'],
                    'description': data['weather'][0]['description'],
                    'wind_speed': data['wind']['speed'],
                    'country': data['sys']['country'],
                    'coordinates': {
                        'lat': data['coord']['lat'],
                        'lon': data['coord']['lon']
                    }
                }
                
                weather_collection.insert_one(weather_data)
                collected_data.append(weather_data)
        
        return jsonify({
            'message': f'Successfully collected data for {len(collected_data)} cities',
            'data': collected_data
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
