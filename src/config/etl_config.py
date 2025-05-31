"""
ETL Integration Configuration and Setup
Handles environment configuration, credentials, and deployment settings

File: src/config/etl_config.py
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class ETLConfig:
    """Configuration for ETL integration"""
    project_id: str
    dataset_id: str
    credentials_path: Optional[str] = None
    use_default_credentials: bool = True
    fallback_to_api: bool = True
    fallback_to_competitive: bool = True
    max_plans_per_retailer: int = 50
    cache_duration_minutes: int = 30
    
    # BigQuery specific settings
    query_timeout_seconds: int = 60
    max_results: int = 1000
    use_query_cache: bool = True
    
    # Data quality settings
    min_usage_rate: float = 0.10
    max_usage_rate: float = 0.80
    min_supply_charge: float = 0.50
    max_supply_charge: float = 3.00
    
    # Feature flags
    enable_etl_warehouse: bool = True
    enable_api_supplement: bool = True
    enable_detailed_logging: bool = False
    enable_performance_monitoring: bool = True


class ETLConfigManager:
    """Manages ETL configuration across environments"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._get_default_config_path()
        self.config = self._load_config()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path"""
        return os.path.join(os.path.dirname(__file__), "etl_config.json")
    
    def _load_config(self) -> ETLConfig:
        """Load configuration from file or environment"""
        
        # Try to load from file first
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                return ETLConfig(**config_data)
            except Exception as e:
                print(f"⚠️  Failed to load config file {self.config_file}: {e}")
        
        # Fall back to environment variables
        return self._load_from_environment()
    
    def _load_from_environment(self) -> ETLConfig:
        """Load configuration from environment variables"""
        
        return ETLConfig(
            project_id=os.getenv('BIGQUERY_PROJECT_ID', 'wattsmybill-dev'),
            dataset_id=os.getenv('BIGQUERY_DATASET_ID', 'energy_plans'),
            credentials_path=os.getenv('GOOGLE_APPLICATION_CREDENTIALS'),
            use_default_credentials=os.getenv('USE_DEFAULT_CREDENTIALS', 'true').lower() == 'true',
            fallback_to_api=os.getenv('FALLBACK_TO_API', 'true').lower() == 'true',
            fallback_to_competitive=os.getenv('FALLBACK_TO_COMPETITIVE', 'true').lower() == 'true',
            max_plans_per_retailer=int(os.getenv('MAX_PLANS_PER_RETAILER', '50')),
            cache_duration_minutes=int(os.getenv('CACHE_DURATION_MINUTES', '30')),
            query_timeout_seconds=int(os.getenv('QUERY_TIMEOUT_SECONDS', '60')),
            max_results=int(os.getenv('MAX_RESULTS', '1000')),
            use_query_cache=os.getenv('USE_QUERY_CACHE', 'true').lower() == 'true',
            enable_etl_warehouse=os.getenv('ENABLE_ETL_WAREHOUSE', 'true').lower() == 'true',
            enable_api_supplement=os.getenv('ENABLE_API_SUPPLEMENT', 'true').lower() == 'true',
            enable_detailed_logging=os.getenv('ENABLE_DETAILED_LOGGING', 'false').lower() == 'true',
            enable_performance_monitoring=os.getenv('ENABLE_PERFORMANCE_MONITORING', 'true').lower() == 'true'
        )
    
    def save_config(self, config: ETLConfig):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            # Convert to dict and save
            config_dict = {
                'project_id': config.project_id,
                'dataset_id': config.dataset_id,
                'credentials_path': config.credentials_path,
                'use_default_credentials': config.use_default_credentials,
                'fallback_to_api': config.fallback_to_api,
                'fallback_to_competitive': config.fallback_to_competitive,
                'max_plans_per_retailer': config.max_plans_per_retailer,
                'cache_duration_minutes': config.cache_duration_minutes,
                'query_timeout_seconds': config.query_timeout_seconds,
                'max_results': config.max_results,
                'use_query_cache': config.use_query_cache,
                'min_usage_rate': config.min_usage_rate,
                'max_usage_rate': config.max_usage_rate,
                'min_supply_charge': config.min_supply_charge,
                'max_supply_charge': config.max_supply_charge,
                'enable_etl_warehouse': config.enable_etl_warehouse,
                'enable_api_supplement': config.enable_api_supplement,
                'enable_detailed_logging': config.enable_detailed_logging,
                'enable_performance_monitoring': config.enable_performance_monitoring
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=2)
            
            print(f"✅ Configuration saved to {self.config_file}")
            
        except Exception as e:
            print(f"❌ Failed to save configuration: {e}")
    
    def get_config(self) -> ETLConfig:
        """Get current configuration"""
        return self.config
    
    def update_config(self, **kwargs):
        """Update configuration with new values"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                print(f"⚠️  Unknown configuration key: {key}")
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration"""
        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check required fields
        if not self.config.project_id:
            validation_results['errors'].append("project_id is required")
        
        if not self.config.dataset_id:
            validation_results['errors'].append("dataset_id is required")
        
        # Check credentials
        if not self.config.use_default_credentials and not self.config.credentials_path:
            validation_results['errors'].append("credentials_path required when not using default credentials")
        
        if self.config.credentials_path and not os.path.exists(self.config.credentials_path):
            validation_results['errors'].append(f"Credentials file not found: {self.config.credentials_path}")
        
        # Check numeric ranges
        if not (0.05 <= self.config.min_usage_rate <= 0.50):
            validation_results['warnings'].append("min_usage_rate outside typical range (0.05-0.50)")
        
        if not (0.20 <= self.config.max_usage_rate <= 1.00):
            validation_results['warnings'].append("max_usage_rate outside typical range (0.20-1.00)")
        
        # Check feature combinations
        if not self.config.enable_etl_warehouse and not self.config.fallback_to_api:
            validation_results['errors'].append("At least one data source must be enabled")
        
        validation_results['valid'] = len(validation_results['errors']) == 0
        
        return validation_results


def setup_etl_environment(environment: str = 'development') -> ETLConfig:
    """
    Setup ETL environment configuration
    
    Args:
        environment: 'development', 'staging', or 'production'
    
    Returns:
        Configured ETLConfig instance
    """
    
    environment_configs = {
        'development': {
            'project_id': 'wattsmybill-dev',
            'dataset_id': 'energy_plans',
            'use_default_credentials': True,
            'fallback_to_api': True,
            'fallback_to_competitive': True,
            'max_plans_per_retailer': 30,
            'cache_duration_minutes': 15,
            'enable_detailed_logging': True,
            'enable_performance_monitoring': True
        },
        
        'staging': {
            'project_id': 'wattsmybill-staging',
            'dataset_id': 'energy_plans',
            'use_default_credentials': True,
            'fallback_to_api': True,
            'fallback_to_competitive': True,
            'max_plans_per_retailer': 50,
            'cache_duration_minutes': 30,
            'enable_detailed_logging': False,
            'enable_performance_monitoring': True
        },
        
        'production': {
            'project_id': 'wattsmybill-prod',
            'dataset_id': 'energy_plans',
            'use_default_credentials': False,
            'credentials_path': '/etc/secrets/bigquery-credentials.json',
            'fallback_to_api': True,
            'fallback_to_competitive': True,
            'max_plans_per_retailer': 100,
            'cache_duration_minutes': 60,
            'query_timeout_seconds': 120,
            'enable_detailed_logging': False,
            'enable_performance_monitoring': True
        }
    }
    
    if environment not in environment_configs:
        raise ValueError(f"Unknown environment: {environment}. Use 'development', 'staging', or 'production'")
    
    config_data = environment_configs[environment]
    config = ETLConfig(**config_data)
    
    print(f"🔧 ETL environment configured for: {environment}")
    print(f"   Project ID: {config.project_id}")
    print(f"   Dataset ID: {config.dataset_id}")
    print(f"   Max Plans per Retailer: {config.max_plans_per_retailer}")
    print(f"   Cache Duration: {config.cache_duration_minutes} minutes")
    
    return config


def create_sample_config_file(file_path: str = "etl_config.json"):
    """Create a sample configuration file"""
    
    sample_config = {
        "project_id": "wattsmybill-dev",
        "dataset_id": "energy_plans",
        "credentials_path": null,
        "use_default_credentials": True,
        "fallback_to_api": True,
        "fallback_to_competitive": True,
        "max_plans_per_retailer": 50,
        "cache_duration_minutes": 30,
        "query_timeout_seconds": 60,
        "max_results": 1000,
        "use_query_cache": True,
        "min_usage_rate": 0.10,
        "max_usage_rate": 0.80,
        "min_supply_charge": 0.50,
        "max_supply_charge": 3.00,
        "enable_etl_warehouse": True,
        "enable_api_supplement": True,
        "enable_detailed_logging": False,
        "enable_performance_monitoring": True
    }
    
    try:
        with open(file_path, 'w') as f:
            json.dump(sample_config, f, indent=2)
        
        print(f"✅ Sample configuration created: {file_path}")
        print("📝 Edit this file to customize your ETL settings")
        
    except Exception as e:
        print(f"❌ Failed to create sample config: {e}")


def validate_bigquery_access(project_id: str, dataset_id: str) -> Dict[str, Any]:
    """
    Validate BigQuery access and permissions
    
    Args:
        project_id: BigQuery project ID
        dataset_id: BigQuery dataset ID
    
    Returns:
        Validation results
    """
    
    validation_results = {
        'project_access': False,
        'dataset_access': False,
        'tables_accessible': [],
        'missing_tables': [],
        'errors': []
    }
    
    try:
        from google.cloud import bigquery
        from google.cloud.exceptions import NotFound, Forbidden
        
        client = bigquery.Client(project=project_id)
        
        # Test project access
        try:
            client.query("SELECT 1").result()
            validation_results['project_access'] = True
        except Exception as e:
            validation_results['errors'].append(f"Project access failed: {e}")
        
        # Test dataset access
        try:
            dataset_ref = client.dataset(dataset_id)
            dataset = client.get_dataset(dataset_ref)
            validation_results['dataset_access'] = True
        except NotFound:
            validation_results['errors'].append(f"Dataset not found: {project_id}.{dataset_id}")
        except Forbidden:
            validation_results['errors'].append(f"No permission to access dataset: {project_id}.{dataset_id}")
        except Exception as e:
            validation_results['errors'].append(f"Dataset access failed: {e}")
        
        # Test table access
        required_tables = [
            'plan_contract_details',
            'tariff_rates_comprehensive',
            'solar_feed_in_tariffs',
            'plan_fees'
        ]
        
        for table_name in required_tables:
            try:
                table_ref = client.dataset(dataset_id).table(table_name)
                table = client.get_table(table_ref)
                validation_results['tables_accessible'].append(table_name)
            except NotFound:
                validation_results['missing_tables'].append(table_name)
            except Exception as e:
                validation_results['errors'].append(f"Table {table_name} access failed: {e}")
        
    except ImportError:
        validation_results['errors'].append("google-cloud-bigquery package not installed")
    except Exception as e:
        validation_results['errors'].append(f"BigQuery validation failed: {e}")
    
    return validation_results


def setup_development_environment():
    """Quick setup for development environment"""
    
    print("🔧 Setting up ETL Development Environment")
    print("=" * 50)
    
    # Create sample config
    create_sample_config_file()
    
    # Setup development config
    config = setup_etl_environment('development')
    
    # Validate BigQuery access
    print("\n🔍 Validating BigQuery Access...")
    validation = validate_bigquery_access(config.project_id, config.dataset_id)
    
    if validation['project_access']:
        print("✅ Project access: OK")
    else:
        print("❌ Project access: FAILED")
    
    if validation['dataset_access']:
        print("✅ Dataset access: OK")
    else:
        print("❌ Dataset access: FAILED")
    
    print(f"✅ Accessible tables: {len(validation['tables_accessible'])}")
    for table in validation['tables_accessible']:
        print(f"   - {table}")
    
    if validation['missing_tables']:
        print(f"❌ Missing tables: {len(validation['missing_tables'])}")
        for table in validation['missing_tables']:
            print(f"   - {table}")
    
    if validation['errors']:
        print(f"⚠️  Validation errors:")
        for error in validation['errors']:
            print(f"   - {error}")
    
    # Final status
    if validation['project_access'] and validation['dataset_access'] and len(validation['tables_accessible']) >= 3:
        print("\n🎉 Development environment ready!")
        print("💡 You can now use the Enhanced Market Researcher Agent with ETL integration")
        return True
    else:
        print("\n⚠️  Development environment needs attention")
        print("🔧 Please resolve the validation errors above")
        return False


if __name__ == "__main__":
    # Run development setup
    setup_development_environment()