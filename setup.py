#!/usr/bin/env python3
"""
Quick setup script for Weather Data Analytics Project
This script helps set up the project environment and dependencies
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False

def check_python():
    """Check if Python is installed"""
    try:
        version = sys.version_info
        if version.major >= 3 and version.minor >= 7:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} is installed")
            return True
        else:
            print(f"❌ Python 3.7+ required. Found Python {version.major}.{version.minor}")
            return False
    except:
        print("❌ Python not found")
        return False

def check_node():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()} is installed")
            return True
    except:
        pass
    
    print("❌ Node.js not found. Please install Node.js 14+ from https://nodejs.org/")
    return False

def setup_backend():
    """Set up Python backend"""
    print("\n🐍 Setting up Python backend...")
    
    # Create virtual environment
    if not os.path.exists('backend/venv'):
        if not run_command('cd backend && python -m venv venv', 'Creating virtual environment'):
            return False
    
    # Activate virtual environment and install dependencies
    if platform.system() == "Windows":
        pip_command = 'backend\\venv\\Scripts\\pip'
    else:
        pip_command = 'backend/venv/bin/pip'
    
    if not run_command(f'{pip_command} install -r backend/requirements.txt', 'Installing Python dependencies'):
        return False
    
    # Create .env file if it doesn't exist
    env_file = 'backend/.env'
    if not os.path.exists(env_file):
        print("\n📝 Creating .env file...")
        with open(env_file, 'w') as f:
            f.write('MONGO_URI=mongodb://localhost:27017/\n')
            f.write('OPENWEATHER_API_KEY=your_api_key_here\n')
        print("✅ .env file created. Please add your OpenWeatherMap API key!")
    
    return True

def setup_frontend():
    """Set up React frontend"""
    print("\n⚛️ Setting up React frontend...")
    
    if not run_command('cd frontend && npm install', 'Installing Node.js dependencies'):
        return False
    
    return True

def main():
    """Main setup function"""
    print("🌤️  Weather Data Analytics Project Setup")
    print("=" * 50)
    
    # Check prerequisites
    if not check_python():
        return False
    
    if not check_node():
        return False
    
    # Setup backend
    if not setup_backend():
        return False
    
    # Setup frontend
    if not setup_frontend():
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Get your free OpenWeatherMap API key from: https://openweathermap.org/api")
    print("2. Add the API key to backend/.env file")
    print("3. Install and start MongoDB")
    print("4. Run the backend: cd backend && python app.py")
    print("5. Run the frontend: cd frontend && npm start")
    print("6. Open http://localhost:3000 in your browser")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
