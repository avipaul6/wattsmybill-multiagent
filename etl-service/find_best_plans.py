#!/usr/bin/env python3
"""
Simple script to find best energy plans from BigQuery
Usage: python find_best_plans.py --kwh 8000 --postcode 3000
"""

import argparse
from google.cloud import bigquery
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = 'wattsmybill-dev'
DATASET_ID = 'energy_plans'
TABLE_ID = 'plans_simple'

def get_plan_summary():
    """Get summary of plans in database"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
        retailer,
        fuel_type,
        plan_type,
        customer_type,
        COUNT(*) as plan_count
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE 
        (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
        AND effective_from <= CURRENT_TIMESTAMP()
    GROUP BY retailer, fuel_type, plan_type, customer_type
    ORDER BY retailer, fuel_type, plan_type
    """
    
    return client.query(query).to_dataframe()

def find_plans_for_usage(annual_kwh, postcode=None, fuel_type="ELECTRICITY", customer_type="RESIDENTIAL"):
    """Find best plans for given usage"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Simple cost estimation based on plan type
    query = f"""
    SELECT 
        plan_id,
        plan_name,
        brand,
        retailer,
        plan_type,
        fuel_type,
        customer_type,
        application_url,
        
        -- Simple cost estimation
        CASE 
            WHEN plan_type = 'STANDING' THEN {annual_kwh} * 0.35 + 365 * 1.20
            WHEN plan_type = 'MARKET' THEN {annual_kwh} * 0.28 + 365 * 1.20
            ELSE {annual_kwh} * 0.30 + 365 * 1.20
        END AS estimated_annual_cost
        
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE 
        fuel_type = '{fuel_type}'
        AND customer_type = '{customer_type}'
        AND (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
        AND effective_from <= CURRENT_TIMESTAMP()
        AND plan_name IS NOT NULL
        AND brand IS NOT NULL
    
    ORDER BY estimated_annual_cost ASC
    LIMIT 20
    """
    
    result = client.query(query).to_dataframe()
    
    if not result.empty:
        # Add monthly cost
        result['estimated_monthly_cost'] = result['estimated_annual_cost'] / 12
    
    return result

def check_postcode_availability(postcode):
    """Check if we have any geographic data for the postcode"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # This is a simple check - in the detailed version we'd have proper geography tables
    query = f"""
    SELECT COUNT(*) as plans_with_geo_data
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE raw_data LIKE '%{postcode}%'
    """
    
    try:
        result = client.query(query).to_dataframe()
        return result['plans_with_geo_data'].iloc[0] > 0
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Find best energy plans")
    parser.add_argument("--kwh", type=float, default=6000, help="Annual kWh usage")
    parser.add_argument("--postcode", type=str, default="2000", help="Postcode")
    parser.add_argument("--fuel", type=str, default="ELECTRICITY", choices=["ELECTRICITY", "GAS", "DUAL"])
    parser.add_argument("--customer", type=str, default="RESIDENTIAL", choices=["RESIDENTIAL", "BUSINESS"])
    
    args = parser.parse_args()
    
    print(f"🔍 Finding best plans for {args.kwh} kWh/year in postcode {args.postcode}")
    print(f"📋 Fuel: {args.fuel}, Customer: {args.customer}")
    
    # Show summary
    print("\n📊 Plan Summary:")
    try:
        summary = get_plan_summary()
        if not summary.empty:
            for _, row in summary.head(10).iterrows():
                print(f"  {row['retailer']}: {row['plan_count']} {row['fuel_type']} {row['plan_type']} plans")
        else:
            print("  No plans found in database")
            return
    except Exception as e:
        print(f"  Error getting summary: {e}")
        return
    
    # Check postcode
    print(f"\n🗺️  Checking postcode {args.postcode}...")
    has_geo_data = check_postcode_availability(args.postcode)
    if has_geo_data:
        print(f"  ✅ Found some plans with geographic data for {args.postcode}")
    else:
        print(f"  ⚠️  No specific geographic data found for {args.postcode} (using all available plans)")
    
    # Find best plans
    print(f"\n🏆 Best plans for {args.kwh} kWh/year:")
    try:
        best_plans = find_plans_for_usage(args.kwh, args.postcode, args.fuel, args.customer)
        
        if not best_plans.empty:
            for idx, plan in best_plans.head(10).iterrows():
                print(f"\n  {idx+1}. {plan['brand']}: {plan['plan_name']}")
                print(f"     💰 ${plan['estimated_annual_cost']:.2f}/year (${plan['estimated_monthly_cost']:.2f}/month)")
                print(f"     🏷️  {plan['plan_type']} plan from {plan['retailer']}")
                if plan['application_url']:
                    print(f"     🔗 {plan['application_url']}")
        else:
            print("  No plans found matching your criteria")
            
    except Exception as e:
        print(f"  ❌ Error finding plans: {e}")
    
    print(f"\n💡 Note: These are basic estimates. For accurate pricing, we need to extract detailed tariff data.")

if __name__ == "__main__":
    main()