import os
from typing import Dict, Any

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')
    DEBUG = False
    TESTING = False
    
    # Google Cloud Configuration
    BQ_DATASET_ID = os.environ.get('BQ_DATASET_ID', 'energy_data')
    BQ_LOCATION = os.environ.get('BQ_LOCATION', 'australia-southeast1')
    
    # API Keys
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')
    
    # Application settings
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}
    
    @staticmethod
    def init_app(app=None):
        pass

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENVIRONMENT = 'development'
    
    # More verbose logging in development
    LOG_LEVEL = 'DEBUG'
    
    # Allow CORS in development
    ENABLE_CORS = True
    
    # Development-specific settings
    CACHE_TTL = 60  # Short cache for development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENVIRONMENT = 'production'
    
    # Production logging
    LOG_LEVEL = 'INFO'
    
    # Security settings
    ENABLE_CORS = False
    SECURE_HEADERS = True
    
    # Production caching
    CACHE_TTL = 3600  # 1 hour cache
    
    # Performance settings
    MAX_CONCURRENT_USERS = 100
    REQUEST_TIMEOUT = 300

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    ENVIRONMENT = 'testing'
    
    # Test database
    USE_MOCK_DATA = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config() -> Config:
    """Get configuration based on environment"""
    env = os.environ.get('ENVIRONMENT', 'development')
    return config.get(env, config['default'])