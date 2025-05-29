#!/usr/bin/env python3
"""
Retailer Management System for WattsMyBill ETL
Manages systematic extraction of tariffs for each retailer
"""

import logging
from typing import List, Dict, Any
from google.cloud import bigquery
from datetime import datetime, timedelta
import extract_tariffs
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Use environment variable or fallback
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

class RetailerManager:
    """Manages systematic tariff extraction for all retailers"""
    
    # All retailers from the official AER list
    ALL_RETAILERS = [
        "1st-energy", "actewagl", "active-utilities", "agl", "alinta", "altogether",
        "amber", "ampol", "arc-energy", "arcline", "arcstream", "aurora", "besy",
        "blue-nrg", "brighte", "circular", "cleanco", "cleanpeak", "coles",
        "cooperative", "covau", "cpe-mascot", "diamond", "discover", "dodo",
        "electricity-in-a-box", "ea-connect", "energy-locals", "energyaustralia",
        "engie", "ergon", "evergy", "flipped", "flow-power", "flow-systems",
        "future-x", "gee-energy", "globird", "glow-power", "humenergy", "igeno",
        "indigo", "io-energy", "kogan", "locality-planning", "localvolts", "lumo",
        "macarthur", "macquarie", "metered-energy", "microgrid", "momentum",
        "myob", "nectr", "next-business", "origin", "ovo-energy", "pacific-blue",
        "people-energy", "perpetual", "powerdirect", "powerhub", "powershop",
        "powow", "raa", "radian", "real-utilities", "reamped", "red-energy",
        "sanctuary", "savant", "seene", "shell-energy", "smart-energy",
        "smartestenergy", "solstice", "sonnen", "stanwell", "sumo-gas",
        "sumo-power", "tango", "telstra-energy", "tesla", "yes-energy", "zen-energy"
    ]
    
    # Priority retailers (major ones to extract first)
    PRIORITY_RETAILERS = [
        "agl", "origin", "energyaustralia", "alinta", "red-energy",
        "lumo", "momentum", "powershop", "diamond", "dodo", "amber",
        "nectr", "ovo-energy", "shell-energy", "globird"
    ]
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        logger.info(f"RetailerManager initialized for project: {PROJECT_ID}")
    
    def get_retailers_with_plans(self) -> List[Dict[str, Any]]:
        """Get all retailers that have plans in the database with counts"""
        query = f"""
        SELECT 
            retailer,
            COUNT(*) as plan_count,
            COUNT(DISTINCT fuel_type) as fuel_types,
            MAX(extracted_at) as last_extracted
        FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
        WHERE (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
        GROUP BY retailer
        ORDER BY plan_count DESC
        """
        
        result = self.client.query(query).to_dataframe()
        return result.to_dict('records')
    
    def get_retailer_tariff_status(self) -> List[Dict[str, Any]]:
        """Check which retailers have tariff data extracted"""
        query = f"""
        WITH plan_counts AS (
            SELECT 
                retailer,
                COUNT(*) as total_plans
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
            WHERE (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
            GROUP BY retailer
        ),
        tariff_counts AS (
            SELECT 
                p.retailer,
                COUNT(DISTINCT r.plan_id) as plans_with_tariffs,
                COUNT(r.plan_id) as total_tariff_records,
                MAX(r.extracted_at) as last_tariff_extraction
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple` p
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.tariff_rates` r ON p.plan_id = r.plan_id
            GROUP BY p.retailer
        )
        SELECT 
            pc.retailer,
            pc.total_plans,
            COALESCE(tc.plans_with_tariffs, 0) as plans_with_tariffs,
            COALESCE(tc.total_tariff_records, 0) as total_tariff_records,
            tc.last_tariff_extraction,
            ROUND(COALESCE(tc.plans_with_tariffs, 0) * 100.0 / pc.total_plans, 1) as tariff_coverage_percent
        FROM plan_counts pc
        LEFT JOIN tariff_counts tc ON pc.retailer = tc.retailer
        ORDER BY tariff_coverage_percent ASC, pc.total_plans DESC
        """
        
        result = self.client.query(query).to_dataframe()
        return result.to_dict('records')
    
    def get_next_retailers_to_process(self, limit: int = 5) -> List[str]:
        """Get the next retailers that need tariff extraction"""
        status = self.get_retailer_tariff_status()
        
        # Prioritize retailers with:
        # 1. Low tariff coverage
        # 2. High plan counts
        # 3. Priority retailers
        
        next_retailers = []
        
        for retailer_info in status:
            retailer = retailer_info['retailer']
            coverage = retailer_info['tariff_coverage_percent']
            plan_count = retailer_info['total_plans']
            
            # Skip if already well covered (>80%) unless it's a priority retailer
            if coverage > 80 and retailer not in self.PRIORITY_RETAILERS:
                continue
            
            # Skip if very few plans (<10)
            if plan_count < 10:
                continue
            
            next_retailers.append(retailer)
            
            if len(next_retailers) >= limit:
                break
        
        return next_retailers
    
    def extract_tariffs_for_retailer(self, retailer: str, max_plans: int = None) -> Dict[str, Any]:
        """Extract tariffs for a specific retailer"""
        logger.info(f"🔄 Starting tariff extraction for {retailer}")
        
        try:
            # Get plans for this retailer
            plans_query = f"""
            SELECT plan_id, retailer
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
            WHERE retailer = '{retailer}'
            AND (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
            AND plan_id NOT IN (
                SELECT DISTINCT plan_id 
                FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates`
                WHERE plan_id IS NOT NULL
            )
            ORDER BY extracted_at DESC
            """
            
            if max_plans:
                plans_query += f" LIMIT {max_plans}"
            
            result = self.client.query(plans_query).to_dataframe()
            
            if result.empty:
                return {
                    "status": "skipped",
                    "retailer": retailer,
                    "message": "No new plans to process",
                    "plans_processed": 0
                }
            
            plans_to_process = list(zip(result['plan_id'], result['retailer']))
            logger.info(f"📊 Found {len(plans_to_process)} plans to process for {retailer}")
            
            # Setup tables
            extract_tariffs.create_tariff_tables()
            
            # Process in batches
            all_rates = []
            all_geography = []
            batch_size = 25
            
            for i in range(0, len(plans_to_process), batch_size):
                batch = plans_to_process[i:i + batch_size]
                batch_num = i//batch_size + 1
                total_batches = (len(plans_to_process) + batch_size - 1) // batch_size
                
                logger.info(f"Processing batch {batch_num}/{total_batches} for {retailer}")
                
                batch_rates, batch_geography = extract_tariffs.process_plan_batch(batch)
                all_rates.extend(batch_rates)
                all_geography.extend(batch_geography)
                
                # Load batch immediately
                if batch_rates or batch_geography:
                    extract_tariffs.load_to_bigquery(batch_rates, batch_geography)
            
            return {
                "status": "success",
                "retailer": retailer,
                "plans_processed": len(plans_to_process),
                "rates_extracted": len(all_rates),
                "geography_records": len(all_geography),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to extract tariffs for {retailer}: {e}")
            return {
                "status": "error",
                "retailer": retailer,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def run_systematic_extraction(self, retailers_per_run: int = 3, max_plans_per_retailer: int = 100):
        """Run systematic extraction across multiple retailers"""
        logger.info(f"🚀 Starting systematic tariff extraction")
        
        # Get next retailers to process
        next_retailers = self.get_next_retailers_to_process(retailers_per_run)
        
        if not next_retailers:
            logger.info("✅ All retailers are up to date!")
            return {
                "status": "complete",
                "message": "All retailers have adequate tariff coverage",
                "retailers_processed": []
            }
        
        logger.info(f"📋 Processing retailers: {', '.join(next_retailers)}")
        
        results = []
        
        for retailer in next_retailers:
            result = self.extract_tariffs_for_retailer(retailer, max_plans_per_retailer)
            results.append(result)
            
            # Log result
            if result['status'] == 'success':
                logger.info(f"✅ {retailer}: {result['plans_processed']} plans, {result['rates_extracted']} rates")
            elif result['status'] == 'error':
                logger.error(f"❌ {retailer}: {result['error']}")
            else:
                logger.info(f"⏭️ {retailer}: {result['message']}")
        
        return {
            "status": "completed",
            "retailers_processed": len(next_retailers),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def get_extraction_report(self) -> Dict[str, Any]:
        """Generate a comprehensive extraction status report"""
        retailers_status = self.get_retailer_tariff_status()
        
        # Calculate overall stats
        total_plans = sum(r['total_plans'] for r in retailers_status)
        total_with_tariffs = sum(r['plans_with_tariffs'] for r in retailers_status)
        overall_coverage = (total_with_tariffs / total_plans * 100) if total_plans > 0 else 0
        
        # Categorize retailers
        good_coverage = [r for r in retailers_status if r['tariff_coverage_percent'] >= 80]
        medium_coverage = [r for r in retailers_status if 20 <= r['tariff_coverage_percent'] < 80]
        low_coverage = [r for r in retailers_status if r['tariff_coverage_percent'] < 20]
        
        return {
            "overall_stats": {
                "total_retailers": len(retailers_status),
                "total_plans": total_plans,
                "plans_with_tariffs": total_with_tariffs,
                "overall_coverage_percent": round(overall_coverage, 1)
            },
            "coverage_breakdown": {
                "good_coverage_80_plus": len(good_coverage),
                "medium_coverage_20_80": len(medium_coverage),
                "low_coverage_under_20": len(low_coverage)
            },
            "retailers_needing_attention": [
                {
                    "retailer": r['retailer'],
                    "total_plans": r['total_plans'],
                    "coverage_percent": r['tariff_coverage_percent']
                }
                for r in low_coverage + medium_coverage
            ][:10],  # Top 10 that need attention
            "timestamp": datetime.utcnow().isoformat()
        }

def main():
    """Command line interface for retailer management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage retailer tariff extraction")
    parser.add_argument("--status", action="store_true", help="Show retailer status report")
    parser.add_argument("--extract", type=str, help="Extract tariffs for specific retailer")
    parser.add_argument("--systematic", action="store_true", help="Run systematic extraction")
    parser.add_argument("--next", type=int, default=5, help="Number of retailers to process in systematic mode")
    parser.add_argument("--max-plans", type=int, default=100, help="Max plans per retailer")
    
    args = parser.parse_args()
    
    manager = RetailerManager()
    
    if args.status:
        print("📊 Retailer Tariff Extraction Status Report")
        print("=" * 50)
        
        report = manager.get_extraction_report()
        
        print(f"Overall Coverage: {report['overall_stats']['overall_coverage_percent']}%")
        print(f"Total Plans: {report['overall_stats']['total_plans']:,}")
        print(f"Plans with Tariffs: {report['overall_stats']['plans_with_tariffs']:,}")
        print()
        
        print("Coverage Breakdown:")
        print(f"  Good (80%+): {report['coverage_breakdown']['good_coverage_80_plus']} retailers")
        print(f"  Medium (20-80%): {report['coverage_breakdown']['medium_coverage_20_80']} retailers")
        print(f"  Low (<20%): {report['coverage_breakdown']['low_coverage_under_20']} retailers")
        print()
        
        print("Retailers Needing Attention:")
        for retailer in report['retailers_needing_attention']:
            print(f"  {retailer['retailer']}: {retailer['total_plans']} plans, {retailer['coverage_percent']}% coverage")
    
    elif args.extract:
        print(f"🔄 Extracting tariffs for {args.extract}")
        result = manager.extract_tariffs_for_retailer(args.extract, args.max_plans)
        print(f"Result: {result}")
    
    elif args.systematic:
        print(f"🚀 Running systematic extraction for {args.next} retailers")
        result = manager.run_systematic_extraction(args.next, args.max_plans)
        print(f"Completed: {result['retailers_processed']} retailers processed")
        
        for r in result['results']:
            status_emoji = "✅" if r['status'] == 'success' else "❌" if r['status'] == 'error' else "⏭️"
            print(f"  {status_emoji} {r['retailer']}")
    
    else:
        print("Usage:")
        print("  python retailer_manager.py --status                    # Show status report")
        print("  python retailer_manager.py --extract agl               # Extract for specific retailer") 
        print("  python retailer_manager.py --systematic                # Run systematic extraction")
        print("  python retailer_manager.py --systematic --next 3       # Process 3 retailers")

if __name__ == "__main__":
    main()