#!/usr/bin/env python3
"""
Simple monitoring script to check ETL status
Usage: python monitor.py
"""

import requests
import json
from datetime import datetime
import sys

# Configuration
PROJECT_ID = "wattsmybill-dev"
SERVICE_NAME = "energy-plans-etl"
REGION = "australia-southeast1"

# You'll need to get this after deployment
SERVICE_URL = "https://energy-plans-etl-xxxxx-ts.a.run.app"  # Replace with actual URL

def check_service_health():
    """Check if the service is healthy"""
    try:
        response = requests.get(f"{SERVICE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service healthy: {data['status']}")
            return True
        else:
            print(f"❌ Service unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot reach service: {e}")
        return False

def get_data_stats():
    """Get current data statistics"""
    try:
        response = requests.get(f"{SERVICE_URL}/stats", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"\n📊 Data Statistics (as of {data['timestamp']}):")
            print(f"  Total plans: {data['total_plans']:,}")
            print(f"  Tariff rates: {data['total_tariff_rates']:,}")
            print(f"  Geography records: {data['total_geography_records']:,}")
            
            print(f"\n📋 Plans by retailer:")
            for retailer_data in data['plans_by_retailer'][:10]:
                print(f"  {retailer_data['retailer']}: {retailer_data['plan_count']:,} {retailer_data['fuel_type']} plans")
            
            return True
        else:
            print(f"❌ Cannot get stats: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return False

def trigger_manual_extraction(extraction_type="plans"):
    """Manually trigger an extraction"""
    endpoints = {
        "plans": "/extract-plans",
        "tariffs": "/extract-tariffs", 
        "full": "/full-etl"
    }
    
    if extraction_type not in endpoints:
        print(f"❌ Invalid extraction type. Use: {list(endpoints.keys())}")
        return
    
    endpoint = endpoints[extraction_type]
    
    print(f"🚀 Triggering {extraction_type} extraction...")
    
    try:
        payload = {}
        if extraction_type == "tariffs":
            payload = {"sample_size": 50}
        
        response = requests.post(
            f"{SERVICE_URL}{endpoint}", 
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Extraction completed: {data['status']}")
            print(f"   Message: {data['message']}")
            if 'plan_count' in data:
                print(f"   Plans: {data['plan_count']:,}")
            if 'rates_extracted' in data:
                print(f"   Rates: {data['rates_extracted']:,}")
        else:
            print(f"❌ Extraction failed: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error triggering extraction: {e}")

def main():
    print("🔍 Energy Plans ETL Monitor")
    print("=" * 40)
    
    # Check service health
    if not check_service_health():
        sys.exit(1)
    
    # Get current stats
    get_data_stats()
    
    # Interactive menu
    while True:
        print(f"\n🛠️  Available actions:")
        print(f"  1. Refresh stats")
        print(f"  2. Trigger plans extraction")
        print(f"  3. Trigger tariffs extraction (sample)")
        print(f"  4. Trigger full ETL")
        print(f"  5. Exit")
        
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == "1":
            get_data_stats()
        elif choice == "2":
            trigger_manual_extraction("plans")
        elif choice == "3":
            trigger_manual_extraction("tariffs")
        elif choice == "4":
            confirm = input("Full ETL takes a long time. Continue? (y/N): ")
            if confirm.lower() == 'y':
                trigger_manual_extraction("full")
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    main()