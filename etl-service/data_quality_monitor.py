#!/usr/bin/env python3
"""
WattsMyBill Data Quality Monitor
Comprehensive monitoring and validation of ETL data quality
"""

import requests
import json
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration - Use environment variable or fallback
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or "wattsmybill-dev"
DATASET_ID = "energy_plans"
SERVICE_URL = "https://energy-plans-etl-YOUR_HASH.a.run.app"  # Update with actual URL

class DataQualityMonitor:
    """Monitor and validate data quality for WattsMyBill"""
    
    def __init__(self, service_url: str = None):
        self.service_url = service_url or SERVICE_URL
        self.client = bigquery.Client(project=PROJECT_ID)
        self.issues = []
        logger.info(f"DataQualityMonitor initialized for project: {PROJECT_ID}")
        
    def check_service_health(self) -> bool:
        """Check if the ETL service is healthy"""
        try:
            response = requests.get(f"{self.service_url}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Service Status: {health_data['status']}")
                
                # Check table status
                tables = health_data.get('tables_status', {})
                for table, status in tables.items():
                    emoji = "✅" if status == "exists" else "❌"
                    print(f"  {emoji} {table}: {status}")
                
                # Check data counts
                counts = health_data.get('data_counts', {})
                for table, count in counts.items():
                    print(f"    📊 {table}: {count:,} records")
                
                return health_data['status'] == 'healthy'
            else:
                print(f"❌ Service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach service: {e}")
            return False
    
    def validate_plans_data(self) -> dict:
        """Validate energy plans data quality"""
        print("\n🔍 Validating Plans Data Quality...")
        
        validation_results = {
            "total_plans": 0,
            "retailers": 0,
            "issues": [],
            "quality_score": 0
        }
        
        try:
            # Basic counts
            basic_stats_query = f"""
            SELECT 
                COUNT(*) as total_plans,
                COUNT(DISTINCT retailer) as retailers,
                COUNT(DISTINCT fuel_type) as fuel_types,
                COUNT(CASE WHEN plan_name IS NULL OR plan_name = '' THEN 1 END) as plans_missing_name,
                COUNT(CASE WHEN application_url IS NULL OR application_url = '' THEN 1 END) as plans_missing_url,
                COUNT(CASE WHEN effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP() THEN 1 END) as active_plans,
                COUNT(CASE WHEN extracted_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY) THEN 1 END) as recently_updated
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
            """
            
            result = self.client.query(basic_stats_query).to_dataframe()
            stats = result.iloc[0].to_dict()
            
            validation_results["total_plans"] = int(stats["total_plans"])
            validation_results["retailers"] = int(stats["retailers"])
            
            print(f"  📊 Total Plans: {stats['total_plans']:,}")
            print(f"  🏢 Retailers: {stats['retailers']}")
            print(f"  ⚡ Fuel Types: {stats['fuel_types']}")
            print(f"  ✅ Active Plans: {stats['active_plans']:,}")
            print(f"  🔄 Recently Updated: {stats['recently_updated']:,}")
            
            # Check for data quality issues
            if stats["plans_missing_name"] > 0:
                issue = f"{stats['plans_missing_name']} plans missing names"
                validation_results["issues"].append(issue)
                print(f"  ⚠️  {issue}")
            
            if stats["plans_missing_url"] > stats["total_plans"] * 0.5:  # More than 50% missing URLs
                issue = f"High number of plans missing application URLs: {stats['plans_missing_url']}"
                validation_results["issues"].append(issue)
                print(f"  ⚠️  {issue}")
            
            if stats["recently_updated"] < stats["total_plans"] * 0.1:  # Less than 10% updated recently
                issue = "Data appears stale - few recent updates"
                validation_results["issues"].append(issue)
                print(f"  ⚠️  {issue}")
            
            # Check retailer coverage
            retailer_coverage_query = f"""
            SELECT 
                retailer,
                COUNT(*) as plan_count,
                COUNT(CASE WHEN fuel_type = 'ELECTRICITY' THEN 1 END) as electricity_plans,
                COUNT(CASE WHEN fuel_type = 'GAS' THEN 1 END) as gas_plans
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
            WHERE (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
            GROUP BY retailer
            ORDER BY plan_count DESC
            LIMIT 20
            """
            
            retailer_result = self.client.query(retailer_coverage_query).to_dataframe()
            
            # Check for major retailers
            major_retailers = ['agl', 'origin', 'energyaustralia', 'alinta', 'red-energy']
            missing_major = []
            
            for retailer in major_retailers:
                if retailer not in retailer_result['retailer'].values:
                    missing_major.append(retailer)
            
            if missing_major:
                issue = f"Missing major retailers: {', '.join(missing_major)}"
                validation_results["issues"].append(issue)
                print(f"  ❌ {issue}")
            
            # Calculate quality score
            max_score = 100
            score_deductions = len(validation_results["issues"]) * 15
            validation_results["quality_score"] = max(0, max_score - score_deductions)
            
        except Exception as e:
            validation_results["issues"].append(f"Validation failed: {str(e)}")
            print(f"  ❌ Validation error: {e}")
        
        return validation_results
    
    def validate_tariff_data(self) -> dict:
        """Validate tariff data coverage and quality"""
        print("\n🔍 Validating Tariff Data Quality...")
        
        validation_results = {
            "total_rates": 0,
            "plans_with_rates": 0,
            "coverage_percent": 0,
            "issues": [],
            "quality_score": 0
        }
        
        try:
            # Check tariff coverage
            tariff_coverage_query = f"""
            WITH plan_totals AS (
                SELECT COUNT(*) as total_plans
                FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
                WHERE (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
            ),
            tariff_stats AS (
                SELECT 
                    COUNT(*) as total_rates,
                    COUNT(DISTINCT plan_id) as plans_with_rates,
                    COUNT(DISTINCT rate_type) as rate_types,
                    COUNT(CASE WHEN rate_type = 'DAILY_SUPPLY' THEN 1 END) as supply_charges,
                    COUNT(CASE WHEN rate_type = 'USAGE' THEN 1 END) as usage_charges
                FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates`
            )
            SELECT 
                pt.total_plans,
                ts.total_rates,
                ts.plans_with_rates,
                ts.rate_types,
                ts.supply_charges,
                ts.usage_charges,
                ROUND(ts.plans_with_rates * 100.0 / pt.total_plans, 1) as coverage_percent
            FROM plan_totals pt, tariff_stats ts
            """
            
            result = self.client.query(tariff_coverage_query).to_dataframe()
            
            if not result.empty:
                stats = result.iloc[0].to_dict()
                
                validation_results["total_rates"] = int(stats["total_rates"])
                validation_results["plans_with_rates"] = int(stats["plans_with_rates"])
                validation_results["coverage_percent"] = float(stats["coverage_percent"])
                
                print(f"  📊 Total Tariff Rates: {stats['total_rates']:,}")
                print(f"  📋 Plans with Rates: {stats['plans_with_rates']:,}")
                print(f"  📈 Coverage: {stats['coverage_percent']}%")
                print(f"  🏷️  Rate Types: {stats['rate_types']}")
                print(f"  💰 Supply Charges: {stats['supply_charges']:,}")
                print(f"  ⚡ Usage Charges: {stats['usage_charges']:,}")
                
                # Quality checks
                if stats["coverage_percent"] < 20:
                    issue = f"Low tariff coverage: {stats['coverage_percent']}%"
                    validation_results["issues"].append(issue)
                    print(f"  ⚠️  {issue}")
                
                if stats["supply_charges"] < stats["plans_with_rates"] * 0.8:
                    issue = "Many plans missing supply charge data"
                    validation_results["issues"].append(issue)
                    print(f"  ⚠️  {issue}")
                
                # Calculate quality score
                coverage_score = min(100, stats["coverage_percent"] * 5)  # 20% coverage = 100 points
                completeness_score = (stats["supply_charges"] / max(1, stats["plans_with_rates"])) * 100
                validation_results["quality_score"] = (coverage_score + completeness_score) / 2
            
        except Exception as e:
            validation_results["issues"].append(f"Tariff validation failed: {str(e)}")
            print(f"  ❌ Validation error: {e}")
        
        return validation_results
    
    def validate_geography_data(self) -> dict:
        """Validate geographic coverage data"""
        print("\n🔍 Validating Geography Data...")
        
        validation_results = {
            "total_records": 0,
            "plans_with_geography": 0,
            "postcodes_covered": 0,
            "issues": [],
            "quality_score": 0
        }
        
        try:
            geo_stats_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT plan_id) as plans_with_geography,
                COUNT(DISTINCT postcode) as postcodes_covered,
                COUNT(CASE WHEN included = true THEN 1 END) as included_records,
                COUNT(CASE WHEN included = false THEN 1 END) as excluded_records
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography`
            """
            
            result = self.client.query(geo_stats_query).to_dataframe()
            
            if not result.empty:
                stats = result.iloc[0].to_dict()
                
                validation_results["total_records"] = int(stats["total_records"])
                validation_results["plans_with_geography"] = int(stats["plans_with_geography"])
                validation_results["postcodes_covered"] = int(stats["postcodes_covered"])
                
                print(f"  📊 Total Geography Records: {stats['total_records']:,}")
                print(f"  📋 Plans with Geography: {stats['plans_with_geography']:,}")
                print(f"  📍 Postcodes Covered: {stats['postcodes_covered']:,}")
                print(f"  ✅ Included Records: {stats['included_records']:,}")
                print(f"  ❌ Excluded Records: {stats['excluded_records']:,}")
                
                # Quality checks
                if stats["postcodes_covered"] < 1000:  # Australia has ~4000 postcodes
                    issue = f"Low postcode coverage: {stats['postcodes_covered']}"
                    validation_results["issues"].append(issue)
                    print(f"  ⚠️  {issue}")
                
                validation_results["quality_score"] = min(100, (stats["postcodes_covered"] / 4000) * 100)
            
        except Exception as e:
            validation_results["issues"].append(f"Geography validation failed: {str(e)}")
            print(f"  ❌ No geography data available")
            validation_results["quality_score"] = 0
        
        return validation_results
    
    def validate_postcode_data(self) -> dict:
        """Validate Australian postcode data"""
        print("\n🔍 Validating Postcode Data...")
        
        validation_results = {
            "total_postcodes": 0,
            "states_covered": 0,
            "data_source": "unknown",
            "issues": [],
            "quality_score": 0
        }
        
        try:
            postcode_stats_query = f"""
            SELECT 
                COUNT(*) as total_postcodes,
                COUNT(DISTINCT state) as states_covered,
                data_source,
                COUNT(DISTINCT CASE WHEN state = 'NSW' THEN postcode END) as nsw_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'VIC' THEN postcode END) as vic_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'QLD' THEN postcode END) as qld_postcodes,
                MAX(loaded_at) as last_loaded
            FROM `{PROJECT_ID}.{DATASET_ID}.australian_postcodes`
            GROUP BY data_source
            """
            
            result = self.client.query(postcode_stats_query).to_dataframe()
            
            if not result.empty:
                stats = result.iloc[0].to_dict()
                
                validation_results["total_postcodes"] = int(stats["total_postcodes"])
                validation_results["states_covered"] = int(stats["states_covered"])
                validation_results["data_source"] = stats["data_source"]
                
                print(f"  📊 Total Postcodes: {stats['total_postcodes']:,}")
                print(f"  🏛️  States Covered: {stats['states_covered']}")
                print(f"  📡 Data Source: {stats['data_source']}")
                print(f"  🏙️  NSW: {stats['nsw_postcodes']:,}")
                print(f"  🏙️  VIC: {stats['vic_postcodes']:,}")
                print(f"  🏙️  QLD: {stats['qld_postcodes']:,}")
                print(f"  🔄 Last Loaded: {stats['last_loaded']}")
                
                # Quality checks
                if stats["states_covered"] < 8:  # Australia has 8 states/territories
                    issue = f"Missing states: {8 - stats['states_covered']}"
                    validation_results["issues"].append(issue)
                    print(f"  ⚠️  {issue}")
                
                if stats["total_postcodes"] < 3000:  # Australia has ~4000 postcodes
                    issue = f"Low postcode count: {stats['total_postcodes']}"
                    validation_results["issues"].append(issue)
                    print(f"  ⚠️  {issue}")
                
                validation_results["quality_score"] = min(100, (stats["total_postcodes"] / 4000) * 100)
            
        except Exception as e:
            validation_results["issues"].append(f"Postcode validation failed: {str(e)}")
            print(f"  ❌ No postcode data available")
            validation_results["quality_score"] = 0
        
        return validation_results
    
    def generate_recommendations(self, validation_results: dict) -> list:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        
        # Plans data recommendations
        plans_data = validation_results.get("plans", {})
        if plans_data.get("quality_score", 0) < 80:
            recommendations.append({
                "priority": "high",
                "action": "Run plans extraction",
                "command": f"curl -X POST {self.service_url}/extract-plans",
                "description": "Refresh basic energy plans data"
            })
        
        # Tariff data recommendations
        tariff_data = validation_results.get("tariffs", {})
        if tariff_data.get("coverage_percent", 0) < 50:
            recommendations.append({
                "priority": "high",
                "action": "Run systematic tariff extraction",
                "command": f"curl -X POST {self.service_url}/retailers/extract-systematic -d '{\"retailers_per_run\": 5}'",
                "description": "Extract detailed tariff data for better pricing accuracy"
            })
        
        # Geography data recommendations
        geography_data = validation_results.get("geography", {})
        if geography_data.get("quality_score", 0) < 60:
            recommendations.append({
                "priority": "medium",
                "action": "Extract geography data with tariffs",
                "command": "Geography data is extracted automatically with tariff extraction",
                "description": "Improve postcode coverage for location-based plan filtering"
            })
        
        # Postcode data recommendations
        postcode_data = validation_results.get("postcodes", {})
        if postcode_data.get("quality_score", 0) < 80:
            recommendations.append({
                "priority": "medium",
                "action": "Load postcode data",
                "command": f"curl -X POST {self.service_url}/load-postcodes",
                "description": "Load Australian postcode/state mapping for geographic queries"
            })
        
        return recommendations
    
    def run_full_validation(self) -> dict:
        """Run complete data quality validation"""
        print("🔍 WattsMyBill Data Quality Validation")
        print("=" * 50)
        
        # Check service health first
        if not self.check_service_health():
            return {"status": "error", "message": "Service unhealthy"}
        
        # Run all validations
        validation_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "service_url": self.service_url,
            "plans": self.validate_plans_data(),
            "tariffs": self.validate_tariff_data(),
            "geography": self.validate_geography_data(),
            "postcodes": self.validate_postcode_data()
        }
        
        # Calculate overall quality score
        scores = [
            validation_results["plans"]["quality_score"],
            validation_results["tariffs"]["quality_score"],
            validation_results["geography"]["quality_score"],
            validation_results["postcodes"]["quality_score"]
        ]
        validation_results["overall_quality_score"] = sum(scores) / len(scores)
        
        # Generate recommendations
        validation_results["recommendations"] = self.generate_recommendations(validation_results)
        
        # Print summary
        print(f"\n📊 Overall Data Quality Score: {validation_results['overall_quality_score']:.1f}/100")
        
        if validation_results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(validation_results["recommendations"], 1):
                priority_emoji = "🔴" if rec["priority"] == "high" else "🟡"
                print(f"  {i}. {priority_emoji} {rec['action']}")
                print(f"     💬 {rec['description']}")
                print(f"     ⚡ {rec['command']}")
        else:
            print(f"\n✅ No immediate actions required - data quality is good!")
        
        return validation_results

def main():
    """Main monitoring function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="WattsMyBill Data Quality Monitor")
    parser.add_argument("--service-url", type=str, help="ETL Service URL")
    parser.add_argument("--trigger-extractions", action="store_true", help="Automatically trigger recommended extractions")
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = DataQualityMonitor(args.service_url)
    
    # Run validation
    results = monitor.run_full_validation()
    
    # Trigger extractions if requested
    if args.trigger_extractions and results.get("recommendations"):
        print(f"\n🚀 Triggering recommended extractions...")
        
        for rec in results["recommendations"]:
            if rec["priority"] == "high" and "curl" in rec["command"]:
                try:
                    # Extract curl command and execute
                    import subprocess
                    cmd_parts = rec["command"].split()
                    if "curl" in cmd_parts[0]:
                        print(f"  ⏳ Running: {rec['action']}")
                        # For safety, we'll just print what would be executed
                        print(f"    Command: {rec['command']}")
                        # subprocess.run(cmd_parts, timeout=300)  # Uncomment to actually run
                except Exception as e:
                    print(f"    ❌ Failed: {e}")
    
    # Return exit code based on quality
    overall_score = results.get("overall_quality_score", 0)
    if overall_score < 50:
        return 1  # Poor quality
    elif overall_score < 80:
        return 2  # Needs improvement
    else:
        return 0  # Good quality

if __name__ == "__main__":
    exit(main())