#!/usr/bin/env python3
"""
Debug script to test different API versions and endpoints for plan details
"""

import requests
import json
from google.cloud import bigquery

PROJECT_ID = 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

def get_sample_plan():
    """Get a sample plan ID to test with"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT plan_id, retailer, plan_name
    FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
    WHERE retailer = 'agl'
    LIMIT 1
    """
    
    result = client.query(query).to_dataframe()
    if not result.empty:
        return result.iloc[0]['plan_id'], result.iloc[0]['retailer'], result.iloc[0]['plan_name']
    return None, None, None

def test_plan_detail_api(plan_id, retailer):
    """Test different API versions and endpoints"""
    print(f"🧪 Testing plan detail API for {plan_id} from {retailer}")
    
    base_url = f"https://cdr.energymadeeasy.gov.au/{retailer}/cds-au"
    
    # Different endpoints to try
    endpoints = [
        f"{base_url}/v1/energy/plans/{plan_id}",
        f"{base_url}/v2/energy/plans/{plan_id}",
        f"{base_url}/v3/energy/plans/{plan_id}",
    ]
    
    # Different API versions to try
    api_versions = ["1", "2", "3"]
    
    for endpoint in endpoints:
        for version in api_versions:
            print(f"\n--- Testing {endpoint} with x-v: {version} ---")
            
            headers = {
                "x-v": version,
                "Accept": "application/json",
                "User-Agent": "DebugTool/1.0"
            }
            
            try:
                response = requests.get(endpoint, headers=headers, timeout=10)
                print(f"Status: {response.status_code}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    data = response.json()
                    print("✅ SUCCESS!")
                    print(f"Plan data keys: {list(data.keys())}")
                    if 'data' in data:
                        plan_data = data['data']
                        print(f"Plan detail keys: {list(plan_data.keys())}")
                        
                        # Check for contract data
                        if 'electricityContract' in plan_data:
                            print("📊 Has electricity contract data")
                        if 'gasContract' in plan_data:
                            print("⛽ Has gas contract data")
                        if 'geography' in plan_data:
                            print("🗺️  Has geography data")
                            
                        return endpoint, version, data
                        
                elif response.status_code == 406:
                    print("❌ 406 Not Acceptable")
                elif response.status_code == 404:
                    print("❌ 404 Not Found")
                else:
                    print(f"❌ {response.status_code}: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
    
    return None, None, None

def extract_raw_plan_data():
    """Try to extract detailed data from the raw_data JSON in our existing table"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT plan_id, retailer, plan_name, raw_data
    FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
    WHERE retailer = 'agl'
    AND raw_data IS NOT NULL
    LIMIT 5
    """
    
    result = client.query(query).to_dataframe()
    
    print(f"\n🔍 Analyzing raw plan data from existing records...")
    
    for _, row in result.iterrows():
        print(f"\n--- Plan: {row['plan_name']} ({row['plan_id']}) ---")
        
        try:
            raw_data = json.loads(row['raw_data'])
            print(f"Raw data keys: {list(raw_data.keys())}")
            
            # Check for geography data in raw plan data
            if 'geography' in raw_data:
                geo = raw_data['geography']
                print(f"Geography keys: {list(geo.keys())}")
                
                if 'includedPostcodes' in geo:
                    postcodes = geo['includedPostcodes']
                    print(f"Included postcodes: {len(postcodes)} (sample: {postcodes[:5]})")
                
                if 'distributors' in geo:
                    print(f"Distributors: {geo['distributors']}")
            
            # The raw plan data might not have detailed tariff info
            # That's why we need the plan detail API
            
        except json.JSONDecodeError:
            print("❌ Failed to parse raw_data JSON")
        except Exception as e:
            print(f"❌ Error analyzing raw data: {e}")

def main():
    print("🚀 Debugging Energy Plan Detail API...")
    
    # Get a sample plan
    plan_id, retailer, plan_name = get_sample_plan()
    
    if not plan_id:
        print("❌ No sample plan found")
        return
    
    print(f"📋 Using sample plan: {plan_name} ({plan_id}) from {retailer}")
    
    # Test the plan detail API
    working_endpoint, working_version, sample_data = test_plan_detail_api(plan_id, retailer)
    
    if working_endpoint:
        print(f"\n🎉 Found working endpoint!")
        print(f"Endpoint: {working_endpoint}")
        print(f"API Version: {working_version}")
        
        # Show sample of what data is available
        if sample_data and 'data' in sample_data:
            plan_detail = sample_data['data']
            print(f"\n📊 Available data in plan detail:")
            for key, value in plan_detail.items():
                if isinstance(value, dict):
                    print(f"  {key}: {list(value.keys())}")
                elif isinstance(value, list):
                    print(f"  {key}: list with {len(value)} items")
                else:
                    print(f"  {key}: {type(value).__name__}")
    else:
        print(f"\n❌ No working endpoint found for plan detail API")
        print(f"💡 Let's check what data we have in raw_data...")
        extract_raw_plan_data()

if __name__ == "__main__":
    main()