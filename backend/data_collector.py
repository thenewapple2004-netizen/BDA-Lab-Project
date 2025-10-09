"""
Weather Data Collector Script
This script can be used to collect initial weather data for the project
"""
import requests
import time
from datetime import datetime
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
API_KEY = os.getenv('OPENWEATHER_API_KEY', 'your_api_key_here')
BASE_URL = "http://api.openweathermap.org/data/2.5/weather"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client.weather_analytics
weather_collection = db.weather_data

# List of cities to collect data for
CITIES = [
    'London', 'New York', 'Tokyo', 'Paris', 'Sydney',
    'Berlin', 'Moscow', 'Cairo', 'Mumbai', 'Beijing',
    'Los Angeles', 'Chicago', 'Toronto', 'Madrid', 'Rome'
]

def collect_weather_data(city):
    """Collect weather data for a single city"""
    try:
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
            
            # Insert into database
            weather_collection.insert_one(weather_data)
            print(f"✓ Collected data for {city}")
            return True
        else:
            print(f"✗ Failed to collect data for {city}: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error collecting data for {city}: {str(e)}")
        return False

def main():
    """Main function to collect data for all cities"""
    print("Starting weather data collection...")
    print(f"Collecting data for {len(CITIES)} cities...")
    
    successful_collections = 0
    
    for city in CITIES:
        if collect_weather_data(city):
            successful_collections += 1
        time.sleep(1)  # Rate limiting
    
    print(f"\nData collection complete!")
    print(f"Successfully collected data for {successful_collections}/{len(CITIES)} cities")
    
    # Print some statistics
    total_records = weather_collection.count_documents({})
    print(f"Total weather records in database: {total_records}")

if __name__ == "__main__":
    main()
