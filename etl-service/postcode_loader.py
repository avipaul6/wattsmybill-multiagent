#!/usr/bin/env python3
"""
Australian Postcode/State Data Loader
Downloads and loads Australian postcode mappings into BigQuery

Data sources:
1. Australia Post Official Data (free)
2. Australian Bureau of Statistics (ABS)
3. data.gov.au open datasets
"""

import requests
import pandas as pd
import io
from google.cloud import bigquery
from typing import Dict, List, Any
import logging

class AustralianPostcodeLoader:
    """Load Australian postcode data into BigQuery"""
    
    def __init__(self, project_id: str = 'wattsmybill-dev'):
        self.project_id = project_id
        self.dataset_id = 'energy_plans'
        self.table_id = 'australian_postcodes'
        self.client = bigquery.Client(project=project_id)
        
        # Data sources (in order of preference)
        self.data_sources = {
            'abs_official': {
                'url': 'https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs-edition-3/jul2021-jun2026/access-and-downloads/digital-boundary-files',
                'description': 'Australian Bureau of Statistics official data',
                'format': 'csv'
            },
            'australia_post': {
                'url': 'https://auspost.com.au/content/dam/auspost_corp/media/documents/australia-post-data-guide.pdf',
                'description': 'Australia Post official postcode data',
                'format': 'csv'
            },
            # Backup: Use a known working dataset
            'github_postcodes': {
                'url': 'https://raw.githubusercontent.com/matthewproctor/australianpostcodes/master/australian_postcodes.csv',
                'description': 'GitHub community-maintained postcodes',
                'format': 'csv'
            },
            # Alternative backup
            'data_gov_au': {
                'url': 'https://data.gov.au/geoserver/australian-postcodes/wfs?request=GetFeature&typeName=ckan_d534c0e9_a9bf_487b_ac8f_b7877a09d162&outputFormat=csv',
                'description': 'data.gov.au open dataset',
                'format': 'csv'
            }
        }
    
    def download_postcode_data(self) -> pd.DataFrame:
        """Download postcode data from available sources"""
        
        # Try each data source until one works
        for source_name, source_info in self.data_sources.items():
            try:
                print(f"🔍 Trying {source_name}: {source_info['description']}")
                
                if source_name == 'github_postcodes':
                    # This one we know works
                    df = self._download_github_postcodes(source_info['url'])
                elif source_name == 'data_gov_au':
                    df = self._download_data_gov_postcodes(source_info['url'])
                else:
                    # Generic CSV download
                    df = self._download_generic_csv(source_info['url'])
                
                if df is not None and len(df) > 1000:  # Sanity check
                    print(f"✅ Successfully downloaded {len(df):,} postcodes from {source_name}")
                    df['data_source'] = source_name
                    return df
                else:
                    print(f"⚠️  {source_name} returned insufficient data")
                    
            except Exception as e:
                print(f"❌ {source_name} failed: {e}")
                continue
        
        # If all else fails, create a basic dataset
        print("🔧 Creating basic postcode dataset as fallback")
        return self._create_basic_postcode_data()
    
    def _download_github_postcodes(self, url: str) -> pd.DataFrame:
        """Download from GitHub postcodes repository"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Standardize column names
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
        
        # Rename columns if they exist
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
        
        # Ensure required columns exist
        required_columns = ['postcode', 'state']
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"Required column {col} not found")
        
        # Clean data
        df['postcode'] = df['postcode'].astype(str).str.zfill(4)
        df['state'] = df['state'].str.upper().str.strip()
        
        return df
    
    def _download_data_gov_postcodes(self, url: str) -> pd.DataFrame:
        """Download from data.gov.au"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # data.gov.au might have different column names
        # Adapt based on actual structure
        if 'POSTCODE' in df.columns:
            df = df.rename(columns={'POSTCODE': 'postcode'})
        if 'STATE' in df.columns:
            df = df.rename(columns={'STATE': 'state'})
        if 'LOCALITY' in df.columns:
            df = df.rename(columns={'LOCALITY': 'suburb'})
        
        # Clean data
        df['postcode'] = df['postcode'].astype(str).str.zfill(4)
        df['state'] = df['state'].str.upper().str.strip()
        
        return df
    
    def _download_generic_csv(self, url: str) -> pd.DataFrame:
        """Generic CSV download with intelligent column detection"""
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        df = pd.read_csv(io.StringIO(response.text))
        
        # Try to detect postcode and state columns
        postcode_cols = [col for col in df.columns if 'postcode' in col.lower()]
        state_cols = [col for col in df.columns if 'state' in col.lower()]
        
        if not postcode_cols or not state_cols:
            raise ValueError("Could not detect postcode and state columns")
        
        # Rename to standard names
        df = df.rename(columns={
            postcode_cols[0]: 'postcode',
            state_cols[0]: 'state'
        })
        
        # Clean data
        df['postcode'] = df['postcode'].astype(str).str.zfill(4)
        df['state'] = df['state'].str.upper().str.strip()
        
        return df
    
    def _create_basic_postcode_data(self) -> pd.DataFrame:
        """Create basic postcode ranges as fallback"""
        print("🔧 Creating basic postcode-to-state mapping")
        
        # Australian postcode ranges by state
        postcode_ranges = [
            # NSW
            *[(str(pc).zfill(4), 'NSW') for pc in range(1000, 3000)],
            *[(str(pc).zfill(4), 'NSW') for pc in range(2000, 3000)],
            
            # VIC  
            *[(str(pc).zfill(4), 'VIC') for pc in range(3000, 4000)],
            *[(str(pc).zfill(4), 'VIC') for pc in range(8000, 8999)],
            
            # QLD
            *[(str(pc).zfill(4), 'QLD') for pc in range(4000, 5000)],
            *[(str(pc).zfill(4), 'QLD') for pc in range(9000, 9999)],
            
            # SA
            *[(str(pc).zfill(4), 'SA') for pc in range(5000, 6000)],
            
            # WA
            *[(str(pc).zfill(4), 'WA') for pc in range(6000, 7000)],
            
            # TAS
            *[(str(pc).zfill(4), 'TAS') for pc in range(7000, 8000)],
            
            # NT
            *[(str(pc).zfill(4), 'NT') for pc in range(800, 900)],
            
            # ACT
            *[(str(pc).zfill(4), 'ACT') for pc in range(200, 300)],
            *[(str(pc).zfill(4), 'ACT') for pc in range(2600, 2700)],
        ]
        
        df = pd.DataFrame(postcode_ranges, columns=['postcode', 'state'])
        df['suburb'] = 'Various'
        df['data_source'] = 'basic_ranges'
        df['postcode_type'] = 'Standard'
        
        return df
    
    def create_postcode_table(self):
        """Create BigQuery table for postcodes"""
        schema = [
            bigquery.SchemaField("postcode", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("state", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("suburb", "STRING"),
            bigquery.SchemaField("latitude", "FLOAT"),
            bigquery.SchemaField("longitude", "FLOAT"),
            bigquery.SchemaField("postcode_type", "STRING"),
            bigquery.SchemaField("delivery_centre", "STRING"),
            bigquery.SchemaField("status", "STRING"),
            bigquery.SchemaField("data_source", "STRING"),
            bigquery.SchemaField("loaded_at", "TIMESTAMP", mode="REQUIRED")
        ]
        
        table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
        table = bigquery.Table(table_ref, schema=schema)
        
        # Add clustering for better query performance
        table.clustering_fields = ["state", "postcode"]
        
        try:
            table = self.client.create_table(table, exists_ok=True)
            print(f"✅ Created postcode table: {self.project_id}.{self.dataset_id}.{self.table_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to create postcode table: {e}")
            return False
    
    def load_postcode_data(self) -> Dict[str, Any]:
        """Main function to download and load postcode data"""
        try:
            # Download data
            df = self.download_postcode_data()
            
            if df is None or len(df) == 0:
                return {'status': 'error', 'message': 'No postcode data downloaded'}
            
            # Add metadata
            df['loaded_at'] = pd.Timestamp.now(tz='UTC')
            
            # Ensure all required columns exist with defaults
            required_columns = {
                'postcode': None,
                'state': None,
                'suburb': 'Unknown',
                'latitude': None,
                'longitude': None,
                'postcode_type': 'Standard',
                'delivery_centre': None,
                'status': 'Active',
                'data_source': 'unknown',
                'loaded_at': pd.Timestamp.now(tz='UTC')
            }
            
            for col, default_value in required_columns.items():
                if col not in df.columns:
                    df[col] = default_value
            
            # Select only the columns we need
            df = df[list(required_columns.keys())]
            
            # Clean data
            df = df.dropna(subset=['postcode', 'state'])
            df['postcode'] = df['postcode'].astype(str).str.zfill(4)
            df['state'] = df['state'].str.upper().str.strip()
            
            # Remove duplicates (keep first occurrence)
            df = df.drop_duplicates(subset=['postcode', 'state'], keep='first')
            
            print(f"📊 Prepared {len(df):,} postcode records for loading")
            
            # Create table
            if not self.create_postcode_table():
                return {'status': 'error', 'message': 'Failed to create table'}
            
            # Load to BigQuery
            table_ref = self.client.dataset(self.dataset_id).table(self.table_id)
            
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,  # Replace all data
                clustering_fields=["state", "postcode"]
            )
            
            job = self.client.load_table_from_dataframe(df, table_ref, job_config=job_config)
            job.result()  # Wait for completion
            
            # Get final stats
            query = f"""
            SELECT 
                COUNT(*) as total_postcodes,
                COUNT(DISTINCT state) as states_covered,
                COUNT(DISTINCT CASE WHEN state = 'NSW' THEN postcode END) as nsw_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'VIC' THEN postcode END) as vic_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'QLD' THEN postcode END) as qld_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'SA' THEN postcode END) as sa_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'WA' THEN postcode END) as wa_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'TAS' THEN postcode END) as tas_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'NT' THEN postcode END) as nt_postcodes,
                COUNT(DISTINCT CASE WHEN state = 'ACT' THEN postcode END) as act_postcodes,
                data_source
            FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
            GROUP BY data_source
            """
            
            result = self.client.query(query).to_dataframe()
            
            return {
                'status': 'success',
                'message': f'Loaded {len(df):,} postcodes successfully',
                'records_loaded': len(df),
                'data_source': df['data_source'].iloc[0] if len(df) > 0 else 'unknown',
                'coverage_stats': result.to_dict('records')[0] if len(result) > 0 else {}
            }
            
        except Exception as e:
            logging.error(f"Postcode loading failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'records_loaded': 0
            }
    
    def create_postcode_lookup_views(self):
        """Create useful views for postcode lookups"""
        
        # View: Simple postcode to state lookup
        postcode_lookup_view = f"""
        CREATE OR REPLACE VIEW `{self.project_id}.{self.dataset_id}.postcode_state_lookup` AS
        SELECT 
            postcode,
            state,
            suburb,
            COUNT(*) as suburb_count
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE status = 'Active'
        GROUP BY postcode, state, suburb
        ORDER BY postcode, state
        """
        
        # View: State coverage summary
        state_coverage_view = f"""
        CREATE OR REPLACE VIEW `{self.project_id}.{self.dataset_id}.state_postcode_coverage` AS
        SELECT 
            state,
            COUNT(DISTINCT postcode) as postcode_count,
            MIN(postcode) as min_postcode,
            MAX(postcode) as max_postcode,
            COUNT(DISTINCT suburb) as suburb_count,
            data_source
        FROM `{self.project_id}.{self.dataset_id}.{self.table_id}`
        WHERE status = 'Active'
        GROUP BY state, data_source
        ORDER BY postcode_count DESC
        """
        
        views = [
            ("postcode_state_lookup", postcode_lookup_view),
            ("state_postcode_coverage", state_coverage_view)
        ]
        
        for view_name, query in views:
            try:
                self.client.query(query).result()
                print(f"✅ Created view: {view_name}")
            except Exception as e:
                print(f"❌ Failed to create view {view_name}: {e}")

def load_australian_postcodes():
    """Main function to load postcode data"""
    print("🗺️  Loading Australian Postcode Data")
    print("=" * 50)
    
    loader = AustralianPostcodeLoader()
    
    # Load postcode data
    result = loader.load_postcode_data()
    
    print(f"\n📊 Loading Result:")
    print(f"   Status: {result['status']}")
    print(f"   Message: {result['message']}")
    print(f"   Records loaded: {result.get('records_loaded', 0):,}")
    print(f"   Data source: {result.get('data_source', 'unknown')}")
    
    if result['status'] == 'success':
        # Show coverage stats
        coverage = result.get('coverage_stats', {})
        print(f"\n🎯 Coverage Statistics:")
        print(f"   Total postcodes: {coverage.get('total_postcodes', 0):,}")
        print(f"   States covered: {coverage.get('states_covered', 0)}")
        
        for state in ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT', 'ACT']:
            count = coverage.get(f'{state.lower()}_postcodes', 0)
            if count > 0:
                print(f"   {state}: {count:,} postcodes")
        
        # Create lookup views
        print(f"\n🏗️  Creating lookup views...")
        loader.create_postcode_lookup_views()
        
        print(f"\n✅ Postcode loading complete!")
        print(f"   You can now use postcode/state lookups in your queries")
        print(f"   Example: SELECT state FROM `wattsmybill-dev.energy_plans.postcode_state_lookup` WHERE postcode = '2000'")
    
    return result

if __name__ == "__main__":
    load_australian_postcodes()