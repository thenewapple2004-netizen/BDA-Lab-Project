# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites Check
- Python 3.7+ ✅
- Node.js 14+ ✅  
- MongoDB (local or cloud) ✅
- OpenWeatherMap API key (free) ✅

### 1. Run Setup Script
```bash
python setup.py
```

### 2. Get API Key
1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Get your API key

### 3. Configure Environment
Edit `backend/.env` file:
```
MONGO_URI=mongodb://localhost:27017/
OPENWEATHER_API_KEY=your_actual_api_key_here
```

### 4. Start MongoDB
**Option A - Local MongoDB:**
```bash
# Windows
mongod

# macOS (with Homebrew)
brew services start mongodb-community

# Ubuntu/Debian
sudo systemctl start mongod
```

**Option B - MongoDB Atlas (Cloud):**
- Create free account at [MongoDB Atlas](https://www.mongodb.com/atlas)
- Get connection string and update `MONGO_URI` in `.env`

### 5. Start Backend
```bash
cd backend
python app.py
```
✅ Backend running on http://localhost:5000

### 6. Start Frontend
```bash
cd frontend
npm start
```
✅ Frontend running on http://localhost:3000

### 7. Collect Initial Data
1. Open http://localhost:3000
2. Click "Collect Bulk Data" button
3. Wait for data collection to complete

### 8. Explore the Dashboard! 🎉

## 🎯 Features to Try

- **Select different cities** from dropdown
- **View current weather** with real-time data
- **Check statistics** for 7-day averages
- **Analyze temperature trends** in interactive charts
- **Compare humidity & pressure** over time
- **Collect data for multiple cities** at once

## 🔧 Troubleshooting

**Backend won't start?**
- Check if MongoDB is running
- Verify API key in `.env` file
- Check port 5000 is not in use

**Frontend won't start?**
- Run `cd frontend && npm install`
- Check if port 3000 is not in use

**No data showing?**
- Click "Collect Bulk Data" first
- Check browser console for errors
- Verify backend is running on port 5000

## 📚 Full Documentation
See `README.md` for complete setup instructions and API documentation.
