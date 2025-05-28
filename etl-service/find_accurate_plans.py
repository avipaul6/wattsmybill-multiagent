#!/usr/bin/env python3
"""
Find best energy plans using detailed tariff data
Usage: python find_accurate_plans.py --kwh 8000 --postcode 4207
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

def check_detailed_data_availability():
    """Check if detailed tariff data is available"""
    client = bigquery.Client(project=PROJECT_ID)
    
    try:
        # Check tariff rates
        rates_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates`"
        rates_count = client.query(rates_query).to_dataframe()['count'].iloc[0]
        
        # Check geography
        geo_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography`"
        geo_count = client.query(geo_query).to_dataframe()['count'].iloc[0]
        
        return rates_count, geo_count
    except:
        return 0, 0

def find_plans_with_accurate_pricing(annual_kwh, postcode, fuel_type="ELECTRICITY", customer_type="RESIDENTIAL"):
    """Find plans using detailed tariff data"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Check if postcode is available for plans
    postcode_filter = ""
    if postcode:
        postcode_filter = f"""
        AND p.plan_id IN (
            SELECT DISTINCT plan_id 
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography` 
            WHERE postcode = '{postcode}' AND included = true
        )
        AND p.plan_id NOT IN (
            SELECT DISTINCT plan_id 
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography` 
            WHERE postcode = '{postcode}' AND included = false
        )
        """
    
    query = f"""
    WITH plan_calculations AS (
        SELECT 
            p.plan_id,
            p.plan_name,
            p.brand,
            p.retailer,
            p.plan_type,
            p.application_url,
            
            -- Calculate daily supply charge (annual)
            COALESCE(
                (SELECT SUM(unit_price * 365) 
                 FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates` r 
                 WHERE r.plan_id = p.plan_id AND r.rate_type = 'DAILY_SUPPLY'), 
                365 * 1.20  -- Default if no data
            ) AS annual_supply_cost,
            
            -- Calculate usage charges
            COALESCE(
                (SELECT AVG(unit_price) * {annual_kwh}
                 FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates` r 
                 WHERE r.plan_id = p.plan_id AND r.rate_type = 'USAGE'), 
                {annual_kwh} * 0.28  -- Default if no data
            ) AS annual_usage_cost,
            
            -- Check if we have detailed data for this plan
            CASE WHEN EXISTS (
                SELECT 1 FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates` r 
                WHERE r.plan_id = p.plan_id
            ) THEN 'DETAILED' ELSE 'ESTIMATED' END AS calculation_type
            
        FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple` p
        WHERE 
            p.fuel_type = '{fuel_type}'
            AND p.customer_type = '{customer_type}'
            AND (p.effective_to IS NULL OR p.effective_to > CURRENT_TIMESTAMP())
            AND p.effective_from <= CURRENT_TIMESTAMP()
            AND p.plan_name IS NOT NULL
            {postcode_filter}
    )
    
    SELECT 
        *,
        (annual_supply_cost + annual_usage_cost) AS total_annual_cost,
        (annual_supply_cost + annual_usage_cost) / 12 AS total_monthly_cost
    FROM plan_calculations
    WHERE (annual_supply_cost + annual_usage_cost) > 0
    ORDER BY 
        calculation_type DESC,  -- Show detailed calculations first
        total_annual_cost ASC
    LIMIT 25
    """
    
    return client.query(query).to_dataframe()

def get_plan_tariff_breakdown(plan_id):
    """Get detailed tariff breakdown for a specific plan"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
        rate_type,
        time_of_use,
        unit_price,
        unit,
        volume_min,
        volume_max,
        start_time,
        end_time,
        days_of_week
    FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates`
    WHERE plan_id = '{plan_id}'
    ORDER BY rate_type, time_of_use
    """
    
    return client.query(query).to_dataframe()

def get_plan_geography(plan_id):
    """Get geographic availability for a plan"""
    client = bigquery.Client(project=PROJECT_ID)
    
    query = f"""
    SELECT 
        postcode,
        included,
        distributor
    FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography`
    WHERE plan_id = '{plan_id}'
    ORDER BY included DESC, postcode
    LIMIT 10
    """
    
    return client.query(query).to_dataframe()

def main():
    parser = argparse.ArgumentParser(description="Find best energy plans with accurate pricing")
    parser.add_argument("--kwh", type=float, default=6000, help="Annual kWh usage")
    parser.add_argument("--postcode", type=str, help="Postcode")
    parser.add_argument("--fuel", type=str, default="ELECTRICITY", choices=["ELECTRICITY", "GAS", "DUAL"])
    parser.add_argument("--customer", type=str, default="RESIDENTIAL", choices=["RESIDENTIAL", "BUSINESS"])
    parser.add_argument("--details", type=str, help="Show tariff breakdown for specific plan_id")
    
    args = parser.parse_args()
    
    # Check detailed data availability
    rates_count, geo_count = check_detailed_data_availability()
    
    print(f"🔍 Finding accurate plans for {args.kwh} kWh/year")
    if args.postcode:
        print(f"📍 Postcode: {args.postcode}")
    print(f"📋 Fuel: {args.fuel}, Customer: {args.customer}")
    print(f"📊 Available detailed data: {rates_count:,} tariff rates, {geo_count:,} geography records")
    
    if args.details:
        # Show details for specific plan
        print(f"\n🔍 Tariff breakdown for plan {args.details}:")
        
        tariff_breakdown = get_plan_tariff_breakdown(args.details)
        if not tariff_breakdown.empty:
            for _, rate in tariff_breakdown.iterrows():
                print(f"  {rate['rate_type']} - {rate['time_of_use']}: ${rate['unit_price']:.4f}/{rate['unit']}")
                if rate['start_time'] and rate['end_time']:
                    print(f"    Time: {rate['start_time']} - {rate['end_time']}")
                if rate['volume_min']:
                    print(f"    Volume: {rate['volume_min']:,}+ {rate['unit']}")
        else:
            print("  No detailed tariff data found for this plan")
        
        geography = get_plan_geography(args.details)
        if not geography.empty:
            print(f"\n  📍 Geographic availability:")
            included = geography[geography['included'] == True]
            excluded = geography[geography['included'] == False]
            if not included.empty:
                print(f"    Included: {', '.join(included['postcode'].head(5))}...")
            if not excluded.empty:
                print(f"    Excluded: {', '.join(excluded['postcode'].head(5))}...")
        
        return
    
    # Find best plans
    print(f"\n🏆 Best plans for {args.kwh} kWh/year:")
    
    try:
        best_plans = find_plans_with_accurate_pricing(args.kwh, args.postcode, args.fuel, args.customer)
        
        if not best_plans.empty:
            for idx, plan in best_plans.head(15).iterrows():
                calculation_emoji = "🎯" if plan['calculation_type'] == 'DETAILED' else "📊"
                
                print(f"\n  {idx+1}. {calculation_emoji} {plan['brand']}: {plan['plan_name']}")
                print(f"     💰 ${plan['total_annual_cost']:.2f}/year (${plan['total_monthly_cost']:.2f}/month)")
                print(f"     🏷️  {plan['plan_type']} plan from {plan['retailer']}")
                print(f"     📈 Supply: ${plan['annual_supply_cost']:.2f}/year, Usage: ${plan['annual_usage_cost']:.2f}/year")
                print(f"     📊 Calculation: {plan['calculation_type']}")
                
                if plan['application_url']:
                    print(f"     🔗 {plan['application_url']}")
                
                # Show option to get details
                if plan['calculation_type'] == 'DETAILED':
                    print(f"     💡 Run with --details {plan['plan_id']} for tariff breakdown")
        else:
            print("  No plans found matching your criteria")
            
    except Exception as e:
        print(f"  ❌ Error finding plans: {e}")
    
    if rates_count == 0:
        print(f"\n💡 To get accurate pricing, extract detailed tariff data with:")
        print(f"   python extract_tariffs.py --sample 100")

if __name__ == "__main__":
    main()