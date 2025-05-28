#!/usr/bin/env python3
"""
Simple script to extract energy plans from AER API and load into BigQuery
Usage: python extract_plans.py
"""

import requests
import json
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = 'wattsmybill-dev'
DATASET_ID = 'energy_plans'
TABLE_ID = 'plans_simple'

# Major retailers to start with
RETAILERS = [
    "agl", "origin", "energyaustralia", "alinta", "red-energy", 
    "lumo", "momentum", "powershop", "diamond", "dodo"
]

def create_simple_table():
    """Create a simple table for energy plans"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create dataset if it doesn't exist
    dataset_ref = client.dataset(DATASET_ID)
    try:
        client.get_dataset(dataset_ref)
        logger.info(f"Dataset {DATASET_ID} already exists")
    except:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        logger.info(f"Created dataset {DATASET_ID}")
    
    # Create simple table
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("retailer", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("plan_name", "STRING"),
        bigquery.SchemaField("brand", "STRING"),
        bigquery.SchemaField("plan_type", "STRING"),  # MARKET, STANDING
        bigquery.SchemaField("fuel_type", "STRING"),  # ELECTRICITY, GAS
        bigquery.SchemaField("customer_type", "STRING"),  # RESIDENTIAL, BUSINESS
        bigquery.SchemaField("effective_from", "TIMESTAMP"),
        bigquery.SchemaField("effective_to", "TIMESTAMP"),
        bigquery.SchemaField("last_updated", "TIMESTAMP"),
        bigquery.SchemaField("application_url", "STRING"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP"),
        bigquery.SchemaField("raw_data", "STRING")  # Store the full JSON
    ]
    
    try:
        client.get_table(table_ref)
        logger.info(f"Table {TABLE_ID} already exists")
    except:
        table = bigquery.Table(table_ref, schema=schema)
        table = client.create_table(table)
        logger.info(f"Created table {TABLE_ID}")

def fetch_plans_from_retailer(retailer):
    """Fetch plans from a single retailer"""
    logger.info(f"Fetching plans from {retailer}...")
    
    url = f"https://cdr.energymadeeasy.gov.au/{retailer}/cds-au/v1/energy/plans"
    headers = {
        "x-v": "1",
        "Accept": "application/json",
        "User-Agent": "EnergyPlanExtractor/1.0"
    }
    params = {
        "type": "ALL",
        "fuelType": "ALL",
        "effective": "CURRENT",
        "page-size": "100"
    }
    
    all_plans = []
    page = 1
    
    while True:
        params["page"] = page
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                plans = data.get("data", {}).get("plans", [])
                
                if not plans:
                    break
                
                # Transform plans to simple format
                for plan in plans:
                    simple_plan = {
                        "plan_id": plan.get("planId"),
                        "retailer": retailer,
                        "plan_name": plan.get("displayName"),
                        "brand": plan.get("brandName"),
                        "plan_type": plan.get("type"),
                        "fuel_type": plan.get("fuelType"),
                        "customer_type": plan.get("customerType"),
                        "application_url": plan.get("applicationUri"),
                        "extracted_at": datetime.utcnow(),
                        "raw_data": json.dumps(plan)
                    }
                    
                    # Handle dates
                    for date_field, simple_field in [
                        ("effectiveFrom", "effective_from"),
                        ("effectiveTo", "effective_to"),
                        ("lastUpdated", "last_updated")
                    ]:
                        if plan.get(date_field):
                            try:
                                simple_plan[simple_field] = datetime.fromisoformat(
                                    plan[date_field].replace('Z', '+00:00')
                                )
                            except:
                                simple_plan[simple_field] = None
                    
                    all_plans.append(simple_plan)
                
                logger.info(f"Fetched page {page} from {retailer}: {len(plans)} plans")
                
                # Check if more pages
                meta = data.get("meta", {})
                if page >= meta.get("totalPages", 1):
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting
                
            else:
                logger.error(f"Failed to fetch from {retailer}: {response.status_code}")
                break
                
        except Exception as e:
            logger.error(f"Error fetching from {retailer}: {e}")
            break
    
    logger.info(f"Total plans from {retailer}: {len(all_plans)}")
    return all_plans

def load_plans_to_bigquery(all_plans):
    """Load plans to BigQuery"""
    if not all_plans:
        logger.warning("No plans to load")
        return
    
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Convert to DataFrame
    df = pd.DataFrame(all_plans)
    
    # Clean up None values
    df = df.where(pd.notnull(df), None)
    
    # Load to BigQuery
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    
    logger.info(f"Loading {len(all_plans)} plans to BigQuery...")
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Wait for completion
    
    logger.info(f"Successfully loaded {len(all_plans)} plans to BigQuery")
    
    # Verify
    query = f"SELECT COUNT(*) as total FROM `{table_ref}`"
    result = client.query(query).to_dataframe()
    logger.info(f"BigQuery table now contains {result['total'].iloc[0]} plans")

def main():
    """Main extraction process"""
    logger.info("Starting energy plans extraction...")
    
    # Create table
    create_simple_table()
    
    # Extract from all retailers
    all_plans = []
    for retailer in RETAILERS:
        plans = fetch_plans_from_retailer(retailer)
        all_plans.extend(plans)
    
    logger.info(f"Total plans extracted: {len(all_plans)}")
    
    # Load to BigQuery
    load_plans_to_bigquery(all_plans)
    
    logger.info("Extraction complete!")

if __name__ == "__main__":
    main()