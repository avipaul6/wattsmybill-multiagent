#!/usr/bin/env python3
"""
WattsMyBill ETL Service with Comprehensive Data Management
Enhanced with comprehensive tariff extraction and monitoring
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify
from google.cloud import bigquery
import sys

# Import our ETL functions
sys.path.append('.')
import extract_plans
import extract_tariffs_comprehensive as extract_tariffs  # Updated import
import retailer_manager
import postcode_loader
from tariff_data_quality_monitor import TariffDataQualityMonitor, save_report_to_bigquery

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT', 'wattsmybill-dev')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
DATASET_ID = 'energy_plans'

logger.info(f"🚀 Starting WattsMyBill ETL Service - Environment: {ENVIRONMENT}")

# Initialize retailer manager
rm = retailer_manager.RetailerManager()

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API documentation"""
    return jsonify({
        "service": "WattsMyBill ETL Service",
        "version": "3.0.0",
        "description": "Australian Energy Plan Data ETL Service with Comprehensive Tariff Extraction",
        "environment": ENVIRONMENT,
        "status": "operational",
        "features": [
            "Complete CDR Energy API schema extraction",
            "10 specialized tariff data tables",
            "Automated data quality monitoring",
            "Systematic retailer processing",
            "Raw data backup and validation"
        ],
        "endpoints": {
            "health": "GET /health - Service health check",
            "api": "GET /api - API documentation",
            "stats": "GET /stats - Database statistics",
            "extract_plans": "POST /extract-plans - Extract basic energy plans",
            "extract_tariffs_comprehensive": "POST /extract-tariffs-comprehensive - Extract comprehensive tariff data",
            "data_quality": "GET /data-quality - Run data quality checks",
            "load_postcodes": "POST /load-postcodes - Load Australian postcode data",
            "retailers": {
                "status": "GET /retailers/status - Retailer extraction status",
                "systematic": "POST /retailers/extract-systematic - Run systematic extraction",
                "specific": "POST /retailers/{retailer}/extract - Extract for specific retailer",
                "next": "GET /retailers/next - Get next retailers to process"
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Comprehensive health check including new tables"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Test BigQuery connection
        query = f"SELECT 1 as test"
        client.query(query).result()
        
        # Check table existence - updated for comprehensive system
        tables_status = {}
        required_tables = [
            'plans_simple',
            'plan_contract_details',
            'tariff_rates_comprehensive', 
            'plan_discounts',
            'plan_fees',
            'plan_incentives',
            'solar_feed_in_tariffs',
            'plan_geography',
            'australian_postcodes'
        ]
        
        for table in required_tables:
            try:
                table_ref = f"{PROJECT_ID}.{DATASET_ID}.{table}"
                client.get_table(table_ref)
                tables_status[table] = "exists"
            except:
                tables_status[table] = "missing"
        
        # Get data counts
        data_counts = {}
        for table in required_tables:
            if tables_status[table] == "exists":
                try:
                    count_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{table}`"
                    result = client.query(count_query).to_dataframe()
                    data_counts[table] = int(result['count'].iloc[0])
                except:
                    data_counts[table] = 0
            else:
                data_counts[table] = 0
        
        # Determine overall health - updated criteria
        critical_tables = ['plans_simple', 'plan_contract_details']
        is_healthy = all(tables_status[table] == "exists" and data_counts[table] > 0 
                        for table in critical_tables)
        
        # Check data freshness
        freshness_status = "unknown"
        try:
            freshness_query = f"""
            SELECT TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(extracted_at), HOUR) as hours_old
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
            """
            freshness_result = client.query(freshness_query).to_dataframe()
            if not freshness_result.empty:
                hours_old = freshness_result.iloc[0]['hours_old']
                freshness_status = "fresh" if hours_old < 24 else "stale"
        except:
            pass
        
        return jsonify({
            "status": "healthy" if is_healthy else "degraded",
            "service": "wattsmybill-etl",
            "environment": ENVIRONMENT,
            "version": "3.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "bigquery_connection": "ok",
            "tables_status": tables_status,
            "data_counts": data_counts,
            "data_freshness": freshness_status,
            "comprehensive_tables": len([t for t in tables_status.values() if t == "exists"]),
            "warnings": [] if is_healthy else ["Missing critical data - run initial extraction"]
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "service": "wattsmybill-etl", 
            "environment": ENVIRONMENT,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/api', methods=['GET'])  
def api_info():
    """Updated API information for comprehensive system"""
    return jsonify({
        "service": "WattsMyBill ETL Service",
        "version": "3.0.0",
        "environment": ENVIRONMENT,
        "description": "Extract and manage comprehensive Australian energy plan data",
        "data_sources": [
            "Australian Energy Regulator (AER) Consumer Data Right APIs",
            "Australia Post Postcode Database",
            "Government Energy Plan Registry"
        ],
        "comprehensive_features": {
            "schema_coverage": "95%+ of CDR Energy API",
            "tariff_tables": 10,
            "data_structures": [
                "Complete contract details", "All rate structures", "Discount programs",
                "Fee schedules", "Incentive programs", "Solar feed-in tariffs",
                "Controlled load pricing", "Green power options", "Eligibility criteria"
            ]
        },
        "endpoints": {
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "Service health and comprehensive data status"
            },
            "stats": {
                "method": "GET", 
                "path": "/stats",
                "description": "Current database statistics across all tables"
            },
            "extract_plans": {
                "method": "POST",
                "path": "/extract-plans",
                "description": "Extract basic energy plans from all retailers"
            },
            "extract_tariffs_comprehensive": {
                "method": "POST",
                "path": "/extract-tariffs-comprehensive",
                "description": "Extract comprehensive tariff data",
                "parameters": {
                    "sample": "Extract N sample plans for testing",
                    "retailer": "Extract for specific retailer",
                    "fuel_type": "ELECTRICITY, GAS, or DUAL",
                    "batch_size": "Plans per batch (default: 20)"
                }
            },
            "data_quality": {
                "method": "GET",
                "path": "/data-quality",
                "description": "Run comprehensive data quality checks",
                "parameters": {
                    "save_report": "Save report to BigQuery (default: true)"
                }
            },
            "load_postcodes": {
                "method": "POST",
                "path": "/load-postcodes", 
                "description": "Load Australian postcode/state mapping data"
            },
            "systematic_extraction": {
                "method": "POST",
                "path": "/retailers/extract-systematic",
                "description": "Run systematic comprehensive tariff extraction",
                "parameters": {
                    "retailers_per_run": "Number of retailers to process (default: 2)",
                    "max_plans_per_retailer": "Max plans per retailer (default: 50)"
                }
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Enhanced database statistics for comprehensive system"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Get plan counts by retailer and fuel type
        plans_query = f"""
        SELECT 
            retailer,
            fuel_type,
            COUNT(*) as plan_count,
            MAX(extracted_at) as last_updated
        FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
        WHERE (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
        GROUP BY retailer, fuel_type
        ORDER BY plan_count DESC
        """
        plans_stats = client.query(plans_query).to_dataframe()
        
        # Get comprehensive tariff data stats
        comprehensive_stats = {}
        tariff_tables = [
            'plan_contract_details', 'tariff_rates_comprehensive', 'plan_discounts',
            'plan_fees', 'plan_incentives', 'solar_feed_in_tariffs',
            'controlled_load_tariffs', 'green_power_charges', 'plan_eligibility'
        ]
        
        for table in tariff_tables:
            try:
                query = f"""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT plan_id) as unique_plans,
                    MAX(extracted_at) as last_extraction
                FROM `{PROJECT_ID}.{DATASET_ID}.{table}`
                """
                result = client.query(query).to_dataframe()
                if not result.empty:
                    comprehensive_stats[table] = result.iloc[0].to_dict()
                else:
                    comprehensive_stats[table] = {"total_records": 0, "unique_plans": 0}
            except:
                comprehensive_stats[table] = {"total_records": 0, "unique_plans": 0}
        
        # Get geography stats
        try:
            geo_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT plan_id) as plans_with_geography,
                COUNT(DISTINCT postcode) as postcodes_covered
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography`
            """
            geo_result = client.query(geo_query).to_dataframe()
            geo_stats = geo_result.iloc[0].to_dict() if not geo_result.empty else {}
        except:
            geo_stats = {"total_records": 0, "plans_with_geography": 0, "postcodes_covered": 0}
        
        # Get retailer coverage stats
        retailer_stats = rm.get_extraction_report()
        
        # Calculate comprehensive coverage
        total_plans = comprehensive_stats.get('plan_contract_details', {}).get('unique_plans', 0)
        simple_plans = int(plans_stats['plan_count'].sum()) if not plans_stats.empty else 0
        comprehensive_coverage = (total_plans / simple_plans * 100) if simple_plans > 0 else 0
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "data_summary": {
                "total_simple_plans": simple_plans,
                "comprehensive_coverage_percent": round(comprehensive_coverage, 1),
                "total_contract_details": comprehensive_stats.get('plan_contract_details', {}).get('total_records', 0),
                "total_tariff_rates": comprehensive_stats.get('tariff_rates_comprehensive', {}).get('total_records', 0),
                "total_discounts": comprehensive_stats.get('plan_discounts', {}).get('total_records', 0),
                "total_solar_fits": comprehensive_stats.get('solar_feed_in_tariffs', {}).get('total_records', 0),
                "postcodes_available": geo_stats.get('postcodes_covered', 0) > 0,
                "retailer_coverage": retailer_stats['overall_stats']
            },
            "plans_by_retailer": plans_stats.to_dict('records') if not plans_stats.empty else [],
            "comprehensive_extraction": comprehensive_stats,
            "geography_coverage": geo_stats
        })
        
    except Exception as e:
        logger.error(f"Stats query failed: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "environment": ENVIRONMENT,
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/extract-tariffs-comprehensive', methods=['POST'])
def extract_tariffs_comprehensive_endpoint():
    """Extract comprehensive tariff data using new system"""
    data = request.get_json() or {}
    sample_size = data.get('sample', None)
    retailer = data.get('retailer', None)
    fuel_type = data.get('fuel_type', None)
    batch_size = data.get('batch_size', 20)
    
    logger.info(f"🔄 Starting comprehensive tariff extraction...")
    logger.info(f"   Parameters: sample={sample_size}, retailer={retailer}, fuel_type={fuel_type}")
    
    try:
        # Import and run comprehensive extraction
        import subprocess
        import sys
        
        # Build command
        cmd = [sys.executable, 'extract_tariffs_comprehensive.py']
        
        if sample_size:
            cmd.extend(['--sample', str(sample_size)])
        if retailer:
            cmd.extend(['--retailer', retailer])
        if fuel_type:
            cmd.extend(['--fuel-type', fuel_type])
        cmd.extend(['--batch-size', str(batch_size)])
        
        # Run extraction
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
        
        if result.returncode == 0:
            # Get extraction stats
            client = bigquery.Client(project=PROJECT_ID)
            stats_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT plan_id) as unique_plans,
                COUNT(DISTINCT extraction_run_id) as extraction_runs,
                MAX(extracted_at) as last_extraction
            FROM `{PROJECT_ID}.{DATASET_ID}.plan_contract_details`
            WHERE DATE(extracted_at) = CURRENT_DATE()
            """
            stats_result = client.query(stats_query).to_dataframe()
            extraction_stats = stats_result.iloc[0].to_dict() if not stats_result.empty else {}
            
            logger.info(f"✅ Comprehensive extraction completed: {extraction_stats.get('unique_plans', 0)} plans")
            
            return jsonify({
                "status": "success",
                "service": "wattsmybill-etl",
                "operation": "extract_tariffs_comprehensive",
                "environment": ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "parameters": {
                    "sample": sample_size,
                    "retailer": retailer,
                    "fuel_type": fuel_type,
                    "batch_size": batch_size
                },
                "results": extraction_stats,
                "stdout": result.stdout[-1000:] if result.stdout else "",  # Last 1000 chars
            })
        else:
            logger.error(f"❌ Comprehensive extraction failed: {result.stderr}")
            return jsonify({
                "status": "error",
                "service": "wattsmybill-etl",
                "operation": "extract_tariffs_comprehensive",
                "message": "Extraction process failed",
                "environment": ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "error": result.stderr[-500:] if result.stderr else "",
                "stdout": result.stdout[-500:] if result.stdout else ""
            }), 500
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Comprehensive extraction timed out")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "extract_tariffs_comprehensive",
            "message": "Extraction timed out (>1 hour)",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500
    except Exception as e:
        logger.error(f"❌ Comprehensive extraction failed: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "extract_tariffs_comprehensive",
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/data-quality', methods=['GET'])
def data_quality_check():
    """Run comprehensive data quality checks"""
    save_report = request.args.get('save_report', 'true').lower() == 'true'
    
    logger.info("🔍 Running comprehensive data quality checks...")
    
    try:
        # Run quality monitor
        monitor = TariffDataQualityMonitor()
        report = monitor.run_all_checks()
        
        # Save report if requested
        if save_report:
            save_report_to_bigquery(report)
        
        # Determine response status based on issues
        critical_issues = report['issues_by_severity'].get('CRITICAL', 0)
        high_issues = report['issues_by_severity'].get('HIGH', 0)
        
        response_status = 200
        if critical_issues > 0:
            response_status = 500
        elif high_issues > 0:
            response_status = 422
        
        return jsonify({
            "status": "completed",
            "service": "wattsmybill-etl",
            "operation": "data_quality_check",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "report_saved": save_report,
            "quality_summary": {
                "total_issues": report['total_issues'],
                "critical_issues": critical_issues,
                "high_issues": high_issues,
                "overall_status": "critical" if critical_issues > 0 else "warning" if high_issues > 0 else "good"
            },
            "detailed_report": report
        }), response_status
        
    except Exception as e:
        logger.error(f"❌ Data quality check failed: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "data_quality_check",
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# Keep existing endpoints but update extract-plans to work with legacy tariff system
@app.route('/extract-plans', methods=['POST'])
def extract_plans_endpoint():
    """Extract basic energy plans"""
    logger.info("🔄 Starting basic plans extraction...")
    
    try:
        # Run extraction
        extract_plans.main()
        
        # Get results
        client = bigquery.Client(project=PROJECT_ID)
        query = f"""
        SELECT 
            COUNT(*) as total_plans,
            COUNT(DISTINCT retailer) as retailers,
            COUNT(DISTINCT fuel_type) as fuel_types
        FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
        """
        result = client.query(query).to_dataframe()
        stats = result.iloc[0].to_dict()
        
        logger.info(f"✅ Plans extraction completed: {stats['total_plans']:,} plans from {stats['retailers']} retailers")
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "operation": "extract_plans",
            "message": f"Successfully extracted {stats['total_plans']:,} energy plans",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": {
                "total_plans": int(stats['total_plans']),
                "retailers": int(stats['retailers']),
                "fuel_types": int(stats['fuel_types']),
                "extraction_time": datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"❌ Plans extraction failed: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "extract_plans",
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# Keep all existing retailer endpoints but update them to work with comprehensive system
@app.route('/retailers/extract-systematic', methods=['POST'])
def systematic_extraction():
    """Run systematic comprehensive tariff extraction across retailers"""
    data = request.get_json() or {}
    retailers_per_run = data.get('retailers_per_run', 2)  # Reduced default for comprehensive extraction
    max_plans_per_retailer = data.get('max_plans_per_retailer', 50)  # Reduced for comprehensive extraction
    
    logger.info(f"🚀 Starting systematic comprehensive extraction: {retailers_per_run} retailers")
    
    try:
        result = rm.run_systematic_comprehensive_extraction(retailers_per_run, max_plans_per_retailer)
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "operation": "systematic_comprehensive_extraction",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": result
        })
    except Exception as e:
        logger.error(f"❌ Systematic comprehensive extraction failed: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "systematic_comprehensive_extraction",
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# Keep other existing endpoints unchanged
@app.route('/load-postcodes', methods=['POST'])
def load_postcodes_endpoint():
    """Load Australian postcode data"""
    logger.info("🗺️ Starting postcode data loading...")
    
    try:
        loader = postcode_loader.AustralianPostcodeLoader(PROJECT_ID)
        result = loader.load_postcode_data()
        
        if result['status'] == 'success':
            # Create lookup views
            loader.create_postcode_lookup_views()
            
            logger.info(f"✅ Postcode loading completed: {result['records_loaded']:,} postcodes")
            
            return jsonify({
                "status": "success",
                "service": "wattsmybill-etl",
                "operation": "load_postcodes",
                "environment": ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "results": result
            })
        else:
            return jsonify({
                "status": "error",
                "service": "wattsmybill-etl",
                "operation": "load_postcodes",
                "message": result['message'],
                "environment": ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat()
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Postcode loading failed: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "load_postcodes",
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

# Keep existing retailer status endpoints
@app.route('/retailers/status', methods=['GET'])
def retailer_status():
    """Get detailed retailer extraction status"""
    try:
        report = rm.get_extraction_report()
        retailer_details = rm.get_retailer_comprehensive_status()
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "timestamp": datetime.utcnow().isoformat(),
            "summary": report,
            "retailer_details": retailer_details[:20]
        })
    except Exception as e:
        logger.error(f"Retailer status failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/retailers/<retailer>/extract', methods=['POST'])
def extract_specific_retailer(retailer):
    """Extract comprehensive tariffs for a specific retailer"""
    data = request.get_json() or {}
    max_plans = data.get('max_plans', 100)
    
    logger.info(f"🔄 Starting comprehensive extraction for {retailer}")
    
    try:
        result = rm.extract_comprehensive_tariffs_for_retailer(retailer, max_plans)
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "operation": "retailer_comprehensive_extraction",
            "retailer": retailer,
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": result
        })
    except Exception as e:
        logger.error(f"❌ Comprehensive extraction failed for {retailer}: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "retailer_comprehensive_extraction",
            "retailer": retailer,
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/retailers/next', methods=['GET'])
def get_next_retailers():
    """Get the next retailers that need comprehensive tariff extraction"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        next_retailers = rm.get_next_retailers_to_process_comprehensive(limit)
        
        return jsonify({
            "status": "success",
            "next_retailers": next_retailers,
            "count": len(next_retailers),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.errorhandler(404)
def not_found(error):
    """404 handler"""
    return jsonify({
        "status": "error",
        "service": "wattsmybill-etl",
        "message": "Endpoint not found",
        "available_endpoints": [
            "/", "/health", "/api", "/stats", "/extract-plans", "/extract-tariffs-comprehensive",
            "/data-quality", "/load-postcodes", "/retailers/status", "/retailers/extract-systematic",
            "/retailers/{retailer}/extract"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 handler"""
    logger.error(f"Internal error: {error}")
    return jsonify({
        "status": "error",
        "service": "wattsmybill-etl",
        "message": "Internal server error",
        "timestamp": datetime.utcnow().isoformat()
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"🌐 Starting WattsMyBill ETL Service v3.0 on port {port}")
    app.run(host='0.0.0.0', port=port, debug=DEBUG)