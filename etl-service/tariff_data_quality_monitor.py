#!/usr/bin/env python3
"""
Tariff Data Quality Monitor
Validates and monitors the quality of extracted comprehensive tariff data
"""

import os
import logging
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

class TariffDataQualityMonitor:
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        self.issues = []
        
    def add_issue(self, severity: str, category: str, description: str, count: int = None, details: dict = None):
        """Add a data quality issue"""
        issue = {
            "timestamp": datetime.utcnow(),
            "severity": severity,  # CRITICAL, HIGH, MEDIUM, LOW
            "category": category,
            "description": description,
            "count": count,
            "details": details or {}
        }
        self.issues.append(issue)
        
        # Log based on severity
        if severity == "CRITICAL":
            logger.error(f"🔴 {description}" + (f" (count: {count})" if count else ""))
        elif severity == "HIGH":
            logger.warning(f"🟠 {description}" + (f" (count: {count})" if count else ""))
        elif severity == "MEDIUM":
            logger.info(f"🟡 {description}" + (f" (count: {count})" if count else ""))
        else:
            logger.debug(f"🟢 {description}" + (f" (count: {count})" if count else ""))

    def check_table_exists(self, table_name: str) -> bool:
        """Check if a table exists"""
        try:
            table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
            self.client.get_table(table_ref)
            return True
        except:
            self.add_issue("CRITICAL", "infrastructure", f"Table {table_name} does not exist")
            return False

    def get_extraction_runs(self, days_back: int = 7) -> pd.DataFrame:
        """Get recent extraction runs"""
        query = f"""
        SELECT 
            extraction_run_id,
            COUNT(*) as plans_extracted,
            MIN(extracted_at) as run_start,
            MAX(extracted_at) as run_end,
            COUNT(DISTINCT retailer) as retailers,
            COUNT(DISTINCT fuel_type) as fuel_types
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
        WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days_back} DAY)
        GROUP BY extraction_run_id
        ORDER BY run_start DESC
        """
        return self.client.query(query).to_dataframe()

    def check_data_freshness(self, max_age_hours: int = 24):
        """Check if data is fresh enough"""
        query = f"""
        SELECT 
            MAX(extracted_at) as latest_extraction,
            TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(extracted_at), HOUR) as hours_since_last
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
        """
        
        result = self.client.query(query).to_dataframe()
        
        if result.empty:
            self.add_issue("CRITICAL", "freshness", "No extraction data found")
            return
            
        hours_since = result.iloc[0]['hours_since_last']
        
        if hours_since > max_age_hours:
            self.add_issue("HIGH", "freshness", 
                          f"Data is {hours_since:.1f} hours old (threshold: {max_age_hours}h)")
        else:
            self.add_issue("LOW", "freshness", f"Data is fresh ({hours_since:.1f} hours old)")

    def check_tariff_rate_completeness(self):
        """Check completeness of tariff rate extraction"""
        # Plans with contract details but no tariff rates
        query = f"""
        WITH plans_with_contracts AS (
            SELECT DISTINCT plan_id, fuel_type
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
            WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        ),
        plans_with_rates AS (
            SELECT DISTINCT plan_id, fuel_type
            FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive`
            WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        )
        SELECT 
            c.plan_id,
            c.fuel_type
        FROM plans_with_contracts c
        LEFT JOIN plans_with_rates r USING (plan_id, fuel_type)
        WHERE r.plan_id IS NULL
        """
        
        missing_rates = self.client.query(query).to_dataframe()
        
        if not missing_rates.empty:
            self.add_issue("HIGH", "completeness", 
                          f"Plans with contract details but no tariff rates",
                          count=len(missing_rates),
                          details={"missing_plans": missing_rates.to_dict('records')[:10]})

    def check_price_validity(self):
        """Check for invalid pricing data"""
        checks = [
            # Negative prices (except feed-in tariffs)
            {
                "query": f"""
                SELECT plan_id, unit_price, rate_type, fuel_type
                FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive`
                WHERE unit_price < 0 AND rate_type != 'SOLAR_FIT'
                AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
                """,
                "severity": "HIGH",
                "description": "Negative unit prices found (excluding solar FIT)"
            },
            
            # Extremely high prices (>$2/kWh for electricity, >$1/MJ for gas)
            {
                "query": f"""
                SELECT plan_id, unit_price, rate_type, fuel_type, unit
                FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive`
                WHERE (
                    (fuel_type = 'ELECTRICITY' AND unit = 'KWH' AND unit_price > 2.0)
                    OR (fuel_type = 'GAS' AND unit = 'MJ' AND unit_price > 1.0)
                )
                AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
                """,
                "severity": "MEDIUM",
                "description": "Extremely high unit prices detected"
            },
            
            # Zero daily supply charges
            {
                "query": f"""
                SELECT plan_id, fuel_type
                FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive`
                WHERE rate_type = 'DAILY_SUPPLY' AND unit_price = 0
                AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
                """,
                "severity": "MEDIUM",
                "description": "Plans with zero daily supply charges"
            }
        ]
        
        for check in checks:
            result = self.client.query(check["query"]).to_dataframe()
            if not result.empty:
                self.add_issue(check["severity"], "data_validity", 
                              check["description"],
                              count=len(result),
                              details={"examples": result.to_dict('records')[:5]})

    def check_data_consistency(self):
        """Check for data consistency issues"""
        
        # Plans with discounts but no base rates
        query = f"""
        WITH plans_with_discounts AS (
            SELECT DISTINCT plan_id, fuel_type
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_discounts`
            WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        ),
        plans_with_usage_rates AS (
            SELECT DISTINCT plan_id, fuel_type
            FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive`
            WHERE rate_type = 'USAGE'
            AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        )
        SELECT d.plan_id, d.fuel_type
        FROM plans_with_discounts d
        LEFT JOIN plans_with_usage_rates r USING (plan_id, fuel_type)
        WHERE r.plan_id IS NULL
        """
        
        inconsistent = self.client.query(query).to_dataframe()
        if not inconsistent.empty:
            self.add_issue("MEDIUM", "consistency", 
                          "Plans with discounts but no usage rates",
                          count=len(inconsistent))

    def check_retailer_coverage(self):
        """Check retailer coverage compared to simple plans"""
        query = f"""
        WITH simple_retailers AS (
            SELECT DISTINCT retailer
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
            WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        ),
        detailed_retailers AS (
            SELECT DISTINCT retailer
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
            WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        )
        SELECT 
            COUNT(DISTINCT s.retailer) as simple_retailers,
            COUNT(DISTINCT d.retailer) as detailed_retailers,
            COUNT(DISTINCT s.retailer) - COUNT(DISTINCT d.retailer) as missing_retailers
        FROM simple_retailers s
        FULL OUTER JOIN detailed_retailers d ON s.retailer = d.retailer
        """
        
        coverage = self.client.query(query).to_dataframe()
        if not coverage.empty and coverage.iloc[0]['missing_retailers'] > 0:
            self.add_issue("MEDIUM", "coverage", 
                          f"Missing detailed data for {coverage.iloc[0]['missing_retailers']} retailers")

    def check_json_field_validity(self):
        """Check validity of JSON fields"""
        tables_with_json = [
            ("plan_contract_details", ["payment_options", "meter_types", "bill_frequency", "raw_contract_data"]),
            ("tariff_rates_comprehensive", ["days_of_week"]),
            ("controlled_load_tariffs", ["days_of_week"]),
            ("solar_feed_in_tariffs", ["days_of_week"])
        ]
        
        for table_name, json_fields in tables_with_json:
            if not self.check_table_exists(table_name):
                continue
                
            for field in json_fields:
                query = f"""
                SELECT plan_id, {field}
                FROM `{PROJECT_ID}.{DATASET_ID}.{table_name}`
                WHERE {field} IS NOT NULL
                AND {field} != ''
                AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
                LIMIT 10
                """
                
                try:
                    result = self.client.query(query).to_dataframe()
                    invalid_json = []
                    
                    for _, row in result.iterrows():
                        try:
                            json.loads(row[field])
                        except (json.JSONDecodeError, TypeError):
                            invalid_json.append({
                                "plan_id": row["plan_id"],
                                "field": field,
                                "value": str(row[field])[:100]
                            })
                    
                    if invalid_json:
                        self.add_issue("MEDIUM", "data_format", 
                                      f"Invalid JSON in {table_name}.{field}",
                                      count=len(invalid_json),
                                      details={"examples": invalid_json[:3]})
                        
                except Exception as e:
                    logger.debug(f"Could not check JSON validity for {table_name}.{field}: {e}")

    def check_extraction_performance(self):
        """Check extraction performance metrics"""
        query = f"""
        SELECT 
            extraction_run_id,
            COUNT(*) as total_plans,
            COUNT(DISTINCT retailer) as retailers,
            TIMESTAMP_DIFF(MAX(extracted_at), MIN(extracted_at), MINUTE) as duration_minutes,
            COUNT(*) / NULLIF(TIMESTAMP_DIFF(MAX(extracted_at), MIN(extracted_at), MINUTE), 0) as plans_per_minute
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
        WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        GROUP BY extraction_run_id
        ORDER BY MIN(extracted_at) DESC
        LIMIT 5
        """
        
        performance = self.client.query(query).to_dataframe()
        
        if not performance.empty:
            latest_run = performance.iloc[0]
            
            # Check if extraction is too slow
            if latest_run['plans_per_minute'] < 1:
                self.add_issue("MEDIUM", "performance", 
                              f"Slow extraction rate: {latest_run['plans_per_minute']:.2f} plans/minute")
            
            # Check for incomplete runs (very short duration)
            if latest_run['duration_minutes'] < 5 and latest_run['total_plans'] > 100:
                self.add_issue("HIGH", "performance", 
                              f"Suspiciously short extraction run: {latest_run['duration_minutes']} minutes for {latest_run['total_plans']} plans")

    def check_rate_structure_distribution(self):
        """Check distribution of rate structures"""
        query = f"""
        SELECT 
            fuel_type,
            rate_structure,
            COUNT(*) as count,
            COUNT(DISTINCT plan_id) as unique_plans
        FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive`
        WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        GROUP BY fuel_type, rate_structure
        ORDER BY fuel_type, count DESC
        """
        
        distribution = self.client.query(query).to_dataframe()
        
        if not distribution.empty:
            # Check for missing common rate structures
            electricity_structures = distribution[distribution['fuel_type'] == 'ELECTRICITY']['rate_structure'].tolist()
            
            expected_structures = ['singleRate', 'timeOfUseRates', 'dailySupplyCharge']
            missing_structures = [s for s in expected_structures if s not in electricity_structures]
            
            if missing_structures:
                self.add_issue("MEDIUM", "completeness", 
                              f"Missing common rate structures for electricity: {missing_structures}")

    def check_solar_fit_coverage(self):
        """Check solar feed-in tariff coverage for electricity plans"""
        query = f"""
        WITH electricity_plans AS (
            SELECT DISTINCT plan_id
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
            WHERE fuel_type IN ('ELECTRICITY', 'DUAL')
            AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        ),
        plans_with_solar AS (
            SELECT DISTINCT plan_id
            FROM `{PROJECT_ID}.{DATASET_ID}.solar_feed_in_tariffs`
            WHERE extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        )
        SELECT 
            COUNT(e.plan_id) as total_electricity_plans,
            COUNT(s.plan_id) as plans_with_solar,
            ROUND(100.0 * COUNT(s.plan_id) / COUNT(e.plan_id), 2) as solar_coverage_percent
        FROM electricity_plans e
        LEFT JOIN plans_with_solar s USING (plan_id)
        """
        
        solar_coverage = self.client.query(query).to_dataframe()
        
        if not solar_coverage.empty:
            coverage_pct = solar_coverage.iloc[0]['solar_coverage_percent']
            if coverage_pct < 50:  # Expect most electricity plans to have solar FIT
                self.add_issue("MEDIUM", "completeness", 
                              f"Low solar FIT coverage: {coverage_pct}% of electricity plans")

    def generate_summary_report(self) -> dict:
        """Generate a summary report of all checks"""
        # Count issues by severity
        severity_counts = {}
        category_counts = {}
        
        for issue in self.issues:
            severity = issue['severity']
            category = issue['category']
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Get latest extraction stats
        extraction_runs = self.get_extraction_runs(days_back=1)
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_issues": len(self.issues),
            "issues_by_severity": severity_counts,
            "issues_by_category": category_counts,
            "recent_extractions": len(extraction_runs),
            "latest_extraction": extraction_runs.iloc[0].to_dict() if not extraction_runs.empty else None,
            "issues": [
                {
                    "severity": issue['severity'],
                    "category": issue['category'],
                    "description": issue['description'],
                    "count": issue['count'],
                    "timestamp": issue['timestamp'].isoformat()
                }
                for issue in self.issues
            ]
        }
        
        return report

    def run_all_checks(self):
        """Run all data quality checks"""
        logger.info("🔍 Starting comprehensive data quality checks...")
        
        # Core infrastructure checks
        required_tables = [
            "plan_contract_details", "tariff_rates_comprehensive", "plan_discounts",
            "plan_fees", "plan_incentives", "solar_feed_in_tariffs"
        ]
        
        tables_exist = all(self.check_table_exists(table) for table in required_tables)
        
        if not tables_exist:
            logger.error("❌ Critical tables missing - aborting further checks")
            return self.generate_summary_report()
        
        # Data quality checks
        self.check_data_freshness()
        self.check_tariff_rate_completeness()
        self.check_price_validity()
        self.check_data_consistency()
        self.check_retailer_coverage()
        self.check_json_field_validity()
        self.check_extraction_performance()
        self.check_rate_structure_distribution()
        self.check_solar_fit_coverage()
        
        # Generate and return report
        report = self.generate_summary_report()
        
        # Log summary
        logger.info(f"✅ Data quality check complete:")
        logger.info(f"   Total issues: {report['total_issues']}")
        for severity, count in report['issues_by_severity'].items():
            logger.info(f"   {severity}: {count}")
        
        return report

def save_report_to_bigquery(report: dict):
    """Save the quality report to BigQuery for tracking"""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Create quality reports table if it doesn't exist
    table_ref = f"{PROJECT_ID}.{DATASET_ID}.data_quality_reports"
    
    schema = [
        bigquery.SchemaField("report_timestamp", "TIMESTAMP"),
        bigquery.SchemaField("total_issues", "INTEGER"),
        bigquery.SchemaField("critical_issues", "INTEGER"),
        bigquery.SchemaField("high_issues", "INTEGER"),
        bigquery.SchemaField("medium_issues", "INTEGER"),
        bigquery.SchemaField("low_issues", "INTEGER"),
        bigquery.SchemaField("issues_by_category", "STRING"),  # JSON
        bigquery.SchemaField("latest_extraction_run", "STRING"),
        bigquery.SchemaField("full_report", "STRING")  # JSON
    ]
    
    try:
        client.get_table(table_ref)
    except:
        table = bigquery.Table(table_ref, schema=schema)
        client.create_table(table)
        logger.info("Created data_quality_reports table")
    
    # Prepare record
    severity_counts = report['issues_by_severity']
    record = {
        "report_timestamp": datetime.utcnow(),
        "total_issues": report['total_issues'],
        "critical_issues": severity_counts.get('CRITICAL', 0),
        "high_issues": severity_counts.get('HIGH', 0),
        "medium_issues": severity_counts.get('MEDIUM', 0),
        "low_issues": severity_counts.get('LOW', 0),
        "issues_by_category": json.dumps(report['issues_by_category']),
        "latest_extraction_run": report['latest_extraction']['extraction_run_id'] if report['latest_extraction'] else None,
        "full_report": json.dumps(report)
    }
    
    # Insert record
    df = pd.DataFrame([record])
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_APPEND")
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()
    
    logger.info("💾 Saved quality report to BigQuery")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor tariff data quality")
    parser.add_argument("--save-report", action="store_true", 
                       help="Save report to BigQuery")
    parser.add_argument("--output", type=str, 
                       help="Save report to JSON file")
    
    args = parser.parse_args()
    
    # Run quality checks
    monitor = TariffDataQualityMonitor()
    report = monitor.run_all_checks()
    
    # Save report if requested
    if args.save_report:
        save_report_to_bigquery(report)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logger.info(f"📄 Report saved to {args.output}")
    
    # Exit with error code if critical issues found
    critical_issues = report['issues_by_severity'].get('CRITICAL', 0)
    if critical_issues > 0:
        logger.error(f"❌ {critical_issues} critical issues found")
        exit(1)
    else:
        logger.info("✅ No critical issues found")

if __name__ == "__main__":
    main()