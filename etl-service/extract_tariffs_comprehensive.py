#!/usr/bin/env python3
"""
Enhanced extract_tariffs.py - Comprehensive tariff data extraction
Captures the full CDR Energy API schema including contracts, discounts, fees, etc.
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
    
    # 1. Plan Details - Main plan information with raw data
    plan_details_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("retailer", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING"),  # ELECTRICITY, GAS, DUAL
        bigquery.SchemaField("pricing_model", "STRING"),  # SINGLE_RATE, TIME_OF_USE, etc
        bigquery.SchemaField("is_fixed", "BOOLEAN"),
        bigquery.SchemaField("term_type", "STRING"),  # 1_YEAR, 2_YEAR, etc
        bigquery.SchemaField("cooling_off_days", "INTEGER"),
        bigquery.SchemaField("payment_options", "STRING"),  # JSON array
        bigquery.SchemaField("meter_types", "STRING"),  # JSON array
        bigquery.SchemaField("bill_frequency", "STRING"),  # JSON array
        bigquery.SchemaField("time_zone", "STRING"),
        bigquery.SchemaField("variation", "STRING"),
        bigquery.SchemaField("on_expiry_description", "STRING"),
        bigquery.SchemaField("benefit_period", "STRING"),
        bigquery.SchemaField("terms", "STRING"),
        bigquery.SchemaField("additional_fee_information", "STRING"),
        bigquery.SchemaField("intrinsic_green_power_percentage", "FLOAT"),
        bigquery.SchemaField("raw_contract_data", "STRING"),  # Full JSON for backup
        bigquery.SchemaField("extracted_at", "TIMESTAMP"),
        bigquery.SchemaField("extraction_run_id", "STRING")
    ]
    
    # 2. Tariff Periods and Rates
    tariff_rates_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("tariff_period_type", "STRING"),  # ENVIRONMENTAL, PEAK, etc
        bigquery.SchemaField("tariff_period_name", "STRING"),
        bigquery.SchemaField("start_date", "DATE"),
        bigquery.SchemaField("end_date", "DATE"),
        bigquery.SchemaField("rate_structure", "STRING"),  # singleRate, timeOfUseRates, demandCharges
        bigquery.SchemaField("rate_type", "STRING"),  # DAILY_SUPPLY, USAGE, DEMAND
        bigquery.SchemaField("time_of_use_type", "STRING"),  # PEAK, OFF_PEAK, SHOULDER
        bigquery.SchemaField("unit_price", "FLOAT"),
        bigquery.SchemaField("unit", "STRING"),  # KWH, KW, DAYS, MJ
        bigquery.SchemaField("volume_min", "FLOAT"),
        bigquery.SchemaField("volume_max", "FLOAT"),
        bigquery.SchemaField("period", "STRING"),  # P1Y, P1M, etc
        bigquery.SchemaField("start_time", "STRING"),
        bigquery.SchemaField("end_time", "STRING"),
        bigquery.SchemaField("days_of_week", "STRING"),  # JSON array
        bigquery.SchemaField("daily_supply_charge_type", "STRING"),  # SINGLE, BANDED
        bigquery.SchemaField("general_unit_price", "FLOAT"),
        bigquery.SchemaField("measurement_period", "STRING"),  # For demand charges
        bigquery.SchemaField("charge_period", "STRING"),  # For demand charges
        bigquery.SchemaField("min_demand", "FLOAT"),
        bigquery.SchemaField("max_demand", "FLOAT"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 3. Discounts
    discounts_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("display_name", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("discount_type", "STRING"),  # CONDITIONAL, GUARANTEED, etc
        bigquery.SchemaField("category", "STRING"),  # PAY_ON_TIME, DIRECT_DEBIT, etc
        bigquery.SchemaField("end_date", "DATE"),
        bigquery.SchemaField("method_type", "STRING"),  # percentOfBill, percentOfUse, fixedAmount, etc
        bigquery.SchemaField("rate", "FLOAT"),  # Percentage or fixed amount
        bigquery.SchemaField("amount", "FLOAT"),  # For fixed amounts
        bigquery.SchemaField("usage_amount", "FLOAT"),  # For threshold-based discounts
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 4. Fees
    fees_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fee_type", "STRING"),  # EXIT, LATE_PAYMENT, CONNECTION, etc
        bigquery.SchemaField("term", "STRING"),  # FIXED, PERCENT, etc
        bigquery.SchemaField("amount", "FLOAT"),
        bigquery.SchemaField("rate", "FLOAT"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 5. Incentives
    incentives_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("display_name", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("category", "STRING"),  # GIFT, ACCOUNT_CREDIT, etc
        bigquery.SchemaField("eligibility", "STRING"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 6. Solar Feed-in Tariffs
    solar_fit_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("display_name", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("start_date", "DATE"),
        bigquery.SchemaField("end_date", "DATE"),
        bigquery.SchemaField("scheme", "STRING"),  # PREMIUM, REGIONAL, etc
        bigquery.SchemaField("payer_type", "STRING"),  # GOVERNMENT, RETAILER
        bigquery.SchemaField("tariff_type", "STRING"),  # singleTariff, timeVaryingTariffs
        bigquery.SchemaField("time_of_use_type", "STRING"),  # PEAK, OFF_PEAK, etc
        bigquery.SchemaField("unit_price", "FLOAT"),
        bigquery.SchemaField("unit", "STRING"),  # KWH
        bigquery.SchemaField("volume", "FLOAT"),
        bigquery.SchemaField("period", "STRING"),
        bigquery.SchemaField("start_time", "STRING"),
        bigquery.SchemaField("end_time", "STRING"),
        bigquery.SchemaField("days_of_week", "STRING"),  # JSON array
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 7. Controlled Load
    controlled_load_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("display_name", "STRING"),
        bigquery.SchemaField("start_date", "DATE"),
        bigquery.SchemaField("end_date", "DATE"),
        bigquery.SchemaField("rate_structure", "STRING"),  # singleRate, timeOfUseRates
        bigquery.SchemaField("daily_supply_charge", "FLOAT"),
        bigquery.SchemaField("time_of_use_type", "STRING"),
        bigquery.SchemaField("unit_price", "FLOAT"),
        bigquery.SchemaField("unit", "STRING"),
        bigquery.SchemaField("volume", "FLOAT"),
        bigquery.SchemaField("period", "STRING"),
        bigquery.SchemaField("start_time", "STRING"),
        bigquery.SchemaField("end_time", "STRING"),
        bigquery.SchemaField("days_of_week", "STRING"),  # JSON array
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 8. Green Power Charges
    green_power_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("display_name", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("scheme", "STRING"),  # GREENPOWER, etc
        bigquery.SchemaField("charge_type", "STRING"),  # FIXED_PER_DAY, FIXED_PER_WEEK, etc
        bigquery.SchemaField("percent_green", "FLOAT"),
        bigquery.SchemaField("rate", "FLOAT"),
        bigquery.SchemaField("amount", "FLOAT"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 9. Eligibility Criteria
    eligibility_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("fuel_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("eligibility_type", "STRING"),  # EXISTING_CUST, NEW_CUST, etc
        bigquery.SchemaField("information", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # 10. Metering Charges
    metering_charges_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("display_name", "STRING"),
        bigquery.SchemaField("description", "STRING"),
        bigquery.SchemaField("minimum_value", "FLOAT"),
        bigquery.SchemaField("maximum_value", "FLOAT"),
        bigquery.SchemaField("period", "STRING"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP")
    ]
    
    # Create all tables
    tables_to_create = [
        ("plan_contract_details", plan_details_schema),
        ("tariff_rates_comprehensive", tariff_rates_schema),
        ("plan_discounts", discounts_schema),
        ("plan_fees", fees_schema),
        ("plan_incentives", incentives_schema),
        ("solar_feed_in_tariffs", solar_fit_schema),
        ("controlled_load_tariffs", controlled_load_schema),
        ("green_power_charges", green_power_schema),
        ("plan_eligibility", eligibility_schema),
        ("metering_charges", metering_charges_schema)
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
    """Extract main contract details"""
    plan_id = plan_detail.get("planId")
    
    # Determine which contract to process
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    elif fuel_type == "DUAL":
        # For dual fuel, we'll prioritize electricity contract
        contract = plan_detail.get("electricityContract") or plan_detail.get("gasContract")
    
    if not contract:
        return {}
    
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
        "raw_contract_data": json.dumps(contract),  # Store full contract for backup
        "extracted_at": datetime.utcnow()
    }

def extract_comprehensive_tariff_rates(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract all tariff rates including complex structures"""
    plan_id = plan_detail.get("planId")
    rates = []
    
    # Get the appropriate contract
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    
    if not contract:
        return rates
    
    # Process tariff periods
    for period in contract.get("tariffPeriod", []):
        period_type = period.get("type")
        period_name = period.get("displayName")
        start_date = period.get("startDate")
        end_date = period.get("endDate")
        
        # Daily supply charges
        if period.get("dailySupplyCharge"):
            rates.append({
                "plan_id": plan_id,
                "fuel_type": fuel_type,
                "tariff_period_type": period_type,
                "tariff_period_name": period_name,
                "start_date": start_date,
                "end_date": end_date,
                "rate_structure": "dailySupplyCharge",
                "rate_type": "DAILY_SUPPLY",
                "time_of_use_type": "ALL_DAY",
                "unit_price": float(period["dailySupplyCharge"]),
                "unit": "DAYS",
                "daily_supply_charge_type": period.get("dailySupplyChargeType"),
                "extracted_at": datetime.utcnow()
            })
        
        # Banded daily supply charges
        for banded in period.get("bandedDailySupplyCharges", []):
            rates.append({
                "plan_id": plan_id,
                "fuel_type": fuel_type,
                "tariff_period_type": period_type,
                "tariff_period_name": period_name,
                "rate_structure": "bandedDailySupplyCharge",
                "rate_type": "DAILY_SUPPLY",
                "unit_price": float(banded["unitPrice"]),
                "unit": banded.get("measureUnit", "DAYS"),
                "volume_min": banded.get("volume"),
                "daily_supply_charge_type": "BANDED",
                "extracted_at": datetime.utcnow()
            })
        
        # Single rate
        if period.get("singleRate"):
            single_rate = period["singleRate"]
            general_price = single_rate.get("generalUnitPrice")
            
            if general_price:
                rates.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "tariff_period_type": period_type,
                    "tariff_period_name": period_name,
                    "rate_structure": "singleRate",
                    "rate_type": "USAGE",
                    "time_of_use_type": "ALL_DAY",
                    "unit_price": float(general_price),
                    "unit": "KWH" if fuel_type == "ELECTRICITY" else "MJ",
                    "general_unit_price": float(general_price),
                    "period": single_rate.get("period"),
                    "extracted_at": datetime.utcnow()
                })
            
            # Stepped rates within single rate
            for rate in single_rate.get("rates", []):
                rates.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "tariff_period_type": period_type,
                    "tariff_period_name": period_name,
                    "rate_structure": "singleRate",
                    "rate_type": "USAGE",
                    "time_of_use_type": "ALL_DAY",
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH" if fuel_type == "ELECTRICITY" else "MJ"),
                    "volume_min": rate.get("volume"),
                    "period": single_rate.get("period"),
                    "extracted_at": datetime.utcnow()
                })
        
        # Time of use rates
        for tou in period.get("timeOfUseRates", []):
            tou_type = tou.get("type")
            
            for rate in tou.get("rates", []):
                # Extract time periods
                time_periods = tou.get("timeOfUse", [])
                start_time = time_periods[0].get("startTime") if time_periods else None
                end_time = time_periods[0].get("endTime") if time_periods else None
                days_of_week = time_periods[0].get("days", []) if time_periods else []
                
                rates.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "tariff_period_type": period_type,
                    "tariff_period_name": period_name,
                    "rate_structure": "timeOfUseRates",
                    "rate_type": "USAGE",
                    "time_of_use_type": tou_type,
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH" if fuel_type == "ELECTRICITY" else "MJ"),
                    "volume_min": rate.get("volume"),
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
    
    return rates

