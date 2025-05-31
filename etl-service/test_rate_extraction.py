#!/usr/bin/env python3
"""
Test script to debug rate extraction from existing data
"""

import json
import os
from google.cloud import bigquery
from datetime import datetime

PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'wattsmybill-dev')
DATASET_ID = 'energy_plans'

def extract_rates_from_raw_data(raw_contract_data: str, plan_id: str, fuel_type: str):
    """Test the rate extraction logic on raw data"""
    try:
        contract = json.loads(raw_contract_data)
        rates = []
        
        print(f"\n=== Testing {plan_id} ({fuel_type}) ===")
        print(f"Available top-level keys: {list(contract.keys())}")
        
        # CHECK BOTH STRUCTURES
        # 1. Check if electricityContract exists (nested structure)
        elec_contract = contract.get("electricityContract", {})
        gas_contract = contract.get("gasContract", {})
        
        if elec_contract:
            print(f"Found electricityContract with keys: {list(elec_contract.keys())}")
            contract_to_parse = elec_contract
        elif gas_contract:
            print(f"Found gasContract with keys: {list(gas_contract.keys())}")
            contract_to_parse = gas_contract
        else:
            print("No electricityContract or gasContract found, using root level")
            contract_to_parse = contract
        
        # Check for tariffPeriod in the contract
        tariff_periods = contract_to_parse.get("tariffPeriod", [])
        print(f"Found {len(tariff_periods)} tariff periods in contract")
        
        for i, period in enumerate(tariff_periods):
            print(f"\nPeriod {i+1}:")
            print(f"  Keys: {list(period.keys())}")
            
            # Daily supply charge
            if period.get("dailySupplyCharge"):
                supply_charge = period["dailySupplyCharge"]
                print(f"  Daily supply charge: ${supply_charge}")
                rates.append({
                    "type": "DAILY_SUPPLY",
                    "price": float(supply_charge),
                    "unit": "DAYS"
                })
            
            # Single rate
            if period.get("singleRate"):
                single_rate = period["singleRate"]
                print(f"  Single rate keys: {list(single_rate.keys())}")
                
                for rate in single_rate.get("rates", []):
                    unit_price = rate.get("unitPrice")
                    print(f"  Usage rate: ${unit_price}/kWh")
                    rates.append({
                        "type": "USAGE",
                        "price": float(unit_price),
                        "unit": "KWH"
                    })
            
            # Demand charges
            for demand in period.get("demandCharges", []):
                amount = demand.get("amount")
                print(f"  Demand charge: ${amount}/kW")
                rates.append({
                    "type": "DEMAND", 
                    "price": float(amount),
                    "unit": "KW"
                })
        
        # Solar feed-in tariffs (check in contract)
        solar_fits = contract_to_parse.get("solarFeedInTariff", [])
        print(f"\nFound {len(solar_fits)} solar feed-in tariffs")
        for fit in solar_fits:
            if fit.get("singleTariff"):
                for rate in fit["singleTariff"].get("rates", []):
                    unit_price = rate.get("unitPrice")
                    print(f"  Solar FIT: ${unit_price}/kWh")
                    rates.append({
                        "type": "SOLAR_FIT",
                        "price": float(unit_price),
                        "unit": "KWH"
                    })
        
        # Green power (check in contract)
        green_power = contract_to_parse.get("greenPowerCharges", [])
        print(f"Found {len(green_power)} green power options")
        
        # Fees (check in contract)
        fees = contract_to_parse.get("fees", [])
        print(f"Found {len(fees)} fees")
        
        print(f"\nTotal extractable rates: {len(rates)}")
        return rates
        
    except Exception as e:
        print(f"Error processing {plan_id}: {e}")
        return []

def test_existing_data():
    """Test rate extraction on existing contract data"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Get some recent plans with raw data
    query = f"""
    SELECT plan_id, retailer, fuel_type, raw_contract_data
    FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
    WHERE raw_contract_data IS NOT NULL
    ORDER BY extracted_at DESC
    LIMIT 3
    """
    
    result = client.query(query).to_dataframe()
    
    total_rates = 0
    for _, row in result.iterrows():
        rates = extract_rates_from_raw_data(
            row['raw_contract_data'], 
            row['plan_id'], 
            row['fuel_type']
        )
        total_rates += len(rates)
    
    print(f"\n=== SUMMARY ===")
    print(f"Plans tested: {len(result)}")
    print(f"Total rates extracted: {total_rates}")
    print(f"Average rates per plan: {total_rates/len(result) if len(result) > 0 else 0:.1f}")
    
    if total_rates == 0:
        print("\n❌ NO RATES EXTRACTED - This explains why tariff_rates_comprehensive is empty!")
        print("The raw contract data structure might be different than expected.")
    else:
        print(f"\n✅ Rate extraction logic works! Should have {total_rates} rates from {len(result)} plans.")

if __name__ == "__main__":
    test_existing_data()