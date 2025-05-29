#!/usr/bin/env python3
"""
Dynamic Retailer Registry System
Manages retailer list in BigQuery for easy updates and new entrants
"""

import os
import logging
from datetime import datetime
from google.cloud import bigquery
import pandas as pd
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

class RetailerRegistry:
    """Manages dynamic retailer registry in BigQuery"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.table_id = 'retailer_registry'
        
    def create_retailer_registry_table(self):
        """Create the retailer registry table"""
        schema = [
            bigquery.SchemaField("retailer_id", "STRING", mode="REQUIRED", description="Unique retailer identifier"),
            bigquery.SchemaField("retailer_name", "STRING", mode="REQUIRED", description="Display name of retailer"),
            bigquery.SchemaField("api_endpoint", "STRING", description="AER API endpoint identifier"),
            bigquery.SchemaField("tier", "STRING", description="Retailer tier: MAJOR, SECONDARY, REGIONAL, EMERGING"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED", description="ACTIVE, INACTIVE, TESTING"),
            bigquery.SchemaField("priority", "INTEGER", description="Extraction priority (1=highest)"),
            bigquery.SchemaField("max_plans_limit", "INTEGER", description="Max plans to extract per run"),
            bigquery.SchemaField("extraction_enabled", "BOOLEAN", mode="REQUIRED", description="Enable/disable extraction"),
            bigquery.SchemaField("notes", "STRING", description="Additional notes about retailer"),
            bigquery.SchemaField("date_added", "TIMESTAMP", mode="REQUIRED", description="When retailer was added"),
            bigquery.SchemaField("last_successful_extraction", "TIMESTAMP", description="Last successful extraction"),
            bigquery.SchemaField("last_extraction_attempt", "TIMESTAMP", description="Last extraction attempt"),
            bigquery.SchemaField("extraction_success_rate", "FLOAT", description="Success rate percentage"),
            bigquery.SchemaField("total_plans_extracted", "INTEGER", description="Total plans extracted historically"),
            bigquery.SchemaField("avg_extraction_time_seconds", "FLOAT", description="Average extraction time"),
            bigquery.SchemaField("geographic_coverage", "STRING", description="States/regions covered"),
            bigquery.SchemaField("fuel_types", "STRING", description="ELECTRICITY, GAS, DUAL"),
            bigquery.SchemaField("customer_types", "STRING", description="RESIDENTIAL, BUSINESS, BOTH"),
            bigquery.SchemaField("created_by", "STRING", description="Who added this retailer"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", description="Last update timestamp")
        ]
        
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{self.table_id}"
        
        try:
            self.client.get_table(table_ref)
            logger.info(f"Retailer registry table already exists")
        except:
            table = bigquery.Table(table_ref, schema=schema)
            # Add clustering for better query performance
            table.clustering_fields = ["tier", "status", "priority"]
            
            table = self.client.create_table(table)
            logger.info(f"Created retailer registry table: {table_ref}")
    
    def populate_initial_retailer_data(self, force_update=False):
        """
        Populate the table with initial retailer data
        
        Args:
            force_update (bool): If True, updates existing retailers with new data
                               If False, only adds new retailers (default)
        """
        
        # Initial retailer data with comprehensive information
        initial_retailers = [
            # Tier 1: Major National Retailers
            {"retailer_id": "agl", "retailer_name": "AGL", "tier": "MAJOR", "priority": 1, "max_plans_limit": 2000, "geographic_coverage": "ALL_STATES", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "origin", "retailer_name": "Origin Energy", "tier": "MAJOR", "priority": 1, "max_plans_limit": 2000, "geographic_coverage": "ALL_STATES", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "energyaustralia", "retailer_name": "EnergyAustralia", "tier": "MAJOR", "priority": 1, "max_plans_limit": 1800, "geographic_coverage": "ALL_STATES", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "alinta", "retailer_name": "Alinta", "tier": "MAJOR", "priority": 2, "max_plans_limit": 1200, "geographic_coverage": "ALL_STATES", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "red-energy", "retailer_name": "Red Energy", "tier": "MAJOR", "priority": 2, "max_plans_limit": 1000, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            
            # Tier 2: Secondary Major
            {"retailer_id": "lumo", "retailer_name": "Lumo Energy", "tier": "SECONDARY", "priority": 3, "max_plans_limit": 800, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "momentum", "retailer_name": "Momentum Energy", "tier": "SECONDARY", "priority": 3, "max_plans_limit": 800, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "powershop", "retailer_name": "Powershop", "tier": "SECONDARY", "priority": 3, "max_plans_limit": 600, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "diamond", "retailer_name": "Diamond Energy", "tier": "SECONDARY", "priority": 4, "max_plans_limit": 500, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "dodo", "retailer_name": "Dodo Power & Gas", "tier": "SECONDARY", "priority": 4, "max_plans_limit": 500, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "amber", "retailer_name": "Amber Electric", "tier": "SECONDARY", "priority": 4, "max_plans_limit": 300, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "nectr", "retailer_name": "Nectr", "tier": "SECONDARY", "priority": 4, "max_plans_limit": 300, "geographic_coverage": "NSW,QLD", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "ovo-energy", "retailer_name": "OVO Energy", "tier": "SECONDARY", "priority": 5, "max_plans_limit": 500, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "shell-energy", "retailer_name": "Shell Energy", "tier": "SECONDARY", "priority": 5, "max_plans_limit": 600, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "globird", "retailer_name": "GloBird Energy", "tier": "SECONDARY", "priority": 5, "max_plans_limit": 500, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            
            # High-Priority Missing Retailers
            {"retailer_id": "kogan", "retailer_name": "Kogan Energy", "tier": "SECONDARY", "priority": 3, "max_plans_limit": 400, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "coles", "retailer_name": "Coles Energy", "tier": "SECONDARY", "priority": 3, "max_plans_limit": 400, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "tesla", "retailer_name": "Tesla Energy Ventures", "tier": "SECONDARY", "priority": 4, "max_plans_limit": 200, "geographic_coverage": "NSW,VIC,QLD,SA", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            
            # Tier 3: Regional
            {"retailer_id": "ergon", "retailer_name": "Ergon Energy", "tier": "REGIONAL", "priority": 6, "max_plans_limit": 300, "geographic_coverage": "QLD", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "aurora", "retailer_name": "Aurora Energy", "tier": "REGIONAL", "priority": 6, "max_plans_limit": 300, "geographic_coverage": "TAS", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "stanwell", "retailer_name": "Stanwell Energy", "tier": "REGIONAL", "priority": 6, "max_plans_limit": 250, "geographic_coverage": "QLD", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "engie", "retailer_name": "ENGIE", "tier": "REGIONAL", "priority": 7, "max_plans_limit": 400, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "cleanco", "retailer_name": "CleanCo Queensland", "tier": "REGIONAL", "priority": 7, "max_plans_limit": 250, "geographic_coverage": "QLD", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "actewagl", "retailer_name": "ActewAGL", "tier": "REGIONAL", "priority": 7, "max_plans_limit": 300, "geographic_coverage": "ACT,NSW", "fuel_types": "DUAL", "customer_types": "BOTH"},
            
            # Recently Added Retailers (2024-2025)
            {"retailer_id": "savant", "retailer_name": "Savant Energy", "tier": "EMERGING", "priority": 8, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH", "notes": "Added Feb 2025"},
            {"retailer_id": "flipped", "retailer_name": "Flipped Energy", "tier": "EMERGING", "priority": 8, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL", "notes": "Added Oct 2024"},
            {"retailer_id": "perpetual", "retailer_name": "Perpetual Energy", "tier": "EMERGING", "priority": 8, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH", "notes": "Added Nov 2024"},
            {"retailer_id": "macarthur", "retailer_name": "Macarthur Energy Retail", "tier": "EMERGING", "priority": 8, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH", "notes": "Added Oct 2024"},
            
            # Tier 4: Emerging/Smaller
            {"retailer_id": "1st-energy", "retailer_name": "1st Energy", "tier": "EMERGING", "priority": 8, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "active-utilities", "retailer_name": "Active Utilities Retail", "tier": "EMERGING", "priority": 8, "max_plans_limit": 150, "geographic_coverage": "VIC", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "altogether", "retailer_name": "Altogether", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "ampol", "retailer_name": "Ampol Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "NSW,QLD", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "brighte", "retailer_name": "Brighte Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 100, "geographic_coverage": "NSW,VIC", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "circular", "retailer_name": "Circular Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "energy-locals", "retailer_name": "Energy Locals", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "NSW,VIC,QLD", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "localvolts", "retailer_name": "Localvolts", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "NSW,VIC", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "zen-energy", "retailer_name": "ZEN Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "SA", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            
            # Other Notable Retailers
            {"retailer_id": "people-energy", "retailer_name": "People Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "reamped", "retailer_name": "ReAmped Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "tango", "retailer_name": "Tango Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "sanctuary", "retailer_name": "Sanctuary Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "seene", "retailer_name": "Seene", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            
            # Business Focused
            {"retailer_id": "next-business", "retailer_name": "Next Business Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 200, "geographic_coverage": "VIC,NSW,QLD", "fuel_types": "DUAL", "customer_types": "BUSINESS"},
            {"retailer_id": "flow-power", "retailer_name": "Flow Power", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "ELECTRICITY", "customer_types": "BUSINESS"},
            {"retailer_id": "powerdirect", "retailer_name": "Powerdirect", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            
            # Technology/Innovation Focused
            {"retailer_id": "sonnen", "retailer_name": "Sonnen", "tier": "EMERGING", "priority": 10, "max_plans_limit": 50, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "smart-energy", "retailer_name": "Smart Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            
            # Additional AER Listed Retailers
            {"retailer_id": "arc-energy", "retailer_name": "Arc Energy Group", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "WA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "arcline", "retailer_name": "ARCLINE by RACV", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC", "fuel_types": "DUAL", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "arcstream", "retailer_name": "Arcstream", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "besy", "retailer_name": "Besy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 50, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "blue-nrg", "retailer_name": "Blue NRG", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "cleanpeak", "retailer_name": "CleanPeak Energy Retail", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "cooperative", "retailer_name": "Cooperative Power", "tier": "EMERGING", "priority": 9, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "covau", "retailer_name": "CovaU", "tier": "EMERGING", "priority": 10, "max_plans_limit": 50, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "cpe-mascot", "retailer_name": "CPE Mascot", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "discover", "retailer_name": "Discover Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "electricity-in-a-box", "retailer_name": "Electricity in a Box", "tier": "EMERGING", "priority": 10, "max_plans_limit": 50, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "ea-connect", "retailer_name": "Ellis Air Connect", "tier": "EMERGING", "priority": 10, "max_plans_limit": 50, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "evergy", "retailer_name": "Evergy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "flow-systems", "retailer_name": "Flow Systems", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BUSINESS"},
            {"retailer_id": "future-x", "retailer_name": "Future X Power", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "gee-energy", "retailer_name": "GEE Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "glow-power", "retailer_name": "Glow Power", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "humenergy", "retailer_name": "Humenergy Group", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "igeno", "retailer_name": "iGENO", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "indigo", "retailer_name": "Indigo Power", "tier": "EMERGING", "priority": 9, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "io-energy", "retailer_name": "iO Energy Retail Services", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "locality-planning", "retailer_name": "Locality Planning Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 50, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "macquarie", "retailer_name": "Macquarie", "tier": "EMERGING", "priority": 9, "max_plans_limit": 200, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BUSINESS"},
            {"retailer_id": "metered-energy", "retailer_name": "Metered Energy Holdings", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "microgrid", "retailer_name": "Microgrid Power", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "myob", "retailer_name": "MYOB powered by OVO", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BUSINESS"},
            {"retailer_id": "pacific-blue", "retailer_name": "Pacific Blue Retail", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "powerhub", "retailer_name": "PowerHub", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "powow", "retailer_name": "Powow Power", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "raa", "retailer_name": "RAA Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 100, "geographic_coverage": "SA", "fuel_types": "ELECTRICITY", "customer_types": "RESIDENTIAL"},
            {"retailer_id": "radian", "retailer_name": "Radian Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "real-utilities", "retailer_name": "Real Utilities", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "smartestenergy", "retailer_name": "SmartestEnergy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW,QLD", "fuel_types": "ELECTRICITY", "customer_types": "BUSINESS"},
            {"retailer_id": "solstice", "retailer_name": "Solstice Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "sumo-gas", "retailer_name": "Sumo", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "GAS", "customer_types": "BOTH"},
            {"retailer_id": "sumo-power", "retailer_name": "Sumo", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"},
            {"retailer_id": "telstra-energy", "retailer_name": "Telstra Energy", "tier": "EMERGING", "priority": 9, "max_plans_limit": 150, "geographic_coverage": "VIC,NSW,QLD,SA", "fuel_types": "DUAL", "customer_types": "BOTH"},
            {"retailer_id": "yes-energy", "retailer_name": "YES Energy", "tier": "EMERGING", "priority": 10, "max_plans_limit": 100, "geographic_coverage": "VIC,NSW", "fuel_types": "ELECTRICITY", "customer_types": "BOTH"}
        ]
        
        table_ref = f"{PROJECT_ID}.{DATASET_ID}.{self.table_id}"
        
        # Get existing retailer IDs
        try:
            existing_query = f"SELECT retailer_id FROM `{table_ref}`"
            existing_df = self.client.query(existing_query).to_dataframe()
            existing_ids = set(existing_df['retailer_id'].tolist()) if not existing_df.empty else set()
            logger.info(f"Found {len(existing_ids)} existing retailers in registry")
        except Exception as e:
            logger.info(f"No existing data found (this is normal for first run): {e}")
            existing_ids = set()
        
        # Add common fields and filter for new/updated retailers
        current_time = datetime.utcnow()
        new_retailers = []
        updated_retailers = []
        
        for retailer in initial_retailers:
            retailer.update({
                "api_endpoint": retailer["retailer_id"],  # Most use retailer_id as endpoint
                "status": "ACTIVE",
                "extraction_enabled": True,
                "notes": retailer.get("notes", f"Auto-generated entry for {retailer['retailer_name']}"),
                "updated_at": current_time
            })
            
            if retailer["retailer_id"] in existing_ids:
                if force_update:
                    updated_retailers.append(retailer)
                # Skip if exists and not forcing update
            else:
                # New retailer
                retailer["date_added"] = current_time
                retailer["created_by"] = "system_initialization"
                new_retailers.append(retailer)
        
        # Handle new retailers
        if new_retailers:
            logger.info(f"Adding {len(new_retailers)} new retailers: {[r['retailer_id'] for r in new_retailers]}")
            df_new = pd.DataFrame(new_retailers)
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            
            job = self.client.load_table_from_dataframe(df_new, table_ref, job_config=job_config)
            job.result()
            logger.info(f"Successfully added {len(new_retailers)} new retailers")
        
        # Handle updated retailers (if force_update=True)
        if updated_retailers:
            logger.info(f"Updating {len(updated_retailers)} existing retailers")
            
            for retailer in updated_retailers:
                # Update existing retailer with new data (preserve original date_added and created_by)
                update_query = f"""
                UPDATE `{table_ref}`
                SET 
                    retailer_name = '{retailer['retailer_name']}',
                    tier = '{retailer['tier']}',
                    priority = {retailer['priority']},
                    max_plans_limit = {retailer['max_plans_limit']},
                    geographic_coverage = '{retailer['geographic_coverage']}',
                    fuel_types = '{retailer['fuel_types']}',
                    customer_types = '{retailer['customer_types']}',
                    api_endpoint = '{retailer['api_endpoint']}',
                    status = '{retailer['status']}',
                    extraction_enabled = {retailer['extraction_enabled']},
                    notes = '{retailer['notes']}',
                    updated_at = CURRENT_TIMESTAMP()
                WHERE retailer_id = '{retailer['retailer_id']}'
                """
                
                self.client.query(update_query).result()
            
            logger.info(f"Successfully updated {len(updated_retailers)} retailers")
        
        # Get final count
        final_count_query = f"SELECT COUNT(*) as count FROM `{table_ref}`"
        final_result = self.client.query(final_count_query).to_dataframe()
        final_count = final_result['count'].iloc[0]
        
        logger.info(f"Registry now contains {final_count} total retailers")
        logger.info(f"Added: {len(new_retailers)}, Updated: {len(updated_retailers)}, Skipped: {len(initial_retailers) - len(new_retailers) - len(updated_retailers)}")
        
        return {
            'total_count': final_count,
            'new_added': len(new_retailers),
            'updated': len(updated_retailers),
            'skipped': len(initial_retailers) - len(new_retailers) - len(updated_retailers)
        }
    
    def get_active_retailers(self, tier_filter=None, max_retailers=None) -> list:
        """Get list of active retailers for extraction"""
        
        where_conditions = ["status = 'ACTIVE'", "extraction_enabled = TRUE"]
        
        if tier_filter:
            if isinstance(tier_filter, list):
                tier_list = "', '".join(tier_filter)
                where_conditions.append(f"tier IN ('{tier_list}')")
            else:
                where_conditions.append(f"tier = '{tier_filter}'")
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
        SELECT 
            retailer_id,
            retailer_name,
            tier,
            priority,
            max_plans_limit,
            api_endpoint
        FROM `{PROJECT_ID}.{DATASET_ID}.{self.table_id}`
        WHERE {where_clause}
        ORDER BY priority ASC, tier ASC, retailer_name ASC
        """
        
        if max_retailers:
            query += f" LIMIT {max_retailers}"
        
        result = self.client.query(query).to_dataframe()
        return result['retailer_id'].tolist()
    
    def update_extraction_stats(self, retailer_id: str, success: bool, 
                              plans_extracted: int = 0, extraction_time: float = 0):
        """Update extraction statistics for a retailer"""
        
        update_query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{self.table_id}`
        SET 
            last_extraction_attempt = CURRENT_TIMESTAMP(),
            {f"last_successful_extraction = CURRENT_TIMESTAMP()," if success else ""}
            total_plans_extracted = COALESCE(total_plans_extracted, 0) + {plans_extracted},
            avg_extraction_time_seconds = COALESCE(avg_extraction_time_seconds, 0) + {extraction_time},
            updated_at = CURRENT_TIMESTAMP()
        WHERE retailer_id = '{retailer_id}'
        """
        
        self.client.query(update_query).result()
        logger.info(f"Updated extraction stats for {retailer_id}: success={success}, plans={plans_extracted}")
    
    def retailer_exists(self, retailer_id: str) -> bool:
        """Check if a retailer already exists in the registry"""
        query = f"""
        SELECT COUNT(*) as count 
        FROM `{PROJECT_ID}.{DATASET_ID}.{self.table_id}` 
        WHERE retailer_id = '{retailer_id}'
        """
        result = self.client.query(query).to_dataframe()
        return result['count'].iloc[0] > 0

    def add_new_retailer(self, retailer_data: dict, skip_if_exists=True):
        """
        Add a new retailer to the registry
        
        Args:
            retailer_data (dict): Retailer information
            skip_if_exists (bool): If True, skip if retailer already exists
                                  If False, update existing retailer
        """
        
        if skip_if_exists and self.retailer_exists(retailer_data['retailer_id']):
            logger.info(f"Retailer {retailer_data['retailer_id']} already exists, skipping")
            return False
        
        # Set defaults
        retailer_data.update({
            "date_added": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "status": retailer_data.get("status", "ACTIVE"),
            "extraction_enabled": retailer_data.get("extraction_enabled", True),
            "priority": retailer_data.get("priority", 10),
            "max_plans_limit": retailer_data.get("max_plans_limit", 100),
            "api_endpoint": retailer_data.get("api_endpoint", retailer_data['retailer_id']),
            "created_by": retailer_data.get("created_by", "manual_addition")
        })
        
        if self.retailer_exists(retailer_data['retailer_id']) and not skip_if_exists:
            # Update existing retailer
            self.update_retailer(retailer_data['retailer_id'], retailer_data)
            logger.info(f"Updated retailer: {retailer_data['retailer_id']}")
        else:
            # Insert new retailer
            df = pd.DataFrame([retailer_data])
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{self.table_id}"
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_APPEND
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()
            
            logger.info(f"Added new retailer: {retailer_data['retailer_id']}")
        
        return True

    def update_retailer(self, retailer_id: str, update_data: dict):
        """Update an existing retailer's information"""
        
        # Build SET clause dynamically
        set_clauses = []
        for key, value in update_data.items():
            if key not in ['retailer_id', 'date_added', 'created_by']:  # Don't update these
                if isinstance(value, str):
                    set_clauses.append(f"{key} = '{value}'")
                elif isinstance(value, bool):
                    set_clauses.append(f"{key} = {value}")
                elif value is None:
                    set_clauses.append(f"{key} = NULL")
                else:
                    set_clauses.append(f"{key} = {value}")
        
        set_clauses.append("updated_at = CURRENT_TIMESTAMP()")
        
        update_query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{self.table_id}`
        SET {', '.join(set_clauses)}
        WHERE retailer_id = '{retailer_id}'
        """
        
        self.client.query(update_query).result()
        logger.info(f"Updated retailer {retailer_id}")

    def disable_retailer(self, retailer_id: str, reason: str = "Manually disabled"):
        """Disable a retailer from extraction"""
        
        update_query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{self.table_id}`
        SET 
            extraction_enabled = FALSE,
            notes = CONCAT(COALESCE(notes, ''), ' | Disabled: {reason}'),
            updated_at = CURRENT_TIMESTAMP()
        WHERE retailer_id = '{retailer_id}'
        """
        
        self.client.query(update_query).result()
        logger.info(f"Disabled retailer {retailer_id}: {reason}")
    
    def get_retailer_performance_report(self):
        """Get performance report for all retailers"""
        
        query = f"""
        SELECT 
            retailer_id,
            retailer_name,
            tier,
            status,
            extraction_enabled,
            COALESCE(total_plans_extracted, 0) as total_plans_extracted,
            last_successful_extraction,
            CASE 
                WHEN last_successful_extraction IS NULL THEN NULL
                ELSE DATETIME_DIFF(CURRENT_DATETIME(), DATETIME(last_successful_extraction), DAY) 
            END as days_since_last_success,
            COALESCE(extraction_success_rate, 0.0) as extraction_success_rate,
            COALESCE(avg_extraction_time_seconds, 0.0) as avg_extraction_time_seconds,
            priority,
            max_plans_limit,
            geographic_coverage,
            fuel_types,
            customer_types
        FROM `{PROJECT_ID}.{DATASET_ID}.{self.table_id}`
        ORDER BY tier, priority, retailer_name
        """
        
        return self.client.query(query).to_dataframe()

    def get_retailer_summary(self):
        """Get a quick summary of the retailer registry"""
        query = f"""
        SELECT 
            tier,
            COUNT(*) as total_retailers,
            SUM(CASE WHEN extraction_enabled = TRUE THEN 1 ELSE 0 END) as active_retailers,
            SUM(CASE WHEN status = 'ACTIVE' THEN 1 ELSE 0 END) as status_active,
            AVG(max_plans_limit) as avg_max_plans
        FROM `{PROJECT_ID}.{DATASET_ID}.{self.table_id}`
        GROUP BY tier
        ORDER BY 
            CASE tier 
                WHEN 'MAJOR' THEN 1 
                WHEN 'SECONDARY' THEN 2 
                WHEN 'REGIONAL' THEN 3 
                WHEN 'EMERGING' THEN 4 
                ELSE 5 
            END
        """
        
        return self.client.query(query).to_dataframe()