def extract_discounts(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract all discount information"""
    plan_id = plan_detail.get("planId")
    discounts = []
    
    # Get contract based on fuel type
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    
    if not contract:
        return discounts
    
    for discount in contract.get("discounts", []):
        # Base discount info
        discount_data = {
            "plan_id": plan_id,
            "fuel_type": fuel_type,
            "display_name": discount.get("displayName"),
            "description": discount.get("description"),
            "discount_type": discount.get("type"),
            "category": discount.get("category"),
            "end_date": discount.get("endDate"),
            "method_type": discount.get("methodUType"),
            "extracted_at": datetime.utcnow()
        }
        
        # Extract method-specific data
        if discount.get("percentOfBill"):
            discount_data["rate"] = float(discount["percentOfBill"]["rate"])
        elif discount.get("percentOfUse"):
            discount_data["rate"] = float(discount["percentOfUse"]["rate"])
        elif discount.get("fixedAmount"):
            discount_data["amount"] = float(discount["fixedAmount"]["amount"])
        elif discount.get("percentOverThreshold"):
            discount_data["rate"] = float(discount["percentOverThreshold"]["rate"])
            discount_data["usage_amount"] = float(discount["percentOverThreshold"]["usageAmount"])
        
        discounts.append(discount_data)
    
    return discounts

def extract_fees(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract all fee information"""
    plan_id = plan_detail.get("planId")
    fees = []
    
    # Get contract based on fuel type
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    
    if not contract:
        return fees
    
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

def extract_incentives(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract all incentive information"""
    plan_id = plan_detail.get("planId")
    incentives = []
    
    # Get contract based on fuel type
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    
    if not contract:
        return incentives
    
    for incentive in contract.get("incentives", []):
        incentives.append({
            "plan_id": plan_id,
            "fuel_type": fuel_type,
            "display_name": incentive.get("displayName"),
            "description": incentive.get("description"),
            "category": incentive.get("category"),
            "eligibility": incentive.get("eligibility"),
            "extracted_at": datetime.utcnow()
        })
    
    return incentives

def extract_solar_feed_in_tariffs(plan_detail: Dict) -> List[Dict]:
    """Extract solar feed-in tariff information (electricity only)"""
    plan_id = plan_detail.get("planId")
    solar_fits = []
    
    contract = plan_detail.get("electricityContract", {})
    
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
        
        # Time varying tariffs
        for time_tariff in fit.get("timeVaryingTariffs", []):
            for rate in time_tariff.get("rates", []):
                # Extract time variations
                time_vars = time_tariff.get("timeVariations", [])
                start_time = time_vars[0].get("startTime") if time_vars else None
                end_time = time_vars[0].get("endTime") if time_vars else None
                days_of_week = time_vars[0].get("days", []) if time_vars else []
                
                solar_fits.append({
                    "plan_id": plan_id,
                    "display_name": fit.get("displayName"),
                    "description": fit.get("description"),
                    "start_date": fit.get("startDate"),
                    "end_date": fit.get("endDate"),
                    "scheme": fit.get("scheme"),
                    "payer_type": fit.get("payerType"),
                    "tariff_type": "timeVaryingTariffs",
                    "time_of_use_type": time_tariff.get("type"),
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH"),
                    "volume": rate.get("volume"),
                    "period": time_tariff.get("period"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "days_of_week": json.dumps(days_of_week),
                    "extracted_at": datetime.utcnow()
                })
    
    return solar_fits

def extract_controlled_load(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract controlled load information"""
    plan_id = plan_detail.get("planId")
    controlled_loads = []
    
    # Get contract based on fuel type
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    
    if not contract:
        return controlled_loads
    
    for cl in contract.get("controlledLoad", []):
        # Single rate controlled load
        if cl.get("singleRate"):
            single_rate = cl["singleRate"]
            for rate in single_rate.get("rates", []):
                controlled_loads.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "display_name": cl.get("displayName"),
                    "start_date": cl.get("startDate"),
                    "end_date": cl.get("endDate"),
                    "rate_structure": "singleRate",
                    "daily_supply_charge": float(single_rate["dailySupplyCharge"]) if single_rate.get("dailySupplyCharge") else None,
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH"),
                    "volume": rate.get("volume"),
                    "period": single_rate.get("period"),
                    "extracted_at": datetime.utcnow()
                })
        
        # Time of use controlled load
        for tou in cl.get("timeOfUseRates", []):
            for rate in tou.get("rates", []):
                # Extract time periods
                time_periods = tou.get("timeOfUse", [])
                start_time = time_periods[0].get("startTime") if time_periods else None
                end_time = time_periods[0].get("endTime") if time_periods else None
                days_of_week = time_periods[0].get("days", []) if time_periods else []
                
                controlled_loads.append({
                    "plan_id": plan_id,
                    "fuel_type": fuel_type,
                    "display_name": cl.get("displayName"),
                    "start_date": cl.get("startDate"),
                    "end_date": cl.get("endDate"),
                    "rate_structure": "timeOfUseRates",
                    "time_of_use_type": tou.get("type"),
                    "daily_supply_charge": float(tou["dailySupplyCharge"]) if tou.get("dailySupplyCharge") else None,
                    "unit_price": float(rate["unitPrice"]),
                    "unit": rate.get("measureUnit", "KWH"),
                    "volume": rate.get("volume"),
                    "period": tou.get("period"),
                    "start_time": start_time,
                    "end_time": end_time,
                    "days_of_week": json.dumps(days_of_week),
                    "extracted_at": datetime.utcnow()
                })
    
    return controlled_loads

def extract_green_power_charges(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract green power charge information"""
    plan_id = plan_detail.get("planId")
    green_power_charges = []
    
    # Get contract based on fuel type
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    
    if not contract:
        return green_power_charges
    
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

def extract_eligibility(plan_detail: Dict, fuel_type: str) -> List[Dict]:
    """Extract eligibility criteria"""
    plan_id = plan_detail.get("planId")
    eligibility_criteria = []
    
    # Get contract based on fuel type
    contract = None
    if fuel_type == "ELECTRICITY" and "electricityContract" in plan_detail:
        contract = plan_detail["electricityContract"]
    elif fuel_type == "GAS" and "gasContract" in plan_detail:
        contract = plan_detail["gasContract"]
    
    if not contract:
        return eligibility_criteria
    
    for eligibility in contract.get("eligibility", []):
        eligibility_criteria.append({
            "plan_id": plan_id,
            "fuel_type": fuel_type,
            "eligibility_type": eligibility.get("type"),
            "information": eligibility.get("information"),
            "description": eligibility.get("description"),
            "extracted_at": datetime.utcnow()
        })
    
    return eligibility_criteria

def extract_metering_charges(plan_detail: Dict) -> List[Dict]:
    """Extract metering charges"""
    plan_id = plan_detail.get("planId")
    metering_charges = []
    
    for charge in plan_detail.get("meteringCharges", []):
        metering_charges.append({
            "plan_id": plan_id,
            "display_name": charge.get("displayName"),
            "description": charge.get("description"),
            "minimum_value": float(charge["minimumValue"]) if charge.get("minimumValue") else None,
            "maximum_value": float(charge["maximumValue"]) if charge.get("maximumValue") else None,
            "period": charge.get("period"),
            "extracted_at": datetime.utcnow()
        })
    
    return metering_charges

def process_plan_comprehensive(plan_id: str, retailer: str, fuel_type: str, extraction_run_id: str) -> Dict[str, List]:
    """Process a single plan and extract all comprehensive data"""
    logger.info(f"Processing {plan_id} ({fuel_type}) from {retailer}")
    
    # Initialize result structure
    extracted_data = {
        "plan_details": [],
        "tariff_rates": [],
        "discounts": [],
        "fees": [],
        "incentives": [],
        "solar_fits": [],
        "controlled_loads": [],
        "green_power": [],
        "eligibility": [],
        "metering_charges": []
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
        extracted_data["discounts"] = extract_discounts(plan_detail, fuel_type)
        extracted_data["fees"] = extract_fees(plan_detail, fuel_type)
        extracted_data["incentives"] = extract_incentives(plan_detail, fuel_type)
        
        # Electricity-specific extractions
        if fuel_type in ["ELECTRICITY", "DUAL"]:
            extracted_data["solar_fits"] = extract_solar_feed_in_tariffs(plan_detail)
        
        extracted_data["controlled_loads"] = extract_controlled_load(plan_detail, fuel_type)
        extracted_data["green_power"] = extract_green_power_charges(plan_detail, fuel_type)
        extracted_data["eligibility"] = extract_eligibility(plan_detail, fuel_type)
        extracted_data["metering_charges"] = extract_metering_charges(plan_detail)
        
        # Log extraction summary
        total_records = sum(len(records) for records in extracted_data.values())
        logger.info(f"Extracted {total_records} records from {plan_id}: "
                   f"rates={len(extracted_data['tariff_rates'])}, "
                   f"discounts={len(extracted_data['discounts'])}, "
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
        "discounts": "plan_discounts",
        "fees": "plan_fees",
        "incentives": "plan_incentives",
        "solar_fits": "solar_feed_in_tariffs",
        "controlled_loads": "controlled_load_tariffs",
        "green_power": "green_power_charges",
        "eligibility": "plan_eligibility",
        "metering_charges": "metering_charges"
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
        "discounts": [],
        "fees": [],
        "incentives": [],
        "solar_fits": [],
        "controlled_loads": [],
        "green_power": [],
        "eligibility": [],
        "metering_charges": []
    }
    
    for plan_id, retailer, fuel_type in plans_batch:
        extracted_data = process_plan_comprehensive(plan_id, retailer, fuel_type, extraction_run_id)
        
        # Aggregate results
        for data_type in all_extracted_data.keys():
            all_extracted_data[data_type].extend(extracted_data.get(data_type, []))
        
        # Rate limiting
        time.sleep(0.5)
    
    return all_extracted_data

def show_extraction_summary(all_extracted_data: Dict[str, List], extraction_run_id: str, 
                          total_plans: int, start_time: float):
    """Show detailed extraction summary"""
    total_time = time.time() - start_time
    
    logger.info(f"🎯 Comprehensive Extraction Summary (Run ID: {extraction_run_id})")
    logger.info(f"   Plans processed: {total_plans}")
    logger.info(f"   Total time: {total_time:.1f}s ({total_time/total_plans:.1f}s per plan)")
    logger.info(f"   Data extracted:")
    
    for data_type, records in all_extracted_data.items():
        if records:
            logger.info(f"     {data_type}: {len(records):,} records")
    
    total_records = sum(len(records) for records in all_extracted_data.values())
    logger.info(f"   Total records: {total_records:,}")
    
    # Show plan coverage by fuel type
    plan_details = all_extracted_data.get("plan_details", [])
    if plan_details:
        fuel_coverage = {}
        for plan in plan_details:
            fuel_type = plan.get("fuel_type", "UNKNOWN")
            fuel_coverage[fuel_type] = fuel_coverage.get(fuel_type, 0) + 1
        
        logger.info(f"   Fuel type coverage: {dict(fuel_coverage)}")

def main():
    parser = argparse.ArgumentParser(description="Comprehensive tariff data extraction")
    parser.add_argument("--sample", type=int, help="Extract details for N sample plans")
    parser.add_argument("--retailer", type=str, help="Extract details for specific retailer")
    parser.add_argument("--fuel-type", type=str, choices=["ELECTRICITY", "GAS", "DUAL"], 
                       help="Extract details for specific fuel type")
    parser.add_argument("--batch-size", type=int, default=20, 
                       help="Batch size for processing (smaller for comprehensive extraction)")
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
    
    # Confirmation for large extractions
    if not args.sample and not args.retailer and len(plans_to_process) > 100:
        response = input(f"This will process {len(plans_to_process)} plans (comprehensive extraction). Continue? (y/N): ")
        if response.lower() != 'y':
            logger.info("Extraction cancelled")
            return
    
    # Initialize aggregated results
    all_extracted_data = {
        "plan_details": [],
        "tariff_rates": [],
        "discounts": [],
        "fees": [],
        "incentives": [],
        "solar_fits": [],
        "controlled_loads": [],
        "green_power": [],
        "eligibility": [],
        "metering_charges": []
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
    show_extraction_summary(all_extracted_data, extraction_run_id, 
                          len(plans_to_process), start_time)
    
    logger.info("🎉 Comprehensive extraction complete!")

if __name__ == "__main__":
    main()