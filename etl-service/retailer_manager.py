#!/usr/bin/env python3
"""
Retailer Management System for WattsMyBill ETL - Comprehensive Edition
Manages systematic extraction of comprehensive tariffs for each retailer
"""

import logging
from typing import List, Dict, Any
from google.cloud import bigquery
from datetime import datetime, timedelta
import os
import subprocess
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Use environment variable or fallback
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

class RetailerManager:
    """Manages systematic comprehensive tariff extraction for all retailers"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        logger.info(f"RetailerManager initialized for project: {PROJECT_ID} (Comprehensive Mode)")
        
        # Cache for retailer data
        self._all_retailers = None
        self._priority_retailers = None
    
    def get_all_retailers_from_registry(self) -> List[str]:
        """Get all active retailers from the retailer registry"""
        if self._all_retailers is not None:
            return self._all_retailers
            
        try:
            query = f"""
            SELECT retailer_id
            FROM `{PROJECT_ID}.{DATASET_ID}.retailer_registry`
            WHERE status = 'ACTIVE'
            ORDER BY retailer_id
            """
            result = self.client.query(query).to_dataframe()
            self._all_retailers = result['retailer_id'].tolist()
            logger.info(f"Loaded {len(self._all_retailers)} active retailers from registry")
            return self._all_retailers
        except Exception as e:
            logger.warning(f"Could not load retailers from registry: {e}")
            # Fallback to a minimal list of major retailers
            fallback_retailers = [
                "agl", "origin", "energyaustralia", "alinta", "red-energy",
                "lumo", "momentum", "powershop", "diamond", "dodo", "amber",
                "nectr", "ovo-energy", "shell-energy", "globird"
            ]
            logger.info(f"Using fallback retailer list: {len(fallback_retailers)} retailers")
            return fallback_retailers
    
    def get_priority_retailers_from_registry(self) -> List[str]:
        """Get priority retailers from the retailer registry"""
        if self._priority_retailers is not None:
            return self._priority_retailers
            
        try:
            query = f"""
            SELECT retailer_id
            FROM `{PROJECT_ID}.{DATASET_ID}.retailer_registry`
            WHERE status = 'ACTIVE' 
            AND tier IN ('MAJOR', 'SECONDARY')
            ORDER BY 
                CASE 
                    WHEN tier = 'MAJOR' THEN 1
                    WHEN tier = 'SECONDARY' THEN 2
                    ELSE 3
                END,
                priority ASC,
                retailer_id
            """
            result = self.client.query(query).to_dataframe()
            self._priority_retailers = result['retailer_id'].tolist()
            logger.info(f"Loaded {len(self._priority_retailers)} priority retailers from registry")
            return self._priority_retailers
        except Exception as e:
            logger.warning(f"Could not load priority retailers from registry: {e}")
            # Fallback to major retailers
            fallback_priority = [
                "agl", "origin", "energyaustralia", "alinta", "red-energy",
                "lumo", "momentum", "powershop", "diamond", "dodo"
            ]
            return fallback_priority
    
    def get_retailer_info_from_registry(self, retailer_id: str) -> Dict[str, Any]:
        """Get detailed retailer information from registry"""
        try:
            query = f"""
            SELECT 
                retailer_id,
                retailer_name,
                tier,
                priority,
                max_plans_limit,
                total_plans_extracted,
                extraction_success_rate,
                last_successful_extraction
            FROM `{PROJECT_ID}.{DATASET_ID}.retailer_registry`
            WHERE retailer_id = '{retailer_id}'
            """
            result = self.client.query(query).to_dataframe()
            if not result.empty:
                return result.iloc[0].to_dict()
            else:
                return {
                    "retailer_id": retailer_id,
                    "retailer_name": retailer_id.title(),
                    "tier": "UNKNOWN",
                    "priority": 99,
                    "max_plans_limit": 100
                }
        except Exception as e:
            logger.warning(f"Could not get retailer info for {retailer_id}: {e}")
            return {
                "retailer_id": retailer_id,
                "retailer_name": retailer_id.title(),
                "tier": "UNKNOWN",
                "priority": 99,
                "max_plans_limit": 100
            }
    
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
    
    def get_retailer_comprehensive_status(self) -> List[Dict[str, Any]]:
        """Check which retailers have comprehensive tariff data extracted"""
        query = f"""
        WITH plan_counts AS (
            SELECT 
                retailer,
                COUNT(*) as total_plans
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
            WHERE (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
            GROUP BY retailer
        ),
        comprehensive_counts AS (
            SELECT 
                p.retailer,
                COUNT(DISTINCT c.plan_id) as plans_with_comprehensive,
                COUNT(c.plan_id) as total_contract_records,
                MAX(c.extracted_at) as last_comprehensive_extraction
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple` p
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.plan_contract_details` c ON p.plan_id = c.plan_id
            GROUP BY p.retailer
        ),
        tariff_rates_counts AS (
            SELECT 
                p.retailer,
                COUNT(DISTINCT r.plan_id) as plans_with_rates,
                COUNT(r.plan_id) as total_rate_records
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple` p
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive` r ON p.plan_id = r.plan_id
            GROUP BY p.retailer
        )
        SELECT 
            pc.retailer,
            pc.total_plans,
            COALESCE(cc.plans_with_comprehensive, 0) as plans_with_comprehensive,
            COALESCE(cc.total_contract_records, 0) as total_contract_records,
            COALESCE(rc.plans_with_rates, 0) as plans_with_comprehensive_rates,
            COALESCE(rc.total_rate_records, 0) as total_comprehensive_rate_records,
            cc.last_comprehensive_extraction,
            ROUND(COALESCE(cc.plans_with_comprehensive, 0) * 100.0 / pc.total_plans, 1) as comprehensive_coverage_percent
        FROM plan_counts pc
        LEFT JOIN comprehensive_counts cc ON pc.retailer = cc.retailer
        LEFT JOIN tariff_rates_counts rc ON pc.retailer = rc.retailer
        ORDER BY comprehensive_coverage_percent ASC, pc.total_plans DESC
        """
        
        result = self.client.query(query).to_dataframe()
        return result.to_dict('records')
    
    # Legacy method for backward compatibility
    def get_retailer_tariff_status(self) -> List[Dict[str, Any]]:
        """Legacy method - redirects to comprehensive status"""
        return self.get_retailer_comprehensive_status()
    
    def get_next_retailers_to_process_comprehensive(self, limit: int = 5) -> List[str]:
        """Get the next retailers that need comprehensive tariff extraction"""
        status = self.get_retailer_comprehensive_status()
        priority_retailers = self.get_priority_retailers_from_registry()
        
        # Prioritize retailers with:
        # 1. Low comprehensive coverage
        # 2. High plan counts
        # 3. Priority retailers from registry
        
        next_retailers = []
        
        for retailer_info in status:
            retailer = retailer_info['retailer']
            coverage = retailer_info['comprehensive_coverage_percent']
            plan_count = retailer_info['total_plans']
            
            # Skip if already well covered (>80%) unless it's a priority retailer
            if coverage > 80 and retailer not in priority_retailers:
                continue
            
            # Skip if very few plans (<10)
            if plan_count < 10:
                continue
            
            next_retailers.append(retailer)
            
            if len(next_retailers) >= limit:
                break
        
        return next_retailers
    
    # Legacy method for backward compatibility
    def get_next_retailers_to_process(self, limit: int = 5) -> List[str]:
        """Legacy method - redirects to comprehensive processing"""
        return self.get_next_retailers_to_process_comprehensive(limit)
    
    def extract_comprehensive_tariffs_for_retailer(self, retailer: str, max_plans: int = None) -> Dict[str, Any]:
        """Extract comprehensive tariffs for a specific retailer using the new system"""
        logger.info(f"🔄 Starting comprehensive tariff extraction for {retailer}")
        
        try:
            # Get plans for this retailer that don't have comprehensive data
            plans_query = f"""
            SELECT p.plan_id, p.retailer, p.fuel_type
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple` p
            LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.plan_contract_details` c ON p.plan_id = c.plan_id
            WHERE p.retailer = '{retailer}'
            AND (p.effective_to IS NULL OR p.effective_to > CURRENT_TIMESTAMP())
            AND c.plan_id IS NULL  -- No comprehensive data yet
            ORDER BY p.extracted_at DESC
            """
            
            if max_plans:
                plans_query += f" LIMIT {max_plans}"
            
            result = self.client.query(plans_query).to_dataframe()
            
            if result.empty:
                return {
                    "status": "skipped",
                    "retailer": retailer,
                    "message": "No new plans to process for comprehensive extraction",
                    "plans_processed": 0
                }
            
            plans_count = len(result)
            logger.info(f"📊 Found {plans_count} plans to process for comprehensive extraction from {retailer}")
            
            # Use subprocess to call the comprehensive extraction script
            cmd = [
                sys.executable, 'extract_tariffs_comprehensive.py',
                '--retailer', retailer,
                '--batch-size', '15'  # Smaller batches for comprehensive extraction
            ]
            
            if max_plans:
                # The script will naturally limit based on available plans
                pass
            
            # Run the comprehensive extraction
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
            
            if result.returncode == 0:
                # Get extraction results
                stats_query = f"""
                SELECT 
                    COUNT(DISTINCT c.plan_id) as plans_with_comprehensive,
                    COUNT(c.plan_id) as total_contract_records,
                    COUNT(DISTINCT r.plan_id) as plans_with_rates,
                    COUNT(r.plan_id) as total_rate_records
                FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details` c
                LEFT JOIN `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive` r ON c.plan_id = r.plan_id
                WHERE c.retailer = '{retailer}'
                AND DATE(c.extracted_at) = CURRENT_DATE()
                """
                
                stats_result = self.client.query(stats_query).to_dataframe()
                extraction_stats = stats_result.iloc[0].to_dict() if not stats_result.empty else {}
                
                return {
                    "status": "success",
                    "retailer": retailer,
                    "plans_available": plans_count,
                    "plans_with_comprehensive": extraction_stats.get('plans_with_comprehensive', 0),
                    "total_contract_records": extraction_stats.get('total_contract_records', 0),
                    "plans_with_rates": extraction_stats.get('plans_with_rates', 0),
                    "total_rate_records": extraction_stats.get('total_rate_records', 0),
                    "timestamp": datetime.utcnow().isoformat(),
                    "extraction_log": result.stdout[-500:] if result.stdout else ""
                }
            else:
                return {
                    "status": "error",
                    "retailer": retailer,
                    "error": result.stderr[-500:] if result.stderr else "Unknown extraction error",
                    "extraction_log": result.stdout[-500:] if result.stdout else "",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Comprehensive extraction timed out for {retailer}")
            return {
                "status": "error",
                "retailer": retailer,
                "error": "Extraction timed out (>1 hour)",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Failed to extract comprehensive tariffs for {retailer}: {e}")
            return {
                "status": "error",
                "retailer": retailer,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Legacy method for backward compatibility - now uses comprehensive extraction
    def extract_tariffs_for_retailer(self, retailer: str, max_plans: int = None) -> Dict[str, Any]:
        """Legacy method - redirects to comprehensive extraction"""
        return self.extract_comprehensive_tariffs_for_retailer(retailer, max_plans)
    
    def run_systematic_comprehensive_extraction(self, retailers_per_run: int = 2, max_plans_per_retailer: int = 50):
        """Run systematic comprehensive extraction across multiple retailers"""
        logger.info(f"🚀 Starting systematic comprehensive tariff extraction")
        
        # Get next retailers to process
        next_retailers = self.get_next_retailers_to_process_comprehensive(retailers_per_run)
        
        if not next_retailers:
            logger.info("✅ All retailers are up to date with comprehensive data!")
            return {
                "status": "complete",
                "message": "All retailers have adequate comprehensive tariff coverage",
                "retailers_processed": []
            }
        
        logger.info(f"📋 Processing retailers for comprehensive extraction: {', '.join(next_retailers)}")
        
        results = []
        
        for retailer in next_retailers:
            result = self.extract_comprehensive_tariffs_for_retailer(retailer, max_plans_per_retailer)
            results.append(result)
            
            # Log result
            if result['status'] == 'success':
                logger.info(f"✅ {retailer}: {result['plans_with_comprehensive']} plans with comprehensive data, {result['total_rate_records']} rate records")
            elif result['status'] == 'error':
                logger.error(f"❌ {retailer}: {result['error']}")
            else:
                logger.info(f"⏭️ {retailer}: {result['message']}")
        
        return {
            "status": "completed",
            "extraction_type": "comprehensive",
            "retailers_processed": len(next_retailers),
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Legacy method for backward compatibility
    def run_systematic_extraction(self, retailers_per_run: int = 2, max_plans_per_retailer: int = 50):
        """Legacy method - redirects to comprehensive extraction"""
        return self.run_systematic_comprehensive_extraction(retailers_per_run, max_plans_per_retailer)
    
    def get_extraction_report(self) -> Dict[str, Any]:
        """Generate a comprehensive extraction status report"""
        retailers_status = self.get_retailer_comprehensive_status()
        
        # Calculate overall stats
        total_plans = sum(r['total_plans'] for r in retailers_status)
        total_with_comprehensive = sum(r['plans_with_comprehensive'] for r in retailers_status)
        overall_coverage = (total_with_comprehensive / total_plans * 100) if total_plans > 0 else 0
        
        # Categorize retailers
        good_coverage = [r for r in retailers_status if r['comprehensive_coverage_percent'] >= 80]
        medium_coverage = [r for r in retailers_status if 20 <= r['comprehensive_coverage_percent'] < 80]
        low_coverage = [r for r in retailers_status if r['comprehensive_coverage_percent'] < 20]
        
        # Get retailer tier breakdown
        tier_breakdown = {}
        priority_retailers = self.get_priority_retailers_from_registry()
        
        for retailer_info in retailers_status:
            retailer_id = retailer_info['retailer']
            registry_info = self.get_retailer_info_from_registry(retailer_id)
            tier = registry_info.get('tier', 'UNKNOWN')
            
            if tier not in tier_breakdown:
                tier_breakdown[tier] = {
                    "total_retailers": 0,
                    "good_coverage": 0,
                    "medium_coverage": 0,
                    "low_coverage": 0
                }
            
            tier_breakdown[tier]["total_retailers"] += 1
            if retailer_info['comprehensive_coverage_percent'] >= 80:
                tier_breakdown[tier]["good_coverage"] += 1
            elif retailer_info['comprehensive_coverage_percent'] >= 20:
                tier_breakdown[tier]["medium_coverage"] += 1
            else:
                tier_breakdown[tier]["low_coverage"] += 1
        
        # Get data freshness
        freshness_query = f"""
        SELECT 
            COUNT(DISTINCT DATE(extracted_at)) as extraction_days,
            MAX(extracted_at) as latest_extraction,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(extracted_at), HOUR) as hours_since_latest
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
        WHERE DATE(extracted_at) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        """
        
        try:
            freshness_result = self.client.query(freshness_query).to_dataframe()
            freshness_data = freshness_result.iloc[0].to_dict() if not freshness_result.empty else {}
        except:
            freshness_data = {}
        
        return {
            "overall_stats": {
                "total_retailers": len(retailers_status),
                "total_plans": total_plans,
                "plans_with_comprehensive": total_with_comprehensive,
                "overall_comprehensive_coverage_percent": round(overall_coverage, 1),
                "extraction_type": "comprehensive",
                "data_freshness_hours": freshness_data.get('hours_since_latest', 'unknown'),
                "priority_retailers_count": len(priority_retailers)
            },
            "coverage_breakdown": {
                "good_coverage_80_plus": len(good_coverage),
                "medium_coverage_20_80": len(medium_coverage),
                "low_coverage_under_20": len(low_coverage)
            },
            "tier_breakdown": tier_breakdown,
            "retailers_needing_attention": [
                {
                    "retailer": r['retailer'],
                    "total_plans": r['total_plans'],
                    "comprehensive_coverage_percent": r['comprehensive_coverage_percent'],
                    "plans_with_comprehensive": r['plans_with_comprehensive'],
                    "tier": self.get_retailer_info_from_registry(r['retailer']).get('tier', 'UNKNOWN'),
                    "is_priority": r['retailer'] in priority_retailers
                }
                for r in low_coverage + medium_coverage
            ][:10],  # Top 10 that need attention
            "timestamp": datetime.utcnow().isoformat()
        }

def main():
    """Command line interface for retailer management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage comprehensive retailer tariff extraction")
    parser.add_argument("--status", action="store_true", help="Show retailer comprehensive status report")
    parser.add_argument("--extract", type=str, help="Extract comprehensive tariffs for specific retailer")
    parser.add_argument("--systematic", action="store_true", help="Run systematic comprehensive extraction")
    parser.add_argument("--next", type=int, default=3, help="Number of retailers to process in systematic mode")
    parser.add_argument("--max-plans", type=int, default=50, help="Max plans per retailer")
    
    args = parser.parse_args()
    
    manager = RetailerManager()
    
    if args.status:
        print("📊 Retailer Comprehensive Tariff Extraction Status Report")
        print("=" * 60)
        
        report = manager.get_extraction_report()
        
        print(f"Overall Comprehensive Coverage: {report['overall_stats']['overall_comprehensive_coverage_percent']}%")
        print(f"Total Plans: {report['overall_stats']['total_plans']:,}")
        print(f"Plans with Comprehensive Data: {report['overall_stats']['plans_with_comprehensive']:,}")
        print(f"Data Freshness: {report['overall_stats']['data_freshness_hours']} hours")
        print()
        
        print("Coverage Breakdown:")
        print(f"  Good (80%+): {report['coverage_breakdown']['good_coverage_80_plus']} retailers")
        print(f"  Medium (20-80%): {report['coverage_breakdown']['medium_coverage_20_80']} retailers")
        print(f"  Low (<20%): {report['coverage_breakdown']['low_coverage_under_20']} retailers")
        print()
        
        print("Retailers Needing Comprehensive Extraction:")
        for retailer in report['retailers_needing_attention']:
            print(f"  {retailer['retailer']}: {retailer['total_plans']} plans, {retailer['comprehensive_coverage_percent']}% coverage")
    
    elif args.extract:
        print(f"🔄 Extracting comprehensive tariffs for {args.extract}")
        result = manager.extract_comprehensive_tariffs_for_retailer(args.extract, args.max_plans)
        print(f"Result: {result}")
    
    elif args.systematic:
        print(f"🚀 Running systematic comprehensive extraction for {args.next} retailers")
        result = manager.run_systematic_comprehensive_extraction(args.next, args.max_plans)
        print(f"Completed: {result['retailers_processed']} retailers processed")
        
        for r in result['results']:
            status_emoji = "✅" if r['status'] == 'success' else "❌" if r['status'] == 'error' else "⏭️"
            if r['status'] == 'success':
                print(f"  {status_emoji} {r['retailer']}: {r['plans_with_comprehensive']} comprehensive plans")
            else:
                print(f"  {status_emoji} {r['retailer']}")
    
    else:
        print("Usage:")
        print("  python retailer_manager.py --status                    # Show comprehensive status report")
        print("  python retailer_manager.py --extract agl               # Extract comprehensive data for specific retailer") 
        print("  python retailer_manager.py --systematic                # Run systematic comprehensive extraction")
        print("  python retailer_manager.py --systematic --next 2       # Process 2 retailers")

if __name__ == "__main__":
    main()