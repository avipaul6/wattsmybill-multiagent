#!/usr/bin/env python3
"""
Updated extract_plans.py - Fixed schema handling for existing tables
"""

import requests
import json
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
import logging
import time
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Use environment variable or fallback
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
DATASET_ID = 'energy_plans'
TABLE_ID = 'plans_simple'

def get_active_retailers(tier_filter=None, max_retailers=None, client=None):
    """Get active retailers from BigQuery registry with enhanced metadata"""
    if not client:
        client = bigquery.Client(project=PROJECT_ID)
    
    # Check if retailer registry exists
    try:
        where_conditions = ["status = 'ACTIVE'", "extraction_enabled = TRUE"]
        
        if tier_filter:
            if isinstance(tier_filter, list):
                tier_list = "', '".join(tier_filter)
                where_conditions.append(f"tier IN ('{tier_list}')")
            else:
                where_conditions.append(f"tier = '{tier_filter}'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Check which columns exist in the retailer registry
        try:
            schema_check = f"SELECT * FROM `{PROJECT_ID}.{DATASET_ID}.retailer_registry` LIMIT 1"
            schema_df = client.query(schema_check).to_dataframe()
            available_columns = set(schema_df.columns)
        except:
            available_columns = set()
        
        # Build query with only available columns
        base_columns = [
            "retailer_id", "retailer_name", "tier", "priority", "max_plans_limit",
            "api_endpoint", "geographic_coverage", "fuel_types", "customer_types"
        ]
        
        optional_columns = []
        if "total_plans_extracted" in available_columns:
            optional_columns.append("COALESCE(total_plans_extracted, 0) as historical_plans")
        if "last_successful_extraction" in available_columns:
            optional_columns.append("last_successful_extraction")
        if "extraction_success_rate" in available_columns:
            optional_columns.append("COALESCE(extraction_success_rate, 0.0) as success_rate")
        
        # Only include base columns that actually exist
        existing_base_columns = [col for col in base_columns if col in available_columns]
        
        all_columns = existing_base_columns + optional_columns
        
        query = f"""
        SELECT {', '.join(all_columns)}
        FROM `{PROJECT_ID}.{DATASET_ID}.retailer_registry`
        WHERE {where_clause}
        ORDER BY priority ASC, tier ASC, retailer_name ASC
        """
        
        if max_retailers:
            query += f" LIMIT {max_retailers}"
        
        result = client.query(query).to_dataframe()
        
        if not result.empty:
            # Convert to list of dicts for better handling
            retailers = result.to_dict('records')
            logger.info(f"📊 Loaded {len(retailers)} active retailers from registry")
            
            # Show tier breakdown
            tier_counts = result['tier'].value_counts()
            tier_summary = ', '.join([f"{tier}: {count}" for tier, count in tier_counts.items()])
            logger.info(f"   Tier breakdown: {tier_summary}")
            
            # Show retailers with expected plan limits
            retailer_names = [r['retailer_id'] for r in retailers[:10]]
            logger.info(f"   Retailers: {', '.join(retailer_names)}{'...' if len(retailers) > 10 else ''}")
            
            return retailers
        else:
            logger.warning("No active retailers found in registry")
            return []
            
    except Exception as e:
        logger.warning(f"Could not load retailers from registry: {e}")
        logger.info("Falling back to hardcoded retailer list")
        
        # Fallback to hardcoded list if registry doesn't exist
        fallback_retailers = [
            "agl", "origin", "energyaustralia", "alinta", "red-energy",
            "lumo", "momentum", "powershop", "diamond", "dodo",
            "amber", "nectr", "ovo-energy", "shell-energy", "globird"
        ]
        
        # Convert to dict format for consistency
        return [{"retailer_id": r, "retailer_name": r.title(), "tier": "UNKNOWN", 
                "priority": 99, "max_plans_limit": 500} for r in fallback_retailers]

def update_retailer_extraction_stats(retailer_id, success, plans_extracted=0, extraction_time=0, 
                                   error_message=None, client=None):
    """Enhanced update extraction statistics in retailer registry"""
    if not client:
        client = bigquery.Client(project=PROJECT_ID)
    
    try:
        # Calculate success rate (simple running average for now)
        success_rate_update = ""
        if success:
            success_rate_update = """
            extraction_success_rate = CASE 
                WHEN extraction_success_rate IS NULL THEN 100.0
                ELSE LEAST(100.0, extraction_success_rate + 1.0)
            END,
            """
        else:
            success_rate_update = """
            extraction_success_rate = CASE 
                WHEN extraction_success_rate IS NULL THEN 0.0
                ELSE GREATEST(0.0, extraction_success_rate - 5.0)
            END,
            """
        
        # Update notes with error if failed
        notes_update = ""
        if not success and error_message:
            clean_error = error_message.replace("'", "''")[:200]  # Escape quotes and limit length
            notes_update = f"""
            notes = CONCAT(
                COALESCE(notes, ''), 
                ' | Failed: {datetime.utcnow().strftime("%Y-%m-%d %H:%M")} - {clean_error}'
            ),
            """
        
        update_query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.retailer_registry`
        SET 
            last_extraction_attempt = CURRENT_TIMESTAMP(),
            {f"last_successful_extraction = CURRENT_TIMESTAMP()," if success else ""}
            total_plans_extracted = COALESCE(total_plans_extracted, 0) + {plans_extracted},
            avg_extraction_time_seconds = CASE 
                WHEN avg_extraction_time_seconds IS NULL THEN {extraction_time}
                ELSE (COALESCE(avg_extraction_time_seconds, 0) + {extraction_time}) / 2.0
            END,
            {success_rate_update}
            {notes_update}
            updated_at = CURRENT_TIMESTAMP()
        WHERE retailer_id = '{retailer_id}'
        """
        
        client.query(update_query).result()
        logger.debug(f"Updated stats for {retailer_id}: success={success}, plans={plans_extracted}, time={extraction_time:.1f}s")
        
    except Exception as e:
        logger.debug(f"Could not update retailer stats: {e}")

def get_table_schema(client, table_ref):
    """Get the current schema of an existing table"""
    try:
        table = client.get_table(table_ref)
        return {field.name: field for field in table.schema}
    except:
        return None

def create_or_update_table(force_schema_update=False):
    """Create table or update schema if needed"""
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
    
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Define ideal schema
    ideal_schema = [
        bigquery.SchemaField("plan_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("retailer", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("retailer_name", "STRING"),  # New field
        bigquery.SchemaField("retailer_tier", "STRING"),  # New field
        bigquery.SchemaField("plan_name", "STRING"),
        bigquery.SchemaField("brand", "STRING"),
        bigquery.SchemaField("plan_type", "STRING"),
        bigquery.SchemaField("fuel_type", "STRING"),
        bigquery.SchemaField("customer_type", "STRING"),
        bigquery.SchemaField("effective_from", "TIMESTAMP"),
        bigquery.SchemaField("effective_to", "TIMESTAMP"),
        bigquery.SchemaField("last_updated", "TIMESTAMP"),
        bigquery.SchemaField("application_url", "STRING"),
        bigquery.SchemaField("extracted_at", "TIMESTAMP"),
        bigquery.SchemaField("extraction_run_id", "STRING"),  # New field
        bigquery.SchemaField("raw_data", "STRING")
    ]
    
    # Check if table exists
    existing_schema = get_table_schema(client, table_ref)
    
    if existing_schema is None:
        # Table doesn't exist, create with ideal schema
        table = bigquery.Table(table_ref, ideal_schema)
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="extracted_at"
        )
        table.clustering_fields = ["retailer", "fuel_type", "customer_type"]
        table = client.create_table(table)
        logger.info(f"Created new table {TABLE_ID} with enhanced schema")
        return ideal_schema
    
    elif force_schema_update:
        # Add missing fields to existing table
        existing_field_names = set(existing_schema.keys())
        ideal_field_names = {field.name for field in ideal_schema}
        missing_fields = ideal_field_names - existing_field_names
        
        if missing_fields:
            logger.info(f"Adding missing fields to table: {missing_fields}")
            
            # Get current table
            table = client.get_table(table_ref)
            
            # Add missing fields
            new_schema = list(table.schema)
            for field in ideal_schema:
                if field.name in missing_fields:
                    new_schema.append(field)
            
            # Update table schema
            table.schema = new_schema
            table = client.update_table(table, ["schema"])
            logger.info(f"Updated table schema with {len(missing_fields)} new fields")
        
        return ideal_schema
    
    else:
        # Use existing schema as-is
        logger.info(f"Using existing table schema (use --update-schema to add new fields)")
        return list(existing_schema.values())

def prepare_plans_for_loading(plans, table_schema):
    """Prepare plans data to match the existing table schema"""
    if not plans:
        return []
    
    # Get field names from schema
    if isinstance(table_schema, list):
        schema_fields = {field.name for field in table_schema}
    else:
        schema_fields = set(table_schema.keys())
    
    # Filter plans to only include fields that exist in the table
    filtered_plans = []
    for plan in plans:
        filtered_plan = {k: v for k, v in plan.items() if k in schema_fields}
        filtered_plans.append(filtered_plan)
    
    # Log what fields we're including/excluding
    plan_fields = set(plans[0].keys()) if plans else set()
    included_fields = plan_fields & schema_fields
    excluded_fields = plan_fields - schema_fields
    
    if excluded_fields:
        logger.info(f"Excluding fields not in table schema: {excluded_fields}")
    logger.info(f"Including fields: {included_fields}")
    
    return filtered_plans

def fetch_plans_from_retailer(retailer_info, extraction_run_id, client=None):
    """Enhanced fetch plans from a single retailer using registry metadata"""
    start_time = time.time()
    retailer_id = retailer_info['retailer_id']
    retailer_name = retailer_info.get('retailer_name', retailer_id)
    max_plans = retailer_info.get('max_plans_limit', 500)
    api_endpoint = retailer_info.get('api_endpoint', retailer_id)
    
    logger.info(f"Fetching plans from {retailer_name} ({retailer_id}) - max plans: {max_plans}")
    
    url = f"https://cdr.energymadeeasy.gov.au/{api_endpoint}/cds-au/v1/energy/plans"
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
    error_message = None
    
    try:
        while True:
            params["page"] = page
            
            try:
                response = requests.get(url, headers=headers, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    plans = data.get("data", {}).get("plans", [])
                    
                    if not plans:
                        break
                    
                    # Transform plans to simple format with registry metadata
                    for plan in plans:
                        simple_plan = {
                            "plan_id": plan.get("planId"),
                            "retailer": retailer_id,
                            "retailer_name": retailer_name,
                            "retailer_tier": retailer_info.get('tier'),
                            "plan_name": plan.get("displayName"),
                            "brand": plan.get("brandName"),
                            "plan_type": plan.get("type"),
                            "fuel_type": plan.get("fuelType"),
                            "customer_type": plan.get("customerType"),
                            "application_url": plan.get("applicationUri"),
                            "extracted_at": datetime.utcnow(),
                            "extraction_run_id": extraction_run_id,
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
                    
                    logger.info(f"Fetched page {page} from {retailer_id}: {len(plans)} plans (total: {len(all_plans)})")
                    
                    # Respect max plans limit from registry
                    if len(all_plans) >= max_plans:
                        logger.info(f"Reached max plans limit ({max_plans}) for {retailer_id}")
                        all_plans = all_plans[:max_plans]
                        break
                    
                    # Check if more pages
                    meta = data.get("meta", {})
                    if page >= meta.get("totalPages", 1):
                        break
                    
                    page += 1
                    time.sleep(0.5)  # Rate limiting
                    
                else:
                    error_message = f"HTTP {response.status_code}: {response.text[:100]}"
                    logger.error(f"Failed to fetch from {retailer_id}: {error_message}")
                    # Update retailer stats with failure
                    update_retailer_extraction_stats(
                        retailer_id, False, 0, time.time() - start_time, error_message, client
                    )
                    break
                    
            except Exception as e:
                error_message = str(e)[:100]
                logger.error(f"Error fetching from {retailer_id}: {error_message}")
                # Update retailer stats with failure
                update_retailer_extraction_stats(
                    retailer_id, False, 0, time.time() - start_time, error_message, client
                )
                break
        
        # Update retailer stats with success
        extraction_time = time.time() - start_time
        update_retailer_extraction_stats(
            retailer_id, True, len(all_plans), extraction_time, None, client
        )
        
    except Exception as e:
        error_message = str(e)[:100]
        logger.error(f"Overall error fetching from {retailer_id}: {error_message}")
        update_retailer_extraction_stats(
            retailer_id, False, 0, time.time() - start_time, error_message, client
        )
    
    logger.info(f"Total plans from {retailer_id}: {len(all_plans)} (took {time.time() - start_time:.1f}s)")
    return all_plans

def load_plans_to_bigquery(all_plans, extraction_run_id, table_schema):
    """Load plans to BigQuery with schema compatibility"""
    if not all_plans:
        logger.warning("No plans to load")
        return
    
    client = bigquery.Client(project=PROJECT_ID)
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
    
    # Prepare plans to match table schema
    filtered_plans = prepare_plans_for_loading(all_plans, table_schema)
    
    if not filtered_plans:
        logger.error("No valid plans after schema filtering")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(filtered_plans)
    
    # Clean up None values
    df = df.where(pd.notnull(df), None)
    
    # Load to BigQuery
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        create_disposition="CREATE_IF_NEEDED"
    )
    
    logger.info(f"Loading {len(filtered_plans)} plans to BigQuery (run_id: {extraction_run_id})...")
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # Wait for completion
    
    logger.info(f"Successfully loaded {len(filtered_plans)} plans to BigQuery")
    
    # Verify
    query = f"SELECT COUNT(*) as total FROM `{table_ref}` WHERE extraction_run_id = '{extraction_run_id}'"
    try:
        result = client.query(query).to_dataframe()
        if not result.empty:
            logger.info(f"Verified: {result['total'].iloc[0]} plans loaded for this run")
    except:
        # extraction_run_id field might not exist in old schema
        query = f"SELECT COUNT(*) as total FROM `{table_ref}`"
        result = client.query(query).to_dataframe()
        logger.info(f"Total plans in table: {result['total'].iloc[0]}")

def show_extraction_summary(retailers, all_plans, extraction_run_id):
    """Show detailed extraction summary with registry insights"""
    if not all_plans:
        return
        
    df = pd.DataFrame(all_plans)
    retailer_df = pd.DataFrame(retailers)
    
    logger.info(f"📊 Extraction Summary (Run ID: {extraction_run_id}):")
    logger.info(f"   Total plans extracted: {len(all_plans):,}")
    logger.info(f"   Retailers processed: {df['retailer'].nunique()}/{len(retailers)}")
    logger.info(f"   Fuel types: {', '.join(df['fuel_type'].unique())}")
    logger.info(f"   Customer types: {', '.join(df['customer_type'].unique())}")
    
    # Plans by tier (if available)
    if 'retailer_tier' in df.columns:
        tier_summary = df.groupby('retailer_tier').size().sort_values(ascending=False)
        logger.info(f"   Plans by tier:")
        for tier, count in tier_summary.items():
            logger.info(f"     {tier}: {count:,} plans")
    
    # Top retailers by plan count
    retailer_cols = ['retailer']
    if 'retailer_name' in df.columns:
        retailer_cols.append('retailer_name')
    
    top_retailers = df.groupby(retailer_cols).size().sort_values(ascending=False).head(10)
    logger.info(f"   Top retailers by plan count:")
    for retailer_info, count in top_retailers.items():
        if isinstance(retailer_info, tuple):
            retailer_id, retailer_name = retailer_info
            tier_info = retailer_df[retailer_df['retailer_id'] == retailer_id]['tier'].iloc[0] if len(retailer_df[retailer_df['retailer_id'] == retailer_id]) > 0 else 'Unknown'
            logger.info(f"     {retailer_name} ({tier_info}): {count:,} plans")
        else:
            logger.info(f"     {retailer_info}: {count:,} plans")
    
    # Show any retailers that returned 0 plans
    retailers_with_plans = set(df['retailer'].unique())
    all_retailer_ids = set([r['retailer_id'] for r in retailers])
    failed_retailers = all_retailer_ids - retailers_with_plans
    
    if failed_retailers:
        logger.warning(f"   ⚠️  Retailers with 0 plans: {', '.join(failed_retailers)}")

def main(tier_filter=None, max_retailers=None, append_mode=True, update_schema=False):
    """Enhanced main extraction process with schema handling"""
    extraction_run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    logger.info(f"Starting energy plans extraction (Run ID: {extraction_run_id})")
    logger.info(f"Project: {PROJECT_ID}, Mode: {'APPEND' if append_mode else 'REPLACE'}")
    
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create/update table
    table_schema = create_or_update_table(force_schema_update=update_schema)
    
    # Get retailers from registry
    retailers = get_active_retailers(tier_filter=tier_filter, max_retailers=max_retailers, client=client)
    
    if not retailers:
        logger.error("No retailers found for extraction")
        return
    
    # Calculate expected plans
    expected_plans = sum([r.get('max_plans_limit', 100) for r in retailers])
    logger.info(f"Extracting from {len(retailers)} retailers (expecting ~{expected_plans:,} plans)")
    
    # If not append mode, clear previous data
    if not append_mode:
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"
        client.query(f"DELETE FROM `{table_ref}` WHERE true").result()
        logger.info("Cleared existing data (REPLACE mode)")
    
    # Extract from all retailers
    all_plans = []
    successful_retailers = 0
    
    for i, retailer_info in enumerate(retailers, 1):
        retailer_id = retailer_info['retailer_id']
        logger.info(f"[{i}/{len(retailers)}] Processing {retailer_id}...")
        
        plans = fetch_plans_from_retailer(retailer_info, extraction_run_id, client)
        if plans:
            all_plans.extend(plans)
            successful_retailers += 1
        
        # Add small delay between retailers to be respectful
        time.sleep(1)
    
    logger.info(f"Extraction complete: {successful_retailers}/{len(retailers)} retailers successful")
    
    # Load to BigQuery
    if all_plans:
        load_plans_to_bigquery(all_plans, extraction_run_id, table_schema)
        show_extraction_summary(retailers, all_plans, extraction_run_id)
    else:
        logger.error("No plans extracted from any retailer!")
    
    logger.info("Extraction process finished!")
    return len(all_plans)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract energy plans from dynamic retailer registry")
    parser.add_argument("--tier", type=str, help="Filter by retailer tier (MAJOR, SECONDARY, REGIONAL, EMERGING)")
    parser.add_argument("--max-retailers", type=int, help="Maximum number of retailers to process")
    parser.add_argument("--major-only", action="store_true", help="Extract only major retailers")
    parser.add_argument("--replace", action="store_true", help="Replace existing data instead of appending")
    parser.add_argument("--update-schema", action="store_true", help="Update table schema to add new fields")
    
    args = parser.parse_args()
    
    tier_filter = None
    if args.major_only:
        tier_filter = "MAJOR"
    elif args.tier:
        tier_filter = args.tier.upper()
    
    main(
        tier_filter=tier_filter, 
        max_retailers=args.max_retailers, 
        append_mode=not args.replace,
        update_schema=args.update_schema
    )