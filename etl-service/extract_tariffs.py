#!/usr/bin/env python3
"""
Extract detailed tariff information for energy plans
Usage: python extract_tariffs.py --sample 50  # Extract details for 50 plans
Usage: python extract_tariffs.py --retailer agl  # Extract details for all AGL plans
"""

import argparse
import requests
import json
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

def create_tariff_tables():
    """Create tables for detailed tariff data"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Tariff rates table
    rates_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("rate_type", "STRING"),  # DAILY_SUPPLY, USAGE, DEMAND
        bigquery.SchemaField("time_of_use", "STRING"),  # ALL_DAY, PEAK, OFF_PEAK, SHOULDER
        bigquery.SchemaField("unit_price", "FLOAT"),
        bigquery.SchemaField("unit", "STRING"),  # KWH, KW, DAYS
        bigquery.SchemaField("volume_min", "FLOAT"),  # For stepped rates
        bigquery.SchemaField("volume_max", "FLOAT"),
        bigquery.SchemaField("period", "STRING"),  # P1Y, P1M, etc
        bigquery.SchemaField("start_time", "STRING"),  # For time-of-use
        bigquery.SchemaField("end_time", "STRING"),
        bigquery.SchemaField("days_of_week", "STRING"),  # JSON array
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    try:
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.tariff_rates"
        client.get_table(table_ref)
        logger.info("Tariff rates table already exists")
    except:
        table = bigquery.Table(table_ref, schema=rates_schema)
        client.create_table(table)
        logger.info("Created tariff rates table")
    
    # Plan geography table
    geo_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("postcode", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("included", "BOOLEAN"),  # True=included, False=excluded
        bigquery.SchemaField("distributor", "STRING"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    try:
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.plan_geography"
        client.get_table(table_ref)
        logger.info("Plan geography table already exists")
    except:
        table = bigquery.Table(table_ref, schema=geo_schema)
        client.create_table(table)
        logger.info("Created plan geography table")

def get_plans_to_extract(sample_size=None, retailer=None):
    """Get list of plans to extract detailed data for"""
    client = bigquery.Client(project=PROJECT_ID)
    
    where_clause = "WHERE 1=1"
    if retailer:
        where_clause += f" AND retailer = '{retailer}'"
    
    query = f"""
    SELECT DISTINCT plan_id, retailer
    FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
    {where_clause}
    AND (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
    ORDER BY retailer, plan_id
    """
    
    if sample_size:
        query += f" LIMIT {sample_size}"
    
    result = client.query(query).to_dataframe()
    return list(zip(result['plan_id'], result['retailer']))

def fetch_plan_detail(plan_id, retailer):
    """Fetch detailed plan information from AER API"""
    url = f"https://cdr.energymadeeasy.gov.au/{retailer}/cds-au/v1/energy/plans/{plan_id}"
    headers = {
        "x-v": "3",  # Use version 3 for plan details (found by debug script)
        "Accept": "application/json",
        "User-Agent": "TariffExtractor/1.0"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json().get("data", {})
        else:
            logger.warning(f"Failed to fetch {plan_id} from {retailer}: {response.status_code}")
            if response.status_code == 406:
                logger.warning(f"  Response: {response.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"Error fetching {plan_id}: {e}")
        return None

def extract_tariff_rates(plan_detail):
    """Extract tariff rates from plan detail"""
    plan_id = plan_detail.get("planId")
    rates = []
    
    logger.debug(f"Extracting rates for {plan_id}, available contracts: {[k for k in plan_detail.keys() if 'Contract' in k]}")
    
    # Extract electricity contract tariffs
    elec_contract = plan_detail.get("electricityContract", {})
    if elec_contract:
        logger.debug(f"Processing electricity contract for {plan_id}")
        rates.extend(extract_contract_rates(plan_id, elec_contract, "ELECTRICITY"))
    
    # Extract gas contract tariffs  
    gas_contract = plan_detail.get("gasContract", {})
    if gas_contract:
        logger.debug(f"Processing gas contract for {plan_id}")
        rates.extend(extract_contract_rates(plan_id, gas_contract, "GAS"))
    
    if not elec_contract and not gas_contract:
        logger.warning(f"No contract data found for {plan_id}")
    
    return rates

def extract_contract_rates(plan_id, contract, fuel_type):
    """Extract rates from a contract (electricity or gas)"""
    rates = []
    
    for period in contract.get("tariffPeriod", []):
        # Daily supply charge
        if period.get("dailySupplyCharge"):
            rates.append({
                "plan_id": plan_id,
                "rate_type": "DAILY_SUPPLY",
                "time_of_use": "ALL_DAY",
                "unit_price": float(period["dailySupplyCharge"]),
                "unit": "DAYS",
                "extracted_at": datetime.utcnow()
            })
        
        # Single rate
        if period.get("singleRate"):
            single_rate = period["singleRate"]
            for rate in single_rate.get("rates", []):
                rates.append({
                    "plan_id": plan_id,
                    "rate_type": "USAGE",
                    "time_of_use": "ALL_DAY",
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH" if fuel_type == "ELECTRICITY" else "MJ"),
                    "volume_min": rate.get("volume"),
                    "period": single_rate.get("period"),
                    "extracted_at": datetime.utcnow()
                })
        
        # Time of use rates
        for tou in period.get("timeOfUseRates", []):
            for rate in tou.get("rates", []):
                rates.append({
                    "plan_id": plan_id,
                    "rate_type": "USAGE",
                    "time_of_use": tou.get("type", "UNKNOWN"),
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH" if fuel_type == "ELECTRICITY" else "MJ"),
                    "volume_min": rate.get("volume"),
                    "period": tou.get("period"),
                    "start_time": tou.get("timeOfUse", [{}])[0].get("startTime") if tou.get("timeOfUse") else None,
                    "end_time": tou.get("timeOfUse", [{}])[0].get("endTime") if tou.get("timeOfUse") else None,
                    "days_of_week": json.dumps(tou.get("timeOfUse", [{}])[0].get("daysOfWeek", [])) if tou.get("timeOfUse") else None,
                    "extracted_at": datetime.utcnow()
                })
        
        # Demand charges (electricity only)
        if fuel_type == "ELECTRICITY":
            for demand in period.get("demandCharges", []):
                for rate in demand.get("rates", []):
                    rates.append({
                        "plan_id": plan_id,
                        "rate_type": "DEMAND",
                        "time_of_use": demand.get("timeOfUse", {}).get("type", "ALL_DAY"),
                        "unit_price": float(rate["unitPrice"]),
                        "unit": rate.get("measureUnit", "KW"),
                        "extracted_at": datetime.utcnow()
                    })
    
    return rates

def extract_geography(plan_detail):
    """Extract geographic availability from plan detail"""
    plan_id = plan_detail.get("planId")
    geography = []
    
    geo_data = plan_detail.get("geography", {})
    
    # Distributors
    distributors = geo_data.get("distributors", [])
    
    # Included postcodes
    for postcode in geo_data.get("includedPostcodes", []):
        geography.append({
            "plan_id": plan_id,
            "postcode": postcode,
            "included": True,
            "distributor": distributors[0] if distributors else None,
            "extracted_at": datetime.utcnow()
        })
    
    # Excluded postcodes
    for postcode in geo_data.get("excludedPostcodes", []):
        geography.append({
            "plan_id": plan_id,
            "postcode": postcode,
            "included": False,
            "distributor": distributors[0] if distributors else None,
            "extracted_at": datetime.utcnow()
        })
    
    return geography

def process_plan_batch(plan_batch):
    """Process a batch of plans to extract detailed data"""
    all_rates = []
    all_geography = []
    
    for plan_id, retailer in plan_batch:
        logger.info(f"Processing {plan_id} from {retailer}")
        
        # Fetch detailed plan data
        plan_detail = fetch_plan_detail(plan_id, retailer)
        if not plan_detail:
            continue
        
        # Extract tariff rates
        rates = extract_tariff_rates(plan_detail)
        all_rates.extend(rates)
        
        # Extract geography
        geography = extract_geography(plan_detail)
        all_geography.extend(geography)
        
        # Rate limiting
        time.sleep(0.5)
    
    return all_rates, all_geography

def load_to_bigquery(rates, geography):
    """Load extracted data to BigQuery"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Load tariff rates
    if rates:
        df_rates = pd.DataFrame(rates)
        df_rates = df_rates.where(pd.notnull(df_rates), None)
        
        rates_table = f"{PROJECT_ID}.{DATASET_ID}.tariff_rates"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        
        job = client.load_table_from_dataframe(df_rates, rates_table, job_config=job_config)
        job.result()
        logger.info(f"Loaded {len(rates)} tariff rates")
    
    # Load geography
    if geography:
        df_geo = pd.DataFrame(geography)
        df_geo = df_geo.where(pd.notnull(df_geo), None)
        
        geo_table = f"{PROJECT_ID}.{DATASET_ID}.plan_geography"
        job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
        
        job = client.load_table_from_dataframe(df_geo, geo_table, job_config=job_config)
        job.result()
        logger.info(f"Loaded {len(geography)} geography records")

def main():
    parser = argparse.ArgumentParser(description="Extract detailed tariff data")
    parser.add_argument("--sample", type=int, help="Extract details for N sample plans")
    parser.add_argument("--retailer", type=str, help="Extract details for specific retailer")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for processing")
    
    args = parser.parse_args()
    
    logger.info("Starting detailed tariff extraction...")
    
    # Create tables
    create_tariff_tables()
    
    # Get plans to process
    plans_to_process = get_plans_to_extract(args.sample, args.retailer)
    
    if not plans_to_process:
        logger.error("No plans found to process")
        return
    
    logger.info(f"Found {len(plans_to_process)} plans to process")
    
    if not args.sample and not args.retailer and len(plans_to_process) > 100:
        response = input(f"This will process {len(plans_to_process)} plans. Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Extraction cancelled")
            return
    
    # Process in batches
    all_rates = []
    all_geography = []
    
    for i in range(0, len(plans_to_process), args.batch_size):
        batch = plans_to_process[i:i + args.batch_size]
        logger.info(f"Processing batch {i//args.batch_size + 1}/{(len(plans_to_process) + args.batch_size - 1)//args.batch_size}")
        
        batch_rates, batch_geography = process_plan_batch(batch)
        all_rates.extend(batch_rates)
        all_geography.extend(batch_geography)
        
        # Load batch to BigQuery
        if batch_rates or batch_geography:
            load_to_bigquery(batch_rates, batch_geography)
        
        logger.info(f"Batch complete: {len(batch_rates)} rates, {len(batch_geography)} geography records")
    
    logger.info(f"Extraction complete! Total: {len(all_rates)} rates, {len(all_geography)} geography records")

if __name__ == "__main__":
    main()