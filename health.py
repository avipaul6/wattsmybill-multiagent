import streamlit as st
import sys
import os
from pathlib import Path
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def health_check():
    """Health check endpoint for Cloud Run"""
    try:
        # Test imports
        from adk_integration.agent_factory import WattsMyBillAgentFactory
        from utils.bill_parser import AustralianBillParser
        
        # Test basic functionality
        config = {'project_id': os.getenv('GOOGLE_CLOUD_PROJECT', 'test')}
        factory = WattsMyBillAgentFactory(config)
        parser = AustralianBillParser()
        
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "environment": os.getenv('ENVIRONMENT', 'unknown'),
            "version": "1.0.0",
            "components": {
                "agent_factory": "ok",
                "bill_parser": "ok",
                "adk_integration": "ok"
            }
        }
        
        return health_data
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "environment": os.getenv('ENVIRONMENT', 'unknown')
        }

# Add health endpoint to main app
if 'health' in st.query_params or st.query_params.get('health'):
    health_result = health_check()
    st.json(health_result)
    st.stop()