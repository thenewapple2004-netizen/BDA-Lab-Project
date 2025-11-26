# Commands to Run the Project on Localhost

## Option 1: Docker Compose (Full Stack with Hadoop)

This runs everything including Hadoop HDFS, backend, and frontend in Docker containers.

### Prerequisites:
- Docker Desktop installed and running
- Docker Compose installed

### Commands:

```powershell
# Navigate to project directory
cd "C:\Users\miana\OneDrive\Desktop\Uni works\big data project\BDA-Lab-Project"

# Start all services (Hadoop + Backend + Frontend)
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f
```

### Access Points:
- **Frontend**: http://localhost:5000
- **Backend API**: http://localhost:5000/api
- **Hadoop NameNode UI**: http://localhost:9870
- **Hadoop DataNode UI**: http://localhost:9864

---

## Option 2: Local Development (Backend + Frontend Only)

This runs the backend and frontend locally without Docker/Hadoop.

### Prerequisites:
- Python 3.11+ installed
- Node.js and npm installed
- Virtual environment set up for Python

### Setup (First Time Only):

```powershell
# Navigate to project directory
cd "C:\Users\miana\OneDrive\Desktop\Uni works\big data project\BDA-Lab-Project"

# Create Python virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Running the Application:

**Terminal 1 - Backend:**
```powershell
# Activate virtual environment (if not already activated)
.\.venv\Scripts\Activate.ps1

# Run backend server
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 5000 --reload
```

**Terminal 2 - Frontend:**
```powershell
# Navigate to frontend directory
cd frontend

# Start React development server
npm start
```

### Access Points:
- **Frontend**: http://localhost:3000 (automatically opens in browser)
- **Backend API**: http://localhost:5000
- **Backend API Docs**: http://localhost:5000/docs (Swagger UI)

---

## Quick Start Scripts

You can also use the provided PowerShell scripts:

**Backend:**
```powershell
.\start-backend.ps1
```

**Frontend:**
```powershell
.\start-frontend.ps1
```

---

## Troubleshooting

### If Docker Compose fails:
- Ensure Docker Desktop is running
- Check if ports 5000, 9870, 9864, 9000 are available
- Try: `docker-compose down -v` to remove volumes and start fresh

### If local development fails:
- Ensure Python virtual environment is activated
- Check if ports 3000 and 5000 are available
- Verify all dependencies are installed: `pip list` and `npm list`

### Port Conflicts:
- Backend uses port 5000
- Frontend uses port 3000
- Hadoop NameNode uses port 9870
- Hadoop DataNode uses port 9864
- Hadoop RPC uses port 9000