def main():
    """Initialize and manage retailer registry"""
    registry = RetailerRegistry()
    
    print("🏗️ Setting up Retailer Registry...")
    
    # Create table
    registry.create_retailer_registry_table()
    
    # Populate initial data (with deduplication)
    result = registry.populate_initial_retailer_data(force_update=False)
    print(f"✅ Retailer registry ready with {result['total_count']} retailers")
    print(f"   📊 New: {result['new_added']}, Updated: {result['updated']}, Skipped: {result['skipped']}")
    
    # Show summary
    try:
        summary = registry.get_retailer_summary()
        print(f"\n📈 Registry Summary by Tier:")
        print(summary)
    except Exception as e:
        print(f"Error getting summary: {e}")
    
    # Test queries
    print(f"\n📊 Sample queries:")
    
    # Get major retailers only
    try:
        major_retailers = registry.get_active_retailers(tier_filter="MAJOR")
        print(f"Major retailers: {major_retailers}")
    except Exception as e:
        print(f"Error getting major retailers: {e}")
    
    # Get top 10 priority retailers
    try:
        top_retailers = registry.get_active_retailers(max_retailers=10)
        print(f"Top 10 priority retailers: {top_retailers}")
    except Exception as e:
        print(f"Error getting top retailers: {e}")

# Example of how to add a single new retailer
def add_single_retailer_example():
    """Example of adding a single retailer"""
    registry = RetailerRegistry()
    
    new_retailer = {
        "retailer_id": "example-energy",
        "retailer_name": "Example Energy",
        "tier": "EMERGING",
        "priority": 10,
        "max_plans_limit": 100,
        "geographic_coverage": "VIC,NSW",
        "fuel_types": "ELECTRICITY",
        "customer_types": "RESIDENTIAL",
        "notes": "Example retailer for testing"
    }
    
    success = registry.add_new_retailer(new_retailer, skip_if_exists=True)
    if success:
        print(f"Successfully added {new_retailer['retailer_id']}")
    else:
        print(f"Retailer {new_retailer['retailer_id']} already exists")

