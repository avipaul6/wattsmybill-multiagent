#!/usr/bin/env python3
"""
WattsMyBill ETL Service with Retailer Management
Enhanced with systematic retailer processing
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

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        query = f"SELECT 1 as test"
        client.query(query).result()
        
        return jsonify({
            "status": "healthy",
            "service": "wattsmybill-etl",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "bigquery_connection": "ok"
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
    """API info endpoint"""
    return jsonify({
        "service": "WattsMyBill ETL Service",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "endpoints": {
            "health": "GET /health",
            "stats": "GET /stats",
            "extract_plans": "POST /extract-plans",
            "extract_tariffs": "POST /extract-tariffs",
            "retailer_status": "GET /retailers/status",
            "systematic_extraction": "POST /retailers/extract-systematic",
            "retailer_extraction": "POST /retailers/{retailer}/extract"
        },
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Get current database statistics"""
    try:
        client = bigquery.Client(project=PROJECT_ID)
        
        # Get plan counts by retailer and fuel type
        plans_query = f"""
        SELECT 
            retailer,
            fuel_type,
            COUNT(*) as plan_count
        FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`
        WHERE (effective_to IS NULL OR effective_to > CURRENT_TIMESTAMP())
        GROUP BY retailer, fuel_type
        ORDER BY plan_count DESC
        """
        plans_stats = client.query(plans_query).to_dataframe()
        
        # Get tariff data stats
        try:
            tariff_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates`"
            tariff_count = client.query(tariff_query).to_dataframe()['count'].iloc[0]
        except:
            tariff_count = 0
        
        # Get geography stats
        try:
            geo_query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography`"
            geo_count = client.query(geo_query).to_dataframe()['count'].iloc[0]
        except:
            geo_count = 0
        
        # Get retailer coverage stats
        retailer_stats = rm.get_extraction_report()
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "data_summary": {
                "total_plans": int(plans_stats['plan_count'].sum()) if not plans_stats.empty else 0,
                "total_tariff_rates": int(tariff_count),
                "total_geography_records": int(geo_count),
                "retailer_coverage": retailer_stats['overall_stats']
            },
            "plans_by_retailer": plans_stats.to_dict('records') if not plans_stats.empty else []
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
        extract_plans.main()
        
        client = bigquery.Client(project=PROJECT_ID)
        query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple`"
        result = client.query(query).to_dataframe()
        plan_count = result['count'].iloc[0]
        
        logger.info(f"✅ Plans extraction completed: {plan_count:,} plans")
        
        return jsonify({
            "status": "success",
            "service": "wattsmybill-etl",
            "operation": "extract_plans",
            "message": f"Successfully extracted {plan_count:,} energy plans",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": {
                "total_plans": int(plan_count),
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

@app.route('/extract-tariffs', methods=['POST'])
def extract_tariffs_endpoint():
    """Extract detailed tariff data (legacy endpoint)"""
    data = request.get_json() or {}
    sample_size = data.get('sample_size', 100)
    retailer = data.get('retailer')
    
    if retailer:
        # Use retailer manager for specific retailer
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
        # Run systematic extraction
        result = rm.run_systematic_extraction(retailers_per_run=3, max_plans_per_retailer=sample_size)
        return jsonify({
            "status": result['status'],
            "service": "wattsmybill-etl",
            "operation": "extract_tariffs_systematic",
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
            "results": result
        })

# New retailer management endpoints
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
            "retailer_details": retailer_details[:20]  # Top 20 retailers
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
            "/health", "/api", "/stats", "/extract-plans", "/extract-tariffs",
            "/retailers/status", "/retailers/extract-systematic", "/retailers/{retailer}/extract"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500 handler"""
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