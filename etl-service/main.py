#!/usr/bin/env python3
"""
WattsMyBill ETL Service with Complete Data Management
Enhanced with postcode loading and comprehensive monitoring
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
import extract_tariffs
import retailer_manager
import postcode_loader

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
        "version": "2.0.0",
        "description": "Australian Energy Plan Data ETL Service",
        "environment": ENVIRONMENT,
        "status": "operational",
        "endpoints": {
            "health": "GET /health - Service health check",
            "api": "GET /api - API documentation",
            "stats": "GET /stats - Database statistics",
            "extract_plans": "POST /extract-plans - Extract basic energy plans",
            "extract_tariffs": "POST /extract-tariffs - Extract detailed tariffs (legacy)",
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
    """Comprehensive health check"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Test BigQuery connection
        query = f"SELECT 1 as test"
        client.query(query).result()
        
        # Check table existence
        tables_status = {}
        required_tables = [
            'plans_simple',
            'tariff_rates', 
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
        
        # Determine overall health
        critical_tables = ['plans_simple']
        is_healthy = all(tables_status[table] == "exists" and data_counts[table] > 0 
                        for table in critical_tables)
        
        return jsonify({
            "status": "healthy" if is_healthy else "degraded",
            "service": "wattsmybill-etl",
            "environment": ENVIRONMENT,
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "bigquery_connection": "ok",
            "tables_status": tables_status,
            "data_counts": data_counts,
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
    """Detailed API information"""
    return jsonify({
        "service": "WattsMyBill ETL Service",
        "version": "2.0.0",
        "environment": ENVIRONMENT,
        "description": "Extract and manage Australian energy plan data",
        "data_sources": [
            "Australian Energy Regulator (AER) Consumer Data Right APIs",
            "Australia Post Postcode Database",
            "Government Energy Plan Registry"
        ],
        "endpoints": {
            "health": {
                "method": "GET",
                "path": "/health",
                "description": "Service health and data status"
            },
            "stats": {
                "method": "GET", 
                "path": "/stats",
                "description": "Current database statistics"
            },
            "extract_plans": {
                "method": "POST",
                "path": "/extract-plans",
                "description": "Extract basic energy plans from all retailers"
            },
            "load_postcodes": {
                "method": "POST",
                "path": "/load-postcodes", 
                "description": "Load Australian postcode/state mapping data"
            },
            "systematic_extraction": {
                "method": "POST",
                "path": "/retailers/extract-systematic",
                "description": "Run systematic tariff extraction",
                "parameters": {
                    "retailers_per_run": "Number of retailers to process (default: 3)",
                    "max_plans_per_retailer": "Max plans per retailer (default: 100)"
                }
            }
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Enhanced database statistics"""
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
        
        # Get tariff data stats
        try:
            tariff_query = f"""
            SELECT 
                COUNT(*) as total_rates,
                COUNT(DISTINCT plan_id) as plans_with_rates,
                COUNT(DISTINCT rate_type) as rate_types,
                MAX(extracted_at) as last_extraction
            FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates`
            """
            tariff_result = client.query(tariff_query).to_dataframe()
            tariff_stats = tariff_result.iloc[0].to_dict() if not tariff_result.empty else {}
        except:
            tariff_stats = {"total_rates": 0, "plans_with_rates": 0, "rate_types": 0}
        
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
        
        # Get postcode stats
        try:
            postcode_query = f"""
            SELECT 
                COUNT(*) as total_postcodes,
                COUNT(DISTINCT state) as states_covered,
                data_source,
                MAX(loaded_at) as last_loaded
            FROM `{PROJECT_ID}.{DATASET_ID}.australian_postcodes`
            GROUP BY data_source
            """
            postcode_result = client.query(postcode_query).to_dataframe()
            postcode_stats = postcode_result.to_dict('records') if not postcode_result.empty else []
        except:
            postcode_stats = []
        
        # Get retailer coverage stats
        retailer_stats = rm.get_extraction_report()
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "data_summary": {
                "total_plans": int(plans_stats['plan_count'].sum()) if not plans_stats.empty else 0,
                "total_tariff_rates": int(tariff_stats.get('total_rates', 0)),
                "plans_with_tariffs": int(tariff_stats.get('plans_with_rates', 0)),
                "total_geography_records": int(geo_stats.get('total_records', 0)),
                "postcodes_available": len(postcode_stats) > 0,
                "retailer_coverage": retailer_stats['overall_stats']
            },
            "plans_by_retailer": plans_stats.to_dict('records') if not plans_stats.empty else [],
            "tariff_extraction": tariff_stats,
            "geography_coverage": geo_stats,
            "postcode_data": postcode_stats
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

# Keep all existing retailer management endpoints
@app.route('/extract-tariffs', methods=['POST'])
def extract_tariffs_endpoint():
    """Extract detailed tariff data (legacy endpoint)"""
    data = request.get_json() or {}
    sample_size = data.get('sample_size', 100)
    retailer = data.get('retailer')
    
    if retailer:
        result = rm.extract_tariffs_for_retailer(retailer, sample_size)
        return jsonify({
            "status": result['status'],
            "service": "wattsmybill-etl",
            "operation": "extract_tariffs",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": result
        })
    else:
        result = rm.run_systematic_extraction(retailers_per_run=3, max_plans_per_retailer=sample_size)
        return jsonify({
            "status": result['status'],
            "service": "wattsmybill-etl",
            "operation": "extract_tariffs_systematic",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": result
        })

@app.route('/retailers/status', methods=['GET'])
def retailer_status():
    """Get detailed retailer extraction status"""
    try:
        report = rm.get_extraction_report()
        retailer_details = rm.get_retailer_tariff_status()
        
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

@app.route('/retailers/extract-systematic', methods=['POST'])
def systematic_extraction():
    """Run systematic tariff extraction across retailers"""
    data = request.get_json() or {}
    retailers_per_run = data.get('retailers_per_run', 3)
    max_plans_per_retailer = data.get('max_plans_per_retailer', 100)
    
    logger.info(f"🚀 Starting systematic extraction: {retailers_per_run} retailers")
    
    try:
        result = rm.run_systematic_extraction(retailers_per_run, max_plans_per_retailer)
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "operation": "systematic_extraction",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": result
        })
    except Exception as e:
        logger.error(f"❌ Systematic extraction failed: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "systematic_extraction",
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/retailers/<retailer>/extract', methods=['POST'])
def extract_specific_retailer(retailer):
    """Extract tariffs for a specific retailer"""
    data = request.get_json() or {}
    max_plans = data.get('max_plans', 200)
    
    logger.info(f"🔄 Starting extraction for {retailer}")
    
    try:
        result = rm.extract_tariffs_for_retailer(retailer, max_plans)
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "operation": "retailer_extraction",
            "retailer": retailer,
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": result
        })
    except Exception as e:
        logger.error(f"❌ Extraction failed for {retailer}: {e}")
        return jsonify({
            "status": "error",
            "service": "wattsmybill-etl",
            "operation": "retailer_extraction",
            "retailer": retailer,
            "message": str(e),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }), 500

@app.route('/retailers/next', methods=['GET'])
def get_next_retailers():
    """Get the next retailers that need tariff extraction"""
    limit = request.args.get('limit', 10, type=int)
    
    try:
        next_retailers = rm.get_next_retailers_to_process(limit)
        
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
            "/", "/health", "/api", "/stats", "/extract-plans", "/load-postcodes",
            "/retailers/status", "/retailers/extract-systematic", "/retailers/{retailer}/extract"
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
    logger.info(f"🌐 Starting WattsMyBill ETL Service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=DEBUG)