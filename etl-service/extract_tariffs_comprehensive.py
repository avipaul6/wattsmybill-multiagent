#!/usr/bin/env python3
"""
Enhanced extract_tariffs_comprehensive.py - FIXED VERSION
Captures the full CDR Energy API schema including contracts, discounts, fees, etc.
Fixed for Australian CDR API structure (root-level data, no electricityContract wrapper)
"""

import argparse
import requests
import json
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
import logging
import time
import os
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

def create_comprehensive_tables():
    """Create comprehensive tables for all tariff data structures"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Table schemas and creation logic
    tables_to_create = [
        ("plan_contract_details", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("retailer", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING"),
            bigquery.SchemaField("pricing_model", "STRING"),
            bigquery.SchemaField("is_fixed", "BOOLEAN"),
            bigquery.SchemaField("term_type", "STRING"),
            bigquery.SchemaField("cooling_off_days", "INTEGER"),
            bigquery.SchemaField("payment_options", "STRING"),
            bigquery.SchemaField("meter_types", "STRING"),
            bigquery.SchemaField("bill_frequency", "STRING"),
            bigquery.SchemaField("time_zone", "STRING"),
            bigquery.SchemaField("variation", "STRING"),
            bigquery.SchemaField("on_expiry_description", "STRING"),
            bigquery.SchemaField("benefit_period", "STRING"),
            bigquery.SchemaField("terms", "STRING"),
            bigquery.SchemaField("additional_fee_information", "STRING"),
            bigquery.SchemaField("intrinsic_green_power_percentage", "FLOAT"),
            bigquery.SchemaField("raw_contract_data", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP"),
            bigquery.SchemaField("extraction_run_id", "STRING")
        ]),
        ("tariff_rates_comprehensive", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("tariff_period_type", "STRING"),
            bigquery.SchemaField("tariff_period_name", "STRING"),
            bigquery.SchemaField("start_date", "DATE"),
            bigquery.SchemaField("end_date", "DATE"),
            bigquery.SchemaField("rate_structure", "STRING"),
            bigquery.SchemaField("rate_type", "STRING"),
            bigquery.SchemaField("time_of_use_type", "STRING"),
            bigquery.SchemaField("unit_price", "FLOAT"),
            bigquery.SchemaField("unit", "STRING"),
            bigquery.SchemaField("volume_min", "FLOAT"),
            bigquery.SchemaField("volume_max", "FLOAT"),
            bigquery.SchemaField("period", "STRING"),
            bigquery.SchemaField("start_time", "STRING"),
            bigquery.SchemaField("end_time", "STRING"),
            bigquery.SchemaField("days_of_week", "STRING"),
            bigquery.SchemaField("daily_supply_charge_type", "STRING"),
            bigquery.SchemaField("general_unit_price", "FLOAT"),
            bigquery.SchemaField("measurement_period", "STRING"),
            bigquery.SchemaField("charge_period", "STRING"),
            bigquery.SchemaField("min_demand", "FLOAT"),
            bigquery.SchemaField("max_demand", "FLOAT"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("plan_discounts", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("display_name", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("discount_type", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("end_date", "DATE"),
            bigquery.SchemaField("method_type", "STRING"),
            bigquery.SchemaField("rate", "FLOAT"),
            bigquery.SchemaField("amount", "FLOAT"),
            bigquery.SchemaField("usage_amount", "FLOAT"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("plan_fees", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fee_type", "STRING"),
            bigquery.SchemaField("term", "STRING"),
            bigquery.SchemaField("amount", "FLOAT"),
            bigquery.SchemaField("rate", "FLOAT"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("plan_incentives", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("display_name", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("category", "STRING"),
            bigquery.SchemaField("eligibility", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("solar_feed_in_tariffs", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("display_name", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("start_date", "DATE"),
            bigquery.SchemaField("end_date", "DATE"),
            bigquery.SchemaField("scheme", "STRING"),
            bigquery.SchemaField("payer_type", "STRING"),
            bigquery.SchemaField("tariff_type", "STRING"),
            bigquery.SchemaField("time_of_use_type", "STRING"),
            bigquery.SchemaField("unit_price", "FLOAT"),
            bigquery.SchemaField("unit", "STRING"),
            bigquery.SchemaField("volume", "FLOAT"),
            bigquery.SchemaField("period", "STRING"),
            bigquery.SchemaField("start_time", "STRING"),
            bigquery.SchemaField("end_time", "STRING"),
            bigquery.SchemaField("days_of_week", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("controlled_load_tariffs", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("display_name", "STRING"),
            bigquery.SchemaField("start_date", "DATE"),
            bigquery.SchemaField("end_date", "DATE"),
            bigquery.SchemaField("rate_structure", "STRING"),
            bigquery.SchemaField("daily_supply_charge", "FLOAT"),
            bigquery.SchemaField("time_of_use_type", "STRING"),
            bigquery.SchemaField("unit_price", "FLOAT"),
            bigquery.SchemaField("unit", "STRING"),
            bigquery.SchemaField("volume", "FLOAT"),
            bigquery.SchemaField("period", "STRING"),
            bigquery.SchemaField("start_time", "STRING"),
            bigquery.SchemaField("end_time", "STRING"),
            bigquery.SchemaField("days_of_week", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("green_power_charges", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("display_name", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("scheme", "STRING"),
            bigquery.SchemaField("charge_type", "STRING"),
            bigquery.SchemaField("percent_green", "FLOAT"),
            bigquery.SchemaField("rate", "FLOAT"),
            bigquery.SchemaField("amount", "FLOAT"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("plan_eligibility", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("eligibility_type", "STRING"),
            bigquery.SchemaField("information", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ]),
        ("metering_charges", [
            bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("display_name", "STRING"),
            bigquery.SchemaField("description", "STRING"),
            bigquery.SchemaField("minimum_value", "FLOAT"),
            bigquery.SchemaField("maximum_value", "FLOAT"),
            bigquery.SchemaField("period", "STRING"),
            bigquery.SchemaField("extracted_at", "TIMESTAMP")
        ])
    ]
    
    for table_name, schema in tables_to_create:
        try:
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
            client.get_table(table_ref)
            logger.info(f"Table {table_name} already exists")
        except:
            table = bigquery.Table(table_ref, schema=schema)
            if table_name == "plan_contract_details":
                table.time_partitioning = bigquery.TimePartitioning(
                    type_=bigquery.TimePartitioningType.DAY,
                    field="extracted_at"
                )
                table.clustering_fields = ["retailer", "fuel_type"]
            client.create_table(table)
            logger.info(f"Created table {table_name}")

def get_plans_to_extract(sample_size=None, retailer=None, fuel_type=None):
    """Get list of plans to extract detailed data for"""
    client = bigquery.Client(project=PROJECT_ID)
    
    where_conditions = [
        "(effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())"
    ]
    
    if retailer:
        where_conditions.append(f"retailer = '{retailer}'")
    if fuel_type:
        where_conditions.append(f"fuel_type = '{fuel_type}'")
    
    where_clause = "WHERE " + " AND ".join(where_conditions)
    
    query = f"""
    SELECT DISTINCT plan_id, retailer, fuel_type
    FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
    {where_clause}
    ORDER BY retailer, fuel_type, plan_id
    """
    
    if sample_size:
        query += f" LIMIT {sample_size}"
    
    result = client.query(query).to_dataframe()
    return list(zip(result['plan_id'], result['retailer'], result['fuel_type']))

def fetch_plan_detail(plan_id: str, retailer: str) -> Optional[Dict]:
    """Fetch detailed plan information from CDR API"""
    url = f"https://cdr.energymadeeasy.gov.au/{retailer}/cds-au/v1/energy/plans/{plan_id}"
    headers = {
        "x-v": "3",
        "Accept": "application/json",
        "User-Agent": "ComprehensiveTariffExtractor/2.0"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json().get("data", {})
        else:
            logger.warning(f"Failed to fetch {plan_id} from {retailer}: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching {plan_id}: {e}")
        return None

def extract_plan_contract_details(plan_detail: Dict, fuel_type: str) -> Dict:
    """Extract main contract details - FIXED for Australian CDR API"""
    plan_id = plan_detail.get("planId")
    
    # FIXED: Get the correct contract based on fuel type
    if fuel_type == "ELECTRICITY":
        contract = plan_detail.get("electricityContract", {})
    elif fuel_type == "GAS":
        contract = plan_detail.get("gasContract", {})
    else:
        # For DUAL fuel, try electricity first, then gas, then root level
        contract = plan_detail.get("electricityContract") or plan_detail.get("gasContract") or plan_detail
    
    # If no contract found, fallback to root level
    if not contract:
        contract = plan_detail
    
    # Extract intrinsic green power
    green_power_pct = None
    if "intrinsicGreenPower" in contract:
        green_power_pct = float(contract["intrinsicGreenPower"].get("greenPercentage", 0))
    
    return {
        "plan_id": plan_id,
        "retailer": plan_detail.get("brand", ""),
        "fuel_type": fuel_type,
        "pricing_model": contract.get("pricingModel"),
        "is_fixed": contract.get("isFixed"),
        "term_type": contract.get("termType"),
        "cooling_off_days": contract.get("coolingOffDays"),
        "payment_options": json.dumps(contract.get("paymentOption", [])),
        "meter_types": json.dumps(contract.get("meterTypes", [])),
        "bill_frequency": json.dumps(contract.get("billFrequency", [])),
        "time_zone": contract.get("timeZone"),
        "variation": contract.get("variation"),
        "on_expiry_description": contract.get("onExpiryDescription"),
        "benefit_period": contract.get("benefitPeriod"),
        "terms": contract.get("terms"),
        "additional_fee_information": contract.get("additionalFeeInformation"),
        "intrinsic_green_power_percentage": green_power_pct,
        "raw_contract_data": json.dumps(contract),
        "extracted_at": datetime.utcnow()
    }


# Add this helper function at the top of your file
def safe_date_parse(date_str):
    """Safely parse date string to proper format for BigQuery"""
    if not date_str:
        return None
    try:
        # If it's already a datetime object, convert to date
        if isinstance(date_str, datetime):
            return date_str.date()
        # If it's a string, parse it
        if isinstance(date_str, str):
            # Handle various date formats
            for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%SZ']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
        return None
    except:
        return None

# Then modify the tariff rates extraction to use safe date parsing:
def extract_comprehensive_tariff_rates(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract all tariff rates - FIXED for Australian CDR API structure"""
    plan_id = plan_detail.get("planId")
    rates = []
    
    # Get the correct contract based on fuel type
    if fuel_type == "ELECTRICITY":
        contract = plan_detail.get("electricityContract", {})
    elif fuel_type == "GAS":
        contract = plan_detail.get("gasContract", {})
    else:
        contract = plan_detail.get("electricityContract") or plan_detail.get("gasContract") or plan_detail
    
    if not contract:
        contract = plan_detail
    
    # Process tariff periods from the correct contract location
    for period in contract.get("tariffPeriod", []):
        period_type = period.get("type", "STANDARD")
        period_name = period.get("displayName", "Standard Period")
        start_date = safe_date_parse(period.get("startDate"))  # ✅ Fix date parsing
        end_date = safe_date_parse(period.get("endDate"))      # ✅ Fix date parsing
        
        # Daily supply charges
        if period.get("dailySupplyCharge"):
            rates.append({
                "plan_id": plan_id,
                "fuel_type": fuel_type,
                "tariff_period_type": period_type,
                "tariff_period_name": period_name,
                "start_date": start_date,  # ✅ Now properly formatted
                "end_date": end_date,      # ✅ Now properly formatted
                "rate_structure": "dailySupplyCharge",
                "rate_type": "DAILY_SUPPLY",
                "time_of_use_type": "ALL_DAY",
                "unit_price": float(period["dailySupplyCharge"]),
                "unit": "DAYS",
                "daily_supply_charge_type": period.get("dailySupplyChargeType", "SINGLE"),
                "extracted_at": datetime.utcnow()
            })
        
        # Single rate
        if period.get("singleRate"):
            single_rate = period["singleRate"]
            
            for rate in single_rate.get("rates", []):
                rates.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "tariff_period_type": period_type,
                    "tariff_period_name": period_name,
                    "start_date": start_date,  # ✅ Now properly formatted
                    "end_date": end_date,      # ✅ Now properly formatted
                    "rate_structure": "singleRate",
                    "rate_type": "USAGE",
                    "time_of_use_type": "ALL_DAY",
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH" if fuel_type == "ELECTRICITY" else "MJ"),
                    "volume_min": float(rate["volume"]) if rate.get("volume") else None,  # ✅ Safe float conversion
                    "period": single_rate.get("period"),
                    "extracted_at": datetime.utcnow()
                })
        
        # Time of use rates
        for tou in period.get("timeOfUseRates", []):
            tou_type = tou.get("type")
            
            for rate in tou.get("rates", []):
                time_periods = tou.get("timeOfUse", [])
                start_time = time_periods[0].get("startTime") if time_periods else None
                end_time = time_periods[0].get("endTime") if time_periods else None
                days_of_week = time_periods[0].get("days", []) if time_periods else []
                
                rates.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "tariff_period_type": period_type,
                    "tariff_period_name": period_name,
                    "start_date": start_date,  # ✅ Now properly formatted
                    "end_date": end_date,      # ✅ Now properly formatted
                    "rate_structure": "timeOfUseRates",
                    "rate_type": "USAGE",
                    "time_of_use_type": tou_type,
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH" if fuel_type == "ELECTRICITY" else "MJ"),
                    "volume_min": float(rate["volume"]) if rate.get("volume") else None,  # ✅ Safe float conversion
                    "period": tou.get("period"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "days_of_week": json.dumps(days_of_week),
                    "extracted_at": datetime.utcnow()
                })
        
        # Demand charges (electricity only)
        if fuel_type == "ELECTRICITY":
            for demand in period.get("demandCharges", []):
                rates.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "tariff_period_type": period_type,
                    "tariff_period_name": period_name,
                    "start_date": start_date,  # ✅ Now properly formatted
                    "end_date": end_date,      # ✅ Now properly formatted
                    "rate_structure": "demandCharges",
                    "rate_type": "DEMAND",
                    "unit_price": float(demand.get("amount", 0)),
                    "unit": demand.get("measureUnit", "KW"),
                    "start_time": demand.get("startTime"),
                    "end_time": demand.get("endTime"),
                    "days_of_week": json.dumps(demand.get("days", [])),
                    "min_demand": float(demand.get("minDemand", 0)) if demand.get("minDemand") else None,
                    "max_demand": float(demand.get("maxDemand", 0)) if demand.get("maxDemand") else None,
                    "measurement_period": demand.get("measurementPeriod"),
                    "charge_period": demand.get("chargePeriod"),
                    "extracted_at": datetime.utcnow()
                })
    
    logger.debug(f"Extracted {len(rates)} tariff rates for {plan_id}")
    return rates

def extract_fees(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract all fee information - FIXED for Australian CDR API"""
    plan_id = plan_detail.get("planId")
    fees = []
    
    # FIXED: Get the correct contract based on fuel type
    if fuel_type == "ELECTRICITY":
        contract = plan_detail.get("electricityContract", {})
    elif fuel_type == "GAS":
        contract = plan_detail.get("gasContract", {})
    else:
        contract = plan_detail.get("electricityContract") or plan_detail.get("gasContract") or plan_detail
    
    if not contract:
        contract = plan_detail
    
    # Extract fees from the correct contract location
    for fee in contract.get("fees", []):
        fees.append({
            "plan_id": plan_id,
            "fuel_type": fuel_type,
            "fee_type": fee.get("type"),
            "term": fee.get("term"),
            "amount": float(fee["amount"]) if fee.get("amount") else None,
            "rate": float(fee["rate"]) if fee.get("rate") else None,
            "description": fee.get("description"),
            "extracted_at": datetime.utcnow()
        })
    
    return fees

def extract_solar_feed_in_tariffs(plan_detail: Dict) -> List[Dict]:
    """Extract solar feed-in tariff information - FIXED for Australian CDR API"""
    plan_id = plan_detail.get("planId")
    solar_fits = []
    
    # FIXED: Get from electricityContract, not root level
    contract = plan_detail.get("electricityContract", {})
    if not contract:
        contract = plan_detail  # Fallback to root level
    
    # Extract solar FIT from the correct contract location
    for fit in contract.get("solarFeedInTariff", []):
        # Single tariff
        if fit.get("singleTariff"):
            single_tariff = fit["singleTariff"]
            for rate in single_tariff.get("rates", []):
                solar_fits.append({
                    "plan_id": plan_id,
                    "display_name": fit.get("displayName"),
                    "description": fit.get("description"),
                    "start_date": fit.get("startDate"),
                    "end_date": fit.get("endDate"),
                    "scheme": fit.get("scheme"),
                    "payer_type": fit.get("payerType"),
                    "tariff_type": "singleTariff",
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH"),
                    "volume": rate.get("volume"),
                    "period": single_tariff.get("period"),
                    "extracted_at": datetime.utcnow()
                })
    
    return solar_fits

def extract_green_power_charges(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract green power charge information - FIXED for Australian CDR API"""
    plan_id = plan_detail.get("planId")
    green_power_charges = []
    
    # FIXED: Get the correct contract based on fuel type
    if fuel_type == "ELECTRICITY":
        contract = plan_detail.get("electricityContract", {})
    elif fuel_type == "GAS":
        contract = plan_detail.get("gasContract", {})
    else:
        contract = plan_detail.get("electricityContract") or plan_detail.get("gasContract") or plan_detail
    
    if not contract:
        contract = plan_detail
    
    # Extract green power from the correct contract location
    for gp in contract.get("greenPowerCharges", []):
        for tier in gp.get("tiers", []):
            green_power_charges.append({
                "plan_id": plan_id,
                "fuel_type": fuel_type,
                "display_name": gp.get("displayName"),
                "description": gp.get("description"),
                "scheme": gp.get("scheme"),
                "charge_type": gp.get("type"),
                "percent_green": float(tier["percentGreen"]) if tier.get("percentGreen") else None,
                "rate": float(tier["rate"]) if tier.get("rate") else None,
                "amount": float(tier["amount"]) if tier.get("amount") else None,
                "extracted_at": datetime.utcnow()
            })
    
    return green_power_charges

def process_plan_comprehensive(plan_id: str, retailer: str, fuel_type: str, extraction_run_id: str) -> Dict[str, List]:
    """Process a single plan and extract all comprehensive data"""
    logger.debug(f"Processing {plan_id} ({fuel_type}) from {retailer}")
    
    # Initialize result structure
    extracted_data = {
        "plan_details": [],
        "tariff_rates": [],
        "fees": [],
        "solar_fits": [],
        "green_power": []
    }
    
    # Fetch detailed plan data
    plan_detail = fetch_plan_detail(plan_id, retailer)
    if not plan_detail:
        logger.warning(f"Could not fetch plan details for {plan_id}")
        return extracted_data
    
    try:
        # Extract all data types
        plan_details = extract_plan_contract_details(plan_detail, fuel_type)
        if plan_details:
            plan_details["extraction_run_id"] = extraction_run_id
            extracted_data["plan_details"].append(plan_details)
        
        extracted_data["tariff_rates"] = extract_comprehensive_tariff_rates(plan_detail, fuel_type)
        extracted_data["fees"] = extract_fees(plan_detail, fuel_type)
        
        # Electricity-specific extractions
        if fuel_type in ["ELECTRICITY", "DUAL"]:
            extracted_data["solar_fits"] = extract_solar_feed_in_tariffs(plan_detail)
        
        extracted_data["green_power"] = extract_green_power_charges(plan_detail, fuel_type)
        
        # Log extraction summary
        total_records = sum(len(records) for records in extracted_data.values())
        logger.debug(f"Extracted {total_records} records from {plan_id}: "
                    f"rates={len(extracted_data['tariff_rates'])}, "
                    f"fees={len(extracted_data['fees'])}")
        
    except Exception as e:
        logger.error(f"Error processing {plan_id}: {e}")
    
    return extracted_data

def load_comprehensive_data_to_bigquery(all_extracted_data: Dict[str, List], extraction_run_id: str):
    """Load all extracted data to BigQuery tables"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Table mappings
    table_mappings = {
        "plan_details": "plan_contract_details",
        "tariff_rates": "tariff_rates_comprehensive", 
        "fees": "plan_fees",
        "solar_fits": "solar_feed_in_tariffs",
        "green_power": "green_power_charges"
    }
    
    load_summary = {}
    
    for data_type, table_name in table_mappings.items():
        data = all_extracted_data.get(data_type, [])
        if not data:
            load_summary[data_type] = 0
            continue
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data)
            df = df.where(pd.notnull(df), None)
            
            # Load to BigQuery
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
            job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
            
            job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            load_summary[data_type] = len(data)
            logger.info(f"Loaded {len(data)} {data_type} records to {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to load {data_type} to {table_name}: {e}")
            load_summary[data_type] = f"ERROR: {str(e)[:50]}"
    
    # Log overall summary
    total_loaded = sum(count for count in load_summary.values() if isinstance(count, int))
    logger.info(f"Load complete for run {extraction_run_id}: {total_loaded} total records")
    
    return load_summary

def process_plans_batch(plans_batch: List[tuple], extraction_run_id: str) -> Dict[str, List]:
    """Process a batch of plans"""
    # Initialize aggregated results
    all_extracted_data = {
        "plan_details": [],
        "tariff_rates": [],
        "fees": [],
        "solar_fits": [],
        "green_power": []
    }
    
    for plan_id, retailer, fuel_type in plans_batch:
        extracted_data = process_plan_comprehensive(plan_id, retailer, fuel_type, extraction_run_id)
        
        # Aggregate results
        for data_type in all_extracted_data.keys():
            all_extracted_data[data_type].extend(extracted_data.get(data_type, []))
        
        # Rate limiting
        time.sleep(0.5)
    
    return all_extracted_data

def main():
    parser = argparse.ArgumentParser(description="Comprehensive tariff data extraction")
    parser.add_argument("--sample", type=int, help="Extract details for N sample plans")
    parser.add_argument("--retailer", type=str, help="Extract details for specific retailer")
    parser.add_argument("--fuel-type", type=str, choices=["ELECTRICITY", "GAS", "DUAL"], 
                       help="Extract details for specific fuel type")
    parser.add_argument("--batch-size", type=int, default=20, 
                       help="Batch size for processing")
    parser.add_argument("--create-tables", action="store_true", 
                       help="Create/recreate all tables before extraction")
    
    args = parser.parse_args()
    
    start_time = time.time()
    extraction_run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    
    logger.info(f"🚀 Starting comprehensive tariff extraction")
    logger.info(f"   Project: {PROJECT_ID}")
    logger.info(f"   Run ID: {extraction_run_id}")
    
    # Create tables
    if args.create_tables:
        logger.info("Creating comprehensive tables...")
    create_comprehensive_tables()
    
    # Get plans to process
    plans_to_process = get_plans_to_extract(args.sample, args.retailer, args.fuel_type)
    
    if not plans_to_process:
        logger.error("No plans found to process")
        return
    
    logger.info(f"Found {len(plans_to_process)} plans to process")
    
    # Initialize aggregated results
    all_extracted_data = {
        "plan_details": [],
        "tariff_rates": [],
        "fees": [],
        "solar_fits": [],
        "green_power": []
    }
    
    # Process in batches
    total_batches = (len(plans_to_process) + args.batch_size - 1) // args.batch_size
    
    for i in range(0, len(plans_to_process), args.batch_size):
        batch = plans_to_process[i:i + args.batch_size]
        batch_num = i // args.batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} plans)")
        
        batch_data = process_plans_batch(batch, extraction_run_id)
        
        # Aggregate batch results
        for data_type in all_extracted_data.keys():
            all_extracted_data[data_type].extend(batch_data.get(data_type, []))
        
        # Load batch to BigQuery
        load_summary = load_comprehensive_data_to_bigquery(batch_data, extraction_run_id)
        
        batch_total = sum(count for count in load_summary.values() if isinstance(count, int))
        logger.info(f"Batch {batch_num} complete: {batch_total} records loaded")
        
        # Small delay between batches
        time.sleep(2)
    
    # Final summary
    total_time = time.time() - start_time
    total_records = sum(len(records) for records in all_extracted_data.values())
    
    logger.info(f"🎉 Comprehensive extraction complete!")
    logger.info(f"   Plans processed: {len(plans_to_process)}")
    logger.info(f"   Total records: {total_records:,}")
    logger.info(f"   Total time: {total_time:.1f}s")
    
    for data_type, records in all_extracted_data.items():
        if records:
            logger.info(f"   {data_type}: {len(records):,} records")

if __name__ == "__main__":
    main()