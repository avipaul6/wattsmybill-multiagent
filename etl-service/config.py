#!/usr/bin/env python3
"""
Configuration management for WattsMyBill ETL Service
Handles environment-specific configuration with proper defaults
"""

import os
import logging

logger = logging.getLogger(__name__)

class Config:
    """Configuration class that handles environment variables with proper defaults"""
    
    def __init__(self):
        # Core GCP Configuration
        self.PROJECT_ID = self._get_project_id()
        self.REGION = os.environ.get('GOOGLE_CLOUD_REGION', 'australia-southeast1')
        self.DATASET_ID = os.environ.get('BIGQUERY_DATASET_ID', 'energy_plans')
        
        # Environment Configuration
        self.ENVIRONMENT = os.environ.get('ENVIRONMENT', 'development')
        self.DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'
        self.LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
        
        # ETL Configuration
        self.DEFAULT_SAMPLE_SIZE = int(os.environ.get('DEFAULT_SAMPLE_SIZE', '100'))
        self.BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '25'))
        self.MAX_PARALLEL_REQUESTS = int(os.environ.get('MAX_PARALLEL_REQUESTS', '5'))
        self.REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', '0.5'))
        
        # Service Configuration
        self.PORT = int(os.environ.get('PORT', '8080'))
        self.SERVICE_NAME = os.environ.get('SERVICE_NAME', 'energy-plans-etl')
        
        logger.info(f"🔧 Configuration loaded - Environment: {self.ENVIRONMENT}, Project: {self.PROJECT_ID}")
    
    def _get_project_id(self) -> str:
        """
        Get project ID with proper priority:
        1. GOOGLE_CLOUD_PROJECT (set by Cloud Run)
        2. GCP_PROJECT_ID (set by CI/CD)
        3. PROJECT_ID (generic fallback)
        4. wattsmybill-dev (local development default)
        """
        project_id = (
            os.environ.get('GOOGLE_CLOUD_PROJECT') or
            os.environ.get('GCP_PROJECT_ID') or  
            os.environ.get('PROJECT_ID') or
            'wattsmybill-dev'  # Local development default
        )
        
        # Log which source was used (helpful for debugging)
        if os.environ.get('GOOGLE_CLOUD_PROJECT'):
            logger.info(f"Using project ID from GOOGLE_CLOUD_PROJECT: {project_id}")
        elif os.environ.get('GCP_PROJECT_ID'):
            logger.info(f"Using project ID from GCP_PROJECT_ID: {project_id}")
        elif os.environ.get('PROJECT_ID'):
            logger.info(f"Using project ID from PROJECT_ID: {project_id}")
        else:
            logger.info(f"Using default project ID for local development: {project_id}")
        
        return project_id
    
    def get_environment_config(self) -> dict:
        """Get environment-specific configuration"""
        if self.ENVIRONMENT == 'production':
            return {
                'batch_size': 30,
                'max_parallel_requests': 10,
                'request_delay': 0.3,
                'default_sample_size': 200,
                'timeout': 3600
            }
        elif self.ENVIRONMENT == 'development':
            return {
                'batch_size': 15,
                'max_parallel_requests': 3,
                'request_delay': 1.0,
                'default_sample_size': 50,
                'timeout': 1800
            }
        else:  # staging or other environments
            return {
                'batch_size': 20,
                'max_parallel_requests': 5,
                'request_delay': 0.5,
                'default_sample_size': 100,
                'timeout': 2400
            }
    
    def to_dict(self) -> dict:
        """Return configuration as dictionary for logging/debugging"""
        return {
            'project_id': self.PROJECT_ID,
            'environment': self.ENVIRONMENT,
            'region': self.REGION,
            'dataset_id': self.DATASET_ID,
            'debug': self.DEBUG,
            'service_name': self.SERVICE_NAME,
            'environment_config': self.get_environment_config()
        }

# Global configuration instance
config = Config()