# Example of how to update extraction stats
def update_extraction_example():
    """Example of updating extraction statistics"""
    registry = RetailerRegistry()
    
    # Example: AGL extraction was successful, extracted 150 plans in 45 seconds
    registry.update_extraction_stats(
        retailer_id="agl",
        success=True,
        plans_extracted=150,
        extraction_time=45.2
    )
    
    # Example: Origin extraction failed
    registry.update_extraction_stats(
        retailer_id="origin",
        success=False,
        plans_extracted=0,
        extraction_time=12.5
    )

# Example of getting retailers for extraction
def get_retailers_for_extraction_example():
    """Example of getting retailers for different extraction scenarios"""
    registry = RetailerRegistry()
    
    # Get only major retailers for priority extraction
    major_retailers = registry.get_active_retailers(tier_filter="MAJOR")
    print(f"Major retailers for priority extraction: {major_retailers}")
    
    # Get top 20 retailers across all tiers
    top_20 = registry.get_active_retailers(max_retailers=20)
    print(f"Top 20 retailers by priority: {top_20}")
    
    # Get only secondary and regional retailers
    mid_tier = registry.get_active_retailers(tier_filter=["SECONDARY", "REGIONAL"])
    print(f"Secondary and Regional retailers: {mid_tier}")

if __name__ == "__main__":
    main()
    
    # Uncomment to test additional functionality
    # add_single_retailer_example()
    # update_extraction_example()
    # get_retailers_for_extraction_example()