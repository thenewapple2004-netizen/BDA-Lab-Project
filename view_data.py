#!/usr/bin/env python3
"""
Simple script to view weather data stored locally.
Usage:
    python view_data.py                    # Show all cities and dates
    python view_data.py --city lahore     # Show data for Lahore
    python view_data.py --date 2025-11-11 # Show data for specific date
    python view_data.py --city lahore --date 2025-11-11  # Combined
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data" / "apps" / "weather" / "ingest"


def read_jsonl(file_path):
    """Read JSONL file and return list of records"""
    records = []
    if not os.path.exists(file_path):
        return records
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except Exception:
                    continue
    return records


def format_record(rec):
    """Format a record for display"""
    return {
        "city": rec.get("city", "N/A"),
        "timestamp": rec.get("timestamp", "N/A"),
        "tempC": rec.get("tempC", "N/A"),
        "humidity": rec.get("humidity", "N/A"),
        "windKph": rec.get("windKph", "N/A"),
        "conditions": rec.get("conditions", "N/A"),
    }


def list_all_data():
    """List all available data"""
    if not DATA_DIR.exists():
        print(f"[ERROR] Data directory not found: {DATA_DIR}")
        return
    
    print(f"Data Location: {DATA_DIR.parent.parent.parent.parent}")
    print(f"Available Data:\n")
    
    partitions = sorted([d for d in DATA_DIR.iterdir() if d.is_dir() and d.name.startswith("date=")])
    
    if not partitions:
        print("  No data found.")
        return
    
    total_records = 0
    for partition in partitions:
        date_str = partition.name.replace("date=", "")
        files = list(partition.glob("*.jsonl"))
        
        if files:
            print(f"  Date: {date_str}:")
            for file in sorted(files):
                city = file.stem
                records = read_jsonl(file)
                count = len(records)
                total_records += count
                print(f"      - {city}: {count} record(s)")
    
    print(f"\nTotal records: {total_records}")


def show_city_data(city):
    """Show all data for a specific city"""
    city = city.lower()
    print(f"Weather Data for: {city.upper()}\n")
    
    partitions = sorted([d for d in DATA_DIR.iterdir() if d.is_dir() and d.name.startswith("date=")])
    
    found = False
    for partition in partitions:
        file_path = partition / f"{city}.jsonl"
        if file_path.exists():
            found = True
            records = read_jsonl(file_path)
            date_str = partition.name.replace("date=", "")
            print(f"Date: {date_str} ({len(records)} records):")
            for rec in records[:5]:  # Show first 5
                fmt = format_record(rec)
                print(f"  - {fmt['timestamp']}: {fmt['tempC']}C, {fmt['humidity']}% humidity, {fmt['windKph']} km/h")
            if len(records) > 5:
                print(f"  ... and {len(records) - 5} more")
            print()
    
    if not found:
        print(f"[ERROR] No data found for city: {city}")


def show_date_data(date_str):
    """Show all data for a specific date"""
    print(f"Weather Data for: {date_str}\n")
    
    partition = DATA_DIR / f"date={date_str}"
    if not partition.exists():
        print(f"[ERROR] No data found for date: {date_str}")
        return
    
    files = sorted(partition.glob("*.jsonl"))
    if not files:
        print(f"  No data files found.")
        return
    
    for file in files:
        city = file.stem
        records = read_jsonl(file)
        print(f"City: {city.upper()} ({len(records)} records):")
        for rec in records[:3]:  # Show first 3
            fmt = format_record(rec)
            print(f"  - {fmt['timestamp']}: {fmt['tempC']}C, {fmt['humidity']}% humidity, {fmt['windKph']} km/h")
        if len(records) > 3:
            print(f"  ... and {len(records) - 3} more")
        print()


def show_combined(city, date_str):
    """Show data for specific city and date"""
    city = city.lower()
    partition = DATA_DIR / f"date={date_str}"
    file_path = partition / f"{city}.jsonl"
    
    if not file_path.exists():
        print(f"[ERROR] No data found for {city} on {date_str}")
        return
    
    records = read_jsonl(file_path)
    print(f"City: {city.upper()} - Date: {date_str} ({len(records)} records):\n")
    
    for rec in records:
        fmt = format_record(rec)
        print(f"  - {fmt['timestamp']}")
        print(f"    Temperature: {fmt['tempC']}C")
        print(f"    Humidity: {fmt['humidity']}%")
        print(f"    Wind: {fmt['windKph']} km/h")
        print(f"    Conditions: {fmt['conditions']}")
        print()


if __name__ == "__main__":
    city = None
    date_str = None
    
    # Parse arguments
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--city" and i + 1 < len(args):
            city = args[i + 1]
            i += 2
        elif args[i] == "--date" and i + 1 < len(args):
            date_str = args[i + 1]
            i += 2
        else:
            i += 1
    
    # Show data based on arguments
    if city and date_str:
        show_combined(city, date_str)
    elif city:
        show_city_data(city)
    elif date_str:
        show_date_data(date_str)
    else:
        list_all_data()

