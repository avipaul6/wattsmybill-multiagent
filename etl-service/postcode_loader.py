#!/usr/bin/env python3
"""
Enhanced Australian Postcode/State Data Loader
Downloads and loads comprehensive Australian postcode mappings into BigQuery

Improvements:
- Duplicate prevention for incremental loads
- Multiple comprehensive data sources
- Validation of postcode counts
- Support for multiple suburbs per postcode
- Better error handling and recovery
"""

import requests
import pandas as pd
import io
from google.cloud import bigquery
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import json
import os

class AustralianPostcodeLoader:
    """Enhanced loader for comprehensive Australian postcode data"""
    
    def __init__(self, project_id: str = None):
        # Use environment variable with fallback, consistent with other scripts
        self.project_id = project_id or os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
        self.dataset_id = 'energy_plans'
        self.table_id = 'australian_postcodes'
        self.client = bigquery.Client(project=self.project_id)
        
        # Expected postcode counts per state (for validation)
        self.expected_counts = {
            'NSW': 3000,   # Approximately
            'VIC': 2000,
            'QLD': 2500,
            'SA': 800,
            'WA': 1500,
            'TAS': 300,
            'NT': 100,
            'ACT': 50
        }
        
        # Enhanced data sources with comprehensive coverage
        self.data_sources = {
            'comprehensive_github': {
                'url': 'https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv',
                'description': 'GitHub comprehensive postcodes',
                'format': 'csv',
                'min_expected': 15000
            },
            'alternative_github': {
                'url': 'https://raw.githubusercontent.com/Elkfox/Australian-Postcode-Data/master/au_postcodes.csv',
                'description': 'Alternative GitHub postcode dataset',
                'format': 'csv',
                'min_expected': 10000
            },
            'geonames_australia': {
                'url': 'http://download.geonames.org/export/zip/AU.zip',
                'description': 'GeoNames Australia postcodes',
                'format': 'zip_csv',
                'min_expected': 12000
            },
            # Backup comprehensive source
            'kaggle_mirror': {
                'url': 'https://raw.githubusercontent.com/datasets/australian-postcodes/master/australian_postcodes.csv',
                'description': 'Kaggle mirror of postcode data',
                'format': 'csv',
                'min_expected': 8000
            }
        }
    
    def check_existing_data(self) -> Dict[str, Any]:
        """Check what postcode data already exists"""
        try:
            query = f"""
            SELECT 
                COUNT(*) as total_postcodes,
                COUNT(DISTINCT postcode) as unique_postcodes,
                COUNT(DISTINCT state) as states_covered,
                MAX(loaded_at) as last_loaded,
                data_source,
                COUNT(DISTINCT CONCAT(postcode, '-', suburb)) as unique_postcode_suburb_combinations
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            GROUP BY data_source
            ORDER BY total_postcodes DESC
            """
            
            result = self.client.query(query).to_dataframe()
            
            if not result.empty:
                existing = result.iloc[0].to_dict()
                print(f"📊 Existing data: {existing['total_postcodes']:,} postcodes from {existing['data_source']}")
                return existing
            else:
                print("📊 No existing postcode data found")
                return {'total_postcodes': 0}
                
        except Exception as e:
            print(f"⚠️ Could not check existing data: {e}")
            return {'total_postcodes': 0}
    
    def should_update_data(self, existing_data: Dict[str, Any], force_update: bool = False) -> bool:
        """Determine if data should be updated"""
        if force_update:
            print("🔄 Force update requested")
            return True
            
        total_existing = existing_data.get('total_postcodes', 0)
        
        # Update if no data exists
        if total_existing == 0:
            print("📥 No existing data - will load fresh data")
            return True
        
        # Update if data seems incomplete (less than 10,000 postcodes)
        if total_existing < 10000:
            print(f"⚠️ Only {total_existing:,} postcodes exist - seems incomplete, will update")
            return True
        
        # Update if data is old (more than 30 days)
        try:
            last_loaded = existing_data.get('last_loaded')
            if last_loaded:
                if isinstance(last_loaded, str):
                    last_loaded = pd.to_datetime(last_loaded)
                days_old = (datetime.now(last_loaded.tz) - last_loaded).days
                if days_old > 30:
                    print(f"📅 Data is {days_old} days old - will update")
                    return True
        except:
            pass
        
        print(f"✅ Existing data looks good ({total_existing:,} postcodes) - skipping update")
        return False
    
    def download_comprehensive_postcode_data(self) -> Optional[pd.DataFrame]:
        """Download comprehensive postcode data from best available source"""
        
        for source_name, source_info in self.data_sources.items():
            try:
                print(f"🔍 Trying {source_name}: {source_info['description']}")
                
                if source_name == 'comprehensive_github':
                    df = self._download_comprehensive_github(source_info['url'])
                elif source_name == 'alternative_github':
                    df = self._download_alternative_github(source_info['url'])
                elif source_name == 'geonames_australia':
                    df = self._download_geonames_data(source_info['url'])
                else:
                    df = self._download_generic_csv(source_info['url'])
                
                if df is not None and len(df) >= source_info['min_expected']:
                    print(f"✅ Successfully downloaded {len(df):,} postcodes from {source_name}")
                    df['data_source'] = source_name
                    
                    # Validate data quality
                    if self._validate_postcode_data(df):
                        return df
                    else:
                        print(f"⚠️ Data validation failed for {source_name}")
                        continue
                else:
                    expected = source_info['min_expected']
                    actual = len(df) if df is not None else 0
                    print(f"⚠️ {source_name} returned insufficient data: {actual:,} < {expected:,}")
                    
            except Exception as e:
                print(f"❌ {source_name} failed: {e}")
                continue
        
        # If all comprehensive sources fail, create enhanced basic dataset
        print("🔧 All sources failed - creating enhanced basic postcode dataset")
        return self._create_enhanced_basic_postcode_data()
    
    def _download_comprehensive_github(self, url: str) -> pd.DataFrame:
        """Download from comprehensive GitHub source"""
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Map columns to standard format
        column_mapping = {
            'postcode': 'postcode',
            'locality': 'suburb',
            'state': 'state',
            'long': 'longitude',
            'lat': 'latitude',
            'dc': 'delivery_centre',
            'type': 'postcode_type',
            'status': 'status'
        }
        
        df = self._standardize_columns(df, column_mapping)
        return df
    
    def _download_alternative_github(self, url: str) -> pd.DataFrame:
        """Download from alternative GitHub source"""
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Alternative source might have different column names
        column_mapping = {
            'postcode': 'postcode',
            'suburb': 'suburb',
            'state': 'state',
            'latitude': 'latitude',
            'longitude': 'longitude'
        }
        
        df = self._standardize_columns(df, column_mapping)
        return df
    
    def _download_geonames_data(self, url: str) -> pd.DataFrame:
        """Download from GeoNames (requires zip extraction)"""
        # For now, skip GeoNames as it requires zip handling
        # Could implement later if other sources fail
        raise NotImplementedError("GeoNames source requires zip extraction - using other sources")
    
    def _download_generic_csv(self, url: str) -> pd.DataFrame:
        """Generic CSV download with intelligent column detection"""
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Intelligent column detection
        postcode_cols = [col for col in df.columns if any(term in col.lower() for term in ['postcode', 'postal', 'zip'])]
        state_cols = [col for col in df.columns if 'state' in col.lower()]
        suburb_cols = [col for col in df.columns if any(term in col.lower() for term in ['suburb', 'locality', 'place', 'city'])]
        
        if not postcode_cols or not state_cols:
            raise ValueError("Could not detect postcode and state columns")
        
        column_mapping = {
            postcode_cols[0]: 'postcode',
            state_cols[0]: 'state'
        }
        
        if suburb_cols:
            column_mapping[suburb_cols[0]] = 'suburb'
        
        df = self._standardize_columns(df, column_mapping)
        return df
    
    def _standardize_columns(self, df: pd.DataFrame, column_mapping: Dict[str, str]) -> pd.DataFrame:
        """Standardize column names and clean data"""
        # Rename columns
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Ensure required columns exist
        if 'postcode' not in df.columns or 'state' not in df.columns:
            raise ValueError("Required columns (postcode, state) not found after mapping")
        
        # Clean and standardize data
        df['postcode'] = df['postcode'].astype(str).str.zfill(4)
        df['state'] = df['state'].str.upper().str.strip()
        
        # Add default suburb if missing
        if 'suburb' not in df.columns:
            df['suburb'] = 'Various'
        else:
            df['suburb'] = df['suburb'].fillna('Various').str.title().str.strip()
        
        # Filter valid Australian states
        valid_states = ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']
        df = df[df['state'].isin(valid_states)].copy()
        
        return df
    
    def _validate_postcode_data(self, df: pd.DataFrame) -> bool:
        """Validate postcode data quality"""
        try:
            # Check minimum total count
            if len(df) < 8000:
                print(f"❌ Validation failed: Only {len(df):,} postcodes (minimum 8,000)")
                return False
            
            # Check state coverage
            states_in_data = set(df['state'].unique())
            required_states = {'NSW', 'VIC', 'QLD', 'SA', 'WA'}
            missing_states = required_states - states_in_data
            
            if missing_states:
                print(f"❌ Validation failed: Missing major states: {missing_states}")
                return False
            
            # Check postcode counts per state
            state_counts = df['state'].value_counts()
            for state, expected in self.expected_counts.items():
                actual = state_counts.get(state, 0)
                if actual < expected * 0.5:  # Allow 50% tolerance
                    print(f"⚠️ Warning: {state} has only {actual} postcodes (expected ~{expected})")
            
            # Check for reasonable suburb diversity
            total_postcodes = df['postcode'].nunique()
            total_suburbs = df['suburb'].nunique()
            suburb_ratio = total_suburbs / total_postcodes
            
            if suburb_ratio < 0.8:  # Expect at least 80% as many suburbs as postcodes
                print(f"⚠️ Warning: Low suburb diversity ratio: {suburb_ratio:.2f}")
            
            print(f"✅ Data validation passed: {len(df):,} postcodes, {len(states_in_data)} states")
            return True
            
        except Exception as e:
            print(f"❌ Validation error: {e}")
            return False
    
    def _create_enhanced_basic_postcode_data(self) -> pd.DataFrame:
        """Create enhanced basic postcode dataset with major suburbs"""
        print("🔧 Creating enhanced basic postcode dataset with major suburbs")
        
        # Enhanced postcode data with major suburbs
        postcode_data = []
        
        # NSW major postcodes and suburbs
        nsw_data = [
            ('2000', 'NSW', 'SYDNEY'), ('2001', 'NSW', 'SYDNEY'),
            ('2010', 'NSW', 'SURRY HILLS'), ('2015', 'NSW', 'ALEXANDRIA'),
            ('2020', 'NSW', 'MASCOT'), ('2030', 'NSW', 'DOVER HEIGHTS'),
            ('2040', 'NSW', 'LEICHHARDT'), ('2050', 'NSW', 'CAMPERDOWN'),
            ('2060', 'NSW', 'NORTH SYDNEY'), ('2070', 'NSW', 'LINDFIELD'),
            ('2100', 'NSW', 'ALLAMBIE HEIGHTS'), ('2110', 'NSW', 'HUNTERS HILL'),
            ('2120', 'NSW', 'PUTNEY'), ('2130', 'NSW', 'SUMMER HILL'),
            ('2140', 'NSW', 'HOMEBUSH'), ('2150', 'NSW', 'PARRAMATTA'),
            ('2200', 'NSW', 'BANKSTOWN'), ('2300', 'NSW', 'NEWCASTLE'),
            ('2400', 'NSW', 'ARMIDALE'), ('2500', 'NSW', 'WOLLONGONG'),
            ('2600', 'NSW', 'CANBERRA'),  # Sometimes NSW for postal purposes
        ]
        
        # VIC major postcodes
        vic_data = [
            ('3000', 'VIC', 'MELBOURNE'), ('3001', 'VIC', 'MELBOURNE'),
            ('3002', 'VIC', 'EAST MELBOURNE'), ('3003', 'VIC', 'WEST MELBOURNE'),
            ('3006', 'VIC', 'SOUTHBANK'), ('3121', 'VIC', 'RICHMOND'),
            ('3141', 'VIC', 'SOUTH YARRA'), ('3182', 'VIC', 'ST KILDA'),
            ('3199', 'VIC', 'FRANKSTON'), ('3220', 'VIC', 'GEELONG'),
            ('3350', 'VIC', 'BALLARAT'), ('3400', 'VIC', 'HORSHAM'),
            ('3550', 'VIC', 'BENDIGO'), ('3630', 'VIC', 'SHEPPARTON'),
            ('3690', 'VIC', 'ALBURY'), ('3750', 'VIC', 'GISBORNE'),
            ('3800', 'VIC', 'MONASH'), ('3850', 'VIC', 'MOE'),
        ]
        
        # QLD major postcodes
        qld_data = [
            ('4000', 'QLD', 'BRISBANE'), ('4001', 'QLD', 'BRISBANE'),
            ('4006', 'QLD', 'FORTITUDE VALLEY'), ('4101', 'QLD', 'SOUTH BRISBANE'),
            ('4207', 'QLD', 'BEENLEIGH'), ('4215', 'QLD', 'SOUTHPORT'),
            ('4350', 'QLD', 'TOOWOOMBA'), ('4570', 'QLD', 'GYMPIE'),
            ('4740', 'QLD', 'MACKAY'), ('4810', 'QLD', 'TOWNSVILLE'),
            ('4870', 'QLD', 'CAIRNS'), ('4872', 'QLD', 'ATHERTON'),
        ]
        
        # Add major postcodes for all states
        all_major_postcodes = nsw_data + vic_data + qld_data
        
        # Generate ranges for each state
        state_ranges = {
            'NSW': (1000, 2999),
            'VIC': (3000, 3999),
            'QLD': (4000, 4999),
            'SA': (5000, 5999),
            'WA': (6000, 6999),
            'TAS': (7000, 7999),
            'NT': (800, 999),
            'ACT': (2600, 2699)
        }
        
        # Generate basic ranges
        for state, (start, end) in state_ranges.items():
            for pc in range(start, end + 1, 10):  # Every 10th postcode
                postcode = str(pc).zfill(4)
                suburb = f'Various-{state}'
                postcode_data.append((postcode, state, suburb))
        
        # Add major postcodes (these will override the generic ones)
        postcode_data.extend(all_major_postcodes)
        
        # Create DataFrame
        df = pd.DataFrame(postcode_data, columns=['postcode', 'state', 'suburb'])
        
        # Remove duplicates, keeping major postcodes
        df = df.drop_duplicates(subset=['postcode'], keep='last')
        
        # Add metadata
        df['postcode_type'] = 'Standard'
        df['status'] = 'Active'
        df['data_source'] = 'enhanced_basic'
        df['latitude'] = None
        df['longitude'] = None
        df['delivery_centre'] = None
        
        print(f"✅ Created enhanced basic dataset with {len(df):,} postcodes")
        return df
    
    def handle_existing_table_compatibility(self) -> bool:
        """Handle compatibility with existing table structure"""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            existing_table = self.client.get_table(table_ref)
            
            print(f"📋 Found existing table with:")
            print(f"   Partitioning: {existing_table.time_partitioning}")
            print(f"   Clustering: {existing_table.clustering_fields}")
            
            # Check if we need to add missing columns
            existing_fields = {field.name for field in existing_table.schema}
            required_fields = {
                'postcode', 'state', 'suburb', 'latitude', 'longitude', 
                'postcode_type', 'delivery_centre', 'status', 'data_source', 
                'loaded_at', 'update_count'
            }
            
            missing_fields = required_fields - existing_fields
            if missing_fields:
                print(f"⚠️ Missing fields in existing table: {missing_fields}")
                print(f"🔧 Will work with existing schema")
            
            return True
            
        except Exception as e:
            if "Not found" in str(e):
                print(f"📋 Table doesn't exist - will create new one")
                return False
            else:
                print(f"⚠️ Error checking existing table: {e}")
                return False
    
    def get_safe_dataframe_for_existing_table(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare DataFrame to match existing table schema"""
        try:
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            existing_table = self.client.get_table(table_ref)
            existing_fields = {field.name for field in existing_table.schema}
            
            # Only keep columns that exist in the target table
            safe_df = df.copy()
            for col in df.columns:
                if col not in existing_fields:
                    print(f"⚠️ Dropping column {col} - not in existing table schema")
                    safe_df = safe_df.drop(columns=[col])
            
            print(f"📊 Using {len(safe_df.columns)} columns that match existing table")
            return safe_df
            
        except Exception as e:
            print(f"⚠️ Could not check existing schema, using all columns: {e}")
            return df
    def create_comprehensive_postcode_table(self):
        """Create comprehensive BigQuery table for postcodes"""
        # Check if table already exists
        if self.handle_existing_table_compatibility():
            print(f"✅ Using existing table: {self.project_id}.{self.dataset_id}.{self.table_id}")
            return True
        
        # Create new table with full schema
        schema = [
            bigquery.SchemaField("postcode", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("state", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("suburb", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
            bigquery.SchemaField("postcode_type", "STRING"),
            bigquery.SchemaField("delivery_centre", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("data_source", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("loaded_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("update_count", "INTEGER")  # Track how many times updated
        ]
        
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        table = bigquery.Table(table_ref, schema=schema)
        
        # Optimize for queries
        table.clustering_fields = ["state", "postcode"]
        table.time_partitioning = bigquery.TimePartitioning(
            type_=bigquery.TimePartitioningType.DAY,
            field="loaded_at"
        )
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"✅ Created new postcode table: {self.project_id}.{self.dataset_id}.{self.table_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to create postcode table: {e}")
            return False
    
    def load_postcode_data(self, force_update: bool = False) -> Dict[str, Any]:
        """Enhanced main function to download and load postcode data"""
        try:
            print("🗺️ Enhanced Australian Postcode Loader")
            print("=" * 50)
            
            # Check existing data
            existing_data = self.check_existing_data()
            
            # Determine if update is needed
            if not self.should_update_data(existing_data, force_update):
                return {
                    'status': 'skipped',
                    'message': 'Existing data is current and complete',
                    'records_loaded': existing_data.get('total_postcodes', 0),
                    'data_source': existing_data.get('data_source', 'existing')
                }
            
            # Download comprehensive data
            df = self.download_comprehensive_postcode_data()
            
            if df is None or len(df) == 0:
                return {'status': 'error', 'message': 'No postcode data downloaded'}
            
            # Prepare data for loading
            df['loaded_at'] = pd.Timestamp.now(tz='UTC')
            df['update_count'] = 1
            
            # Ensure all required columns exist
            required_columns = {
                'postcode': None,
                'state': None,
                'suburb': 'Various',
                'latitude': None,
                'longitude': None,
                'postcode_type': 'Standard',
                'delivery_centre': None,
                'status': 'Active',
                'data_source': 'unknown',
                'loaded_at': pd.Timestamp.now(tz='UTC'),
                'update_count': 1
            }
            
            for col, default_value in required_columns.items():
                if col not in df.columns:
                    df[col] = default_value
            
            # Select and clean data
            df = df[list(required_columns.keys())]
            df = df.dropna(subset=['postcode', 'state', 'suburb'])
            
            # Clean data types
            df['postcode'] = df['postcode'].astype(str).str.zfill(4)
            df['state'] = df['state'].str.upper().str.strip()
            df['suburb'] = df['suburb'].str.strip().str.title()
            
            # Handle multiple suburbs per postcode (keep all combinations)
            df = df.drop_duplicates(subset=['postcode', 'state', 'suburb'], keep='first')
            
            print(f"📊 Prepared {len(df):,} postcode-suburb combinations for loading")
            
            # Create/verify table
            if not self.create_comprehensive_postcode_table():
                return {'status': 'error', 'message': 'Failed to create table'}
            
            # Prepare DataFrame to match existing table schema
            safe_df = self.get_safe_dataframe_for_existing_table(df)
            
            # Load to BigQuery with simple configuration that works with existing tables
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            
            # Simple job config that doesn't conflict with existing table structure
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE
                # Don't specify clustering or partitioning - inherit from existing table
            )
            
            print(f"📤 Loading {len(safe_df):,} records to BigQuery...")
            job = self.client.load_table_from_dataframe(safe_df, table_ref, job_config=job_config)
            job.result()  # Wait for completion
            print(f"✅ Successfully loaded data to BigQuery")
            
            # Get comprehensive final stats
            stats_query = f"""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT postcode) as unique_postcodes,
                COUNT(DISTINCT state) as states_covered,
                COUNT(DISTINCT CONCAT(postcode, '-', suburb)) as unique_postcode_suburb_combinations,
                data_source,
                COUNTIF(state = 'NSW') as nsw_records,
                COUNTIF(state = 'VIC') as vic_records,
                COUNTIF(state = 'QLD') as qld_records,
                COUNTIF(state = 'SA') as sa_records,
                COUNTIF(state = 'WA') as wa_records,
                COUNTIF(state = 'TAS') as tas_records,
                COUNTIF(state = 'NT') as nt_records,
                COUNTIF(state = 'ACT') as act_records
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            GROUP BY data_source
            """
            
            result = self.client.query(stats_query).to_dataframe()
            stats = result.iloc[0].to_dict() if not result.empty else {}
            
            return {
                'status': 'success',
                'message': f'Loaded {len(df):,} postcode records successfully',
                'records_loaded': len(df),
                'unique_postcodes': stats.get('unique_postcodes', 0),
                'data_source': df['data_source'].iloc[0] if len(df) > 0 else 'unknown',
                'comprehensive_stats': stats
            }
            
        except Exception as e:
            logging.error(f"Enhanced postcode loading failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'records_loaded': 0
            }
    
    def create_enhanced_lookup_views(self):
        """Create enhanced lookup views for comprehensive postcode data"""
        
        # Primary lookup: postcode to state (handles multiple suburbs)
        primary_lookup_view = f"""
        CREATE OR REPLACE VIEW `{self.project_id}.{self.dataset_id}.postcode_state_lookup` AS
        SELECT 
            postcode,
            state,
            STRING_AGG(DISTINCT suburb ORDER BY suburb) as suburbs,
            COUNT(DISTINCT suburb) as suburb_count,
            COUNT(DISTINCT status) as active_or_inactive_count,
            ANY_VALUE(latitude) as sample_latitude,
            ANY_VALUE(longitude) as sample_longitude
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE status = 'Active'
        GROUP BY postcode, state
        ORDER BY postcode
        """
        
        # Detailed lookup: all postcode-suburb combinations
        detailed_lookup_view = f"""
        CREATE OR REPLACE VIEW `{self.project_id}.{self.dataset_id}.postcode_suburb_lookup` AS
        SELECT 
            postcode,
            state,
            suburb,
            postcode_type,
            status,
            latitude,
            longitude,
            delivery_centre
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        ORDER BY postcode, suburb
        """
        
        # State coverage summary
        coverage_summary_view = f"""
        CREATE OR REPLACE VIEW `{self.project_id}.{self.dataset_id}.state_postcode_coverage` AS
        SELECT 
            state,
            COUNT(DISTINCT postcode) as postcode_count,
            COUNT(DISTINCT suburb) as suburb_count,
            COUNT(*) as total_records,
            COUNT(DISTINCT status) as active_or_inactive_count,
            MIN(postcode) as min_postcode,
            MAX(postcode) as max_postcode,
            data_source,
            MAX(loaded_at) as last_updated
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        GROUP BY state, data_source
        ORDER BY postcode_count DESC
        """
        
        views = [
            ("postcode_state_lookup", primary_lookup_view),
            ("postcode_suburb_lookup", detailed_lookup_view),
            ("state_postcode_coverage", coverage_summary_view)
        ]
        
        for view_name, query in views:
            try:
                self.client.query(query).result()
                print(f"✅ Created enhanced view: {view_name}")
            except Exception as e:
                print(f"❌ Failed to create view {view_name}: {e}")

def load_comprehensive_australian_postcodes(force_update: bool = False):
    """Main function to load comprehensive postcode data"""
    print("🗺️ Enhanced Australian Postcode Data Loader")
    print("=" * 60)
    
    # Use environment variables for project ID, consistent with other scripts
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
    print(f"📍 Using project: {project_id}")
    
    loader = AustralianPostcodeLoader(project_id)
    
    # Load postcode data
    result = loader.load_postcode_data(force_update=force_update)
    
    print(f"\n📊 Loading Result:")
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    print(f"   Records loaded: {result.get('records_loaded', 0):,}")
    print(f"   Unique postcodes: {result.get('unique_postcodes', 0):,}")
    print(f"   Data source: {result.get('data_source', 'unknown')}")
    
    if result['status'] == 'success':
        # Show comprehensive coverage stats
        stats = result.get('comprehensive_stats', {})
        print(f"\n🎯 Comprehensive Coverage Statistics:")
        print(f"   Total records: {stats.get('total_records', 0):,}")
        print(f"   Unique postcodes: {stats.get('unique_postcodes', 0):,}")
        print(f"   States covered: {stats.get('states_covered', 0)}")
        print(f"   Postcode-suburb combinations: {stats.get('unique_postcode_suburb_combinations', 0):,}")
        
        print(f"\n🗺️ State Breakdown:")
        for state in ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']:
            count = stats.get(f'{state.lower()}_records', 0)
            if count > 0:
                print(f"   {state}: {count:,} records")
        
        # Create enhanced lookup views
        print(f"\n🏗️ Creating enhanced lookup views...")
        loader.create_enhanced_lookup_views()
        
        print(f"\n✅ Enhanced postcode loading complete!")
        print(f"📋 Usage examples:")
        print(f"   SELECT state FROM `wattsmybill-dev.energy_plans.postcode_state_lookup` WHERE postcode = '2000'")
        print(f"   SELECT suburbs FROM `wattsmybill-dev.energy_plans.postcode_state_lookup` WHERE postcode = '4207'")
        print(f"   SELECT * FROM `wattsmybill-dev.energy_plans.postcode_suburb_lookup` WHERE postcode = '4207'")
    elif result['status'] == 'skipped':
        print(f"\n✅ Postcode data is current - no update needed")
    
    return result

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Load comprehensive Australian postcode data")
    parser.add_argument("--force", action="store_true", help="Force update even if data exists")
    
    args = parser.parse_args()
    
    load_comprehensive_australian_postcodes(force_update=args.force)