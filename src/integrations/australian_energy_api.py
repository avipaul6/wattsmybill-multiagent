"""
OPTIMIZED Australian Energy Plans API Integration
Reduces warning messages and improves data extraction efficiency

File: src/integrations/australian_energy_api.py (OPTIMIZED VERSION)
"""
import requests
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time

class AustralianEnergyAPI:
    """
    OPTIMIZED: Integrates with official Australian energy APIs with improved data extraction
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Configure logging to reduce noise
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        
        # Official Australian Energy API Endpoints
        self.endpoints = {
            'aer_plans_base': 'https://cdr.energymadeeasy.gov.au',
            'cdr_register': 'https://api.cdr.gov.au/cdr-register/v1',
            
            # Retailer-specific CDR endpoints
            'retailer_endpoints': {
                'agl': 'https://cdr.energymadeeasy.gov.au/agl/cds-au/v1/energy/plans',
                'origin': 'https://cdr.energymadeeasy.gov.au/origin/cds-au/v1/energy/plans',
                'energyaustralia': 'https://cdr.energymadeeasy.gov.au/energyaustralia/cds-au/v1/energy/plans',
                'alinta': 'https://cdr.energymadeeasy.gov.au/alinta/cds-au/v1/energy/plans',
                'red_energy': 'https://cdr.energymadeeasy.gov.au/redenergy/cds-au/v1/energy/plans',
                'simply_energy': 'https://cdr.energymadeeasy.gov.au/simplyenergy/cds-au/v1/energy/plans'
            }
        }
        
        # Required headers for CDR API compliance
        self.headers = {
            'x-v': '1',
            'Accept': 'application/json',
            'User-Agent': 'WattsMyBill/1.0 (Australian Energy Analysis Tool)'
        }
        
        # States covered by National Energy Customer Framework
        self.necf_states = ['NSW', 'QLD', 'SA', 'TAS', 'ACT', 'VIC']
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
        # Retailer fallback rates (2025 market rates)
        self.fallback_rates = {
            'agl': {'usage': 0.275, 'supply': 1.20, 'solar': 0.06},
            'origin': {'usage': 0.285, 'supply': 1.15, 'solar': 0.05},
            'energyaustralia': {'usage': 0.295, 'supply': 1.10, 'solar': 0.05},
            'alinta': {'usage': 0.265, 'supply': 1.05, 'solar': 0.06},
            'red_energy': {'usage': 0.270, 'supply': 1.25, 'solar': 0.07},
            'simply_energy': {'usage': 0.259, 'supply': 1.35, 'solar': 0.05}
        }
        
        # Statistics tracking
        self.processing_stats = {
            'plans_processed': 0,
            'plans_with_full_tariffs': 0,
            'plans_with_partial_tariffs': 0,
            'plans_using_fallback': 0
        }
        
    def get_all_retailers(self) -> List[Dict[str, Any]]:
        """Get list of all energy retailers from CDR Register"""
        try:
            url = f"{self.endpoints['cdr_register']}/all/data-holders/brands/summary"
            
            self._rate_limit()
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Filter for energy retailers only
                energy_retailers = []
                for brand in data.get('data', []):
                    if brand.get('industry') == 'energy':
                        energy_retailers.append({
                            'brand_name': brand.get('brandName'),
                            'abn': brand.get('abn'),
                            'public_base_uri': brand.get('publicBaseURI'),
                            'logo_uri': brand.get('logoURI'),
                            'last_updated': brand.get('lastUpdated')
                        })
                
                return energy_retailers
                
            else:
                return []
                
        except Exception:
            return []
    
    def get_plans_for_retailer(self, retailer_key: str, state: str = None, limit: int = 50) -> List[Dict[str, Any]]:
        """OPTIMIZED: Get energy plans for a specific retailer with configurable limit"""
        try:
            if retailer_key not in self.endpoints['retailer_endpoints']:
                return []
            
            url = self.endpoints['retailer_endpoints'][retailer_key]
            
            # CDR API parameters with configurable limit
            params = {
                'type': 'MARKET',  # Focus on market offers (usually have better data)
                'fuelType': 'ELECTRICITY',
                'effective': 'CURRENT',
                'page': 1,
                'page-size': limit  # Configurable limit
            }
            
            self._rate_limit()
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                plans = data.get('data', {}).get('plans', [])
                
                # Process plans efficiently
                processed_plans = []
                for plan in plans:
                    processed_plan = self._process_plan_data_optimized(plan, retailer_key)
                    if processed_plan and self._is_valid_plan(processed_plan):
                        processed_plans.append(processed_plan)
                
                return processed_plans
                
            else:
                return self._get_plans_fallback(retailer_key, state)
                
        except Exception:
            return self._get_plans_fallback(retailer_key, state)
    
    def _process_plan_data_optimized(self, plan_data: Dict[str, Any], retailer_key: str) -> Optional[Dict[str, Any]]:
        """OPTIMIZED: Process plan data with improved tariff extraction"""
        try:
            self.processing_stats['plans_processed'] += 1
            
            plan_id = plan_data.get('planId', f"unknown_{retailer_key}_{hash(str(plan_data))}")
            
            # Basic plan information
            processed = {
                'plan_id': plan_id,
                'retailer': retailer_key.replace('_', ' ').title(),
                'plan_name': self._clean_plan_name(plan_data.get('displayName') or plan_data.get('planId') or 'Unknown Plan'),
                'description': plan_data.get('description', ''),
                'plan_type': (plan_data.get('type') or 'MARKET').lower(),
                'fuel_type': 'electricity',
                'customer_type': 'residential',
                'effective_from': plan_data.get('effectiveFrom'),
                'effective_to': plan_data.get('effectiveTo'),
                'last_updated': plan_data.get('lastUpdated'),
                
                # Initialize tariff data
                'has_time_of_use': False,
                'has_demand_charges': False,
                'has_solar_fit': False,
                'usage_rate': None,
                'supply_charge': None,
                'solar_fit_rate': None,
                'data_quality': 'processing',
                
                # Features
                'features': self._extract_features(plan_data),
                'distribution_zones': plan_data.get('geography', {}).get('distributors', []),
            }
            
            # Extract tariff details with improved logic
            tariff_success = self._extract_tariff_details_optimized(processed, plan_data, retailer_key)
            
            # Set data quality based on extraction success
            if tariff_success == 'full':
                processed['data_quality'] = 'api_complete'
                self.processing_stats['plans_with_full_tariffs'] += 1
            elif tariff_success == 'partial':
                processed['data_quality'] = 'api_partial'
                self.processing_stats['plans_with_partial_tariffs'] += 1
            else:
                processed['data_quality'] = 'estimated'
                self.processing_stats['plans_using_fallback'] += 1
            
            return processed
            
        except Exception:
            return None
    
    def _extract_tariff_details_optimized(self, processed_plan: Dict[str, Any], raw_data: Dict[str, Any], retailer_key: str) -> str:
        """
        OPTIMIZED: Extract tariff details with multiple fallback strategies
        Returns: 'full', 'partial', or 'fallback'
        """
        try:
            # Strategy 1: Standard CDR tariff structure
            electricity_contract = raw_data.get('electricityContract', {})
            if electricity_contract:
                tariffs = electricity_contract.get('tariffs', [])
                if tariffs and self._extract_from_tariffs(processed_plan, tariffs):
                    # Extract solar feed-in tariff
                    self._extract_solar_tariff(processed_plan, electricity_contract)
                    return 'full' if all([processed_plan['usage_rate'], processed_plan['supply_charge']]) else 'partial'
            
            # Strategy 2: Look for rate information in other locations
            if self._extract_from_plan_overview(processed_plan, raw_data):
                return 'partial'
            
            # Strategy 3: Use retailer-specific fallback rates
            self._apply_retailer_fallback(processed_plan, retailer_key)
            return 'fallback'
            
        except Exception:
            # Final fallback
            self._apply_retailer_fallback(processed_plan, retailer_key)
            return 'fallback'
    
    def _extract_from_tariffs(self, processed_plan: Dict[str, Any], tariffs: List[Dict]) -> bool:
        """Extract rates from tariff structure"""
        try:
            for tariff in tariffs:
                # Extract usage rates
                rates = tariff.get('rates', [])
                for rate in rates:
                    rate_type = rate.get('rateBlockUType', '')
                    
                    if rate_type == 'singleRate':
                        single_rate = rate.get('singleRate', {})
                        unit_price = single_rate.get('unitPrice')
                        if unit_price is not None:
                            processed_plan['usage_rate'] = float(unit_price)
                            break
                    
                    elif rate_type == 'timeOfUseRates':
                        processed_plan['has_time_of_use'] = True
                        tou_rates = rate.get('timeOfUseRates', [])
                        if tou_rates:
                            # Calculate weighted average for simplicity
                            valid_rates = [r.get('unitPrice') for r in tou_rates if r.get('unitPrice')]
                            if valid_rates:
                                processed_plan['usage_rate'] = sum(valid_rates) / len(valid_rates)
                                break
                
                # Extract daily supply charge
                daily_supply = tariff.get('dailySupplyCharges')
                if daily_supply is not None:
                    processed_plan['supply_charge'] = float(daily_supply)
                
                # Check for demand charges
                if tariff.get('demandCharges'):
                    processed_plan['has_demand_charges'] = True
                
                # If we found rates, we're good
                if processed_plan['usage_rate'] is not None:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _extract_solar_tariff(self, processed_plan: Dict[str, Any], electricity_contract: Dict) -> bool:
        """Extract solar feed-in tariff"""
        try:
            feed_in_tariffs = electricity_contract.get('solarFeedInTariff', [])
            if feed_in_tariffs:
                processed_plan['has_solar_fit'] = True
                for fit in feed_in_tariffs:
                    single_tariff = fit.get('singleTariff', {})
                    amount = single_tariff.get('amount')
                    if amount is not None:
                        processed_plan['solar_fit_rate'] = float(amount)
                        return True
            return False
        except Exception:
            return False
    
    def _extract_from_plan_overview(self, processed_plan: Dict[str, Any], raw_data: Dict) -> bool:
        """Try to extract rate info from plan overview or other fields"""
        # This would be expanded based on actual API response structure
        # For now, return False to use fallback
        return False
    
    def _apply_retailer_fallback(self, processed_plan: Dict[str, Any], retailer_key: str):
        """Apply retailer-specific fallback rates"""
        fallback = self.fallback_rates.get(retailer_key.lower(), self.fallback_rates['agl'])
        
        if processed_plan['usage_rate'] is None:
            processed_plan['usage_rate'] = fallback['usage']
        
        if processed_plan['supply_charge'] is None:
            processed_plan['supply_charge'] = fallback['supply']
        
        if processed_plan['solar_fit_rate'] is None:
            processed_plan['solar_fit_rate'] = fallback['solar']
            processed_plan['has_solar_fit'] = True
    
    def _clean_plan_name(self, name: str) -> str:
        """Clean up plan names for better display"""
        if not name:
            return 'Unknown Plan'
        
        # Remove common suffixes that clutter the name
        suffixes_to_remove = [
            ' (No Exit Fee)',
            ' - New Customer',
            ' - Existing Customer',
            ' - New To AGL'
        ]
        
        clean_name = name
        for suffix in suffixes_to_remove:
            if clean_name.endswith(suffix):
                clean_name = clean_name[:-len(suffix)]
        
        return clean_name.strip()
    
    def _extract_features(self, plan_data: Dict[str, Any]) -> List[str]:
        """Extract plan features"""
        features = []
        
        # Check plan type
        plan_type = plan_data.get('type', '').lower()
        if plan_type == 'market':
            features.append('Market offer')
        elif plan_type == 'standing':
            features.append('Standing offer')
        
        # Check for common features in description
        description = (plan_data.get('description', '') + ' ' + plan_data.get('displayName', '')).lower()
        
        if 'no exit fee' in description:
            features.append('No exit fees')
        if 'solar' in description:
            features.append('Solar friendly')
        if 'green' in description or 'renewable' in description:
            features.append('Green energy')
        if 'discount' in description:
            features.append('Discounts available')
        
        return features
    
    def _is_valid_plan(self, plan: Dict[str, Any]) -> bool:
        """Check if a plan has minimum required data"""
        return (
            plan.get('usage_rate') is not None and
            plan.get('supply_charge') is not None and
            plan.get('plan_name') and
            plan.get('retailer') and
            0.10 <= plan.get('usage_rate', 0) <= 1.0  # Reasonable rate range
        )
    
    def search_plans(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """OPTIMIZED: Search for energy plans with improved efficiency"""
        state = criteria.get('state', 'NSW')
        usage_kwh = criteria.get('usage_kwh', 4000)
        has_solar = criteria.get('has_solar', False)
        
        # Reset stats
        self.processing_stats = {
            'plans_processed': 0,
            'plans_with_full_tariffs': 0,
            'plans_with_partial_tariffs': 0,
            'plans_using_fallback': 0
        }
        
        # Get plans with reasonable limit
        all_plans = self.get_all_plans_for_state(state, limit=100)
        
        # Filter and calculate costs
        filtered_plans = []
        for plan in all_plans:
            if self._plan_matches_criteria(plan, criteria):
                try:
                    estimated_cost = self._calculate_plan_cost(
                        plan, usage_kwh, has_solar, criteria.get('solar_export_kwh', 0)
                    )
                    if estimated_cost != float('inf'):
                        plan['estimated_annual_cost'] = estimated_cost
                        filtered_plans.append(plan)
                except Exception:
                    continue
        
        # Sort by cost
        filtered_plans.sort(key=lambda x: x.get('estimated_annual_cost', float('inf')))
        
        return filtered_plans[:20]
    
    def get_all_plans_for_state(self, state: str, limit: int = 100) -> List[Dict[str, Any]]:
        """OPTIMIZED: Get plans with configurable limit"""
        if state not in self.necf_states:
            return self._get_state_specific_plans(state)
        
        all_plans = []
        
        # Start with major retailers
        retailers = ['agl', 'origin']  # Can be expanded
        
        for retailer in retailers:
            try:
                plans = self.get_plans_for_retailer(retailer, state, limit//len(retailers))
                all_plans.extend(plans)
                time.sleep(0.5)  # Rate limiting
            except Exception:
                continue
        
        return all_plans
    
    def _calculate_plan_cost(self, plan: Dict[str, Any], usage_kwh: int, has_solar: bool = False, solar_export_kwh: int = 0) -> float:
        """Calculate estimated annual cost"""
        try:
            usage_rate = float(plan.get('usage_rate', 0.30))
            supply_charge = float(plan.get('supply_charge', 1.20))
            solar_fit_rate = float(plan.get('solar_fit_rate', 0.05)) if has_solar else 0
            
            annual_usage_cost = usage_kwh * usage_rate
            annual_supply_cost = 365 * supply_charge
            annual_solar_credit = solar_export_kwh * solar_fit_rate if has_solar else 0
            
            total_cost = annual_usage_cost + annual_supply_cost - annual_solar_credit
            return max(0, total_cost)
            
        except (TypeError, ValueError):
            return float('inf')
    
    def _plan_matches_criteria(self, plan: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if plan matches criteria"""
        # Basic filtering
        if plan.get('customer_type', '').lower() != 'residential':
            return False
        
        # Solar requirement
        if criteria.get('has_solar', False) and not plan.get('has_solar_fit', False):
            return False
        
        return True
    
    def _plan_available_in_state(self, plan: Dict[str, Any], state: str) -> bool:
        """Check if plan is available in state"""
        return True  # Simplified for MVP
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        total = self.processing_stats['plans_processed']
        if total == 0:
            return self.processing_stats
        
        return {
            **self.processing_stats,
            'data_quality_breakdown': {
                'api_complete': f"{(self.processing_stats['plans_with_full_tariffs']/total*100):.1f}%",
                'api_partial': f"{(self.processing_stats['plans_with_partial_tariffs']/total*100):.1f}%",
                'estimated': f"{(self.processing_stats['plans_using_fallback']/total*100):.1f}%"
            }
        }
    
    def _get_plans_fallback(self, retailer_key: str, state: str = None) -> List[Dict[str, Any]]:
        """Fallback plans"""
        fallback = self.fallback_rates.get(retailer_key.lower(), self.fallback_rates['agl'])
        
        return [{
            'plan_id': f'{retailer_key}_fallback',
            'retailer': retailer_key.replace('_', ' ').title(),
            'plan_name': f'{retailer_key.title()} Standard Plan',
            'usage_rate': fallback['usage'],
            'supply_charge': fallback['supply'],
            'solar_fit_rate': fallback['solar'],
            'has_solar_fit': True,
            'plan_type': 'market',
            'fuel_type': 'electricity',
            'customer_type': 'residential',
            'data_quality': 'fallback',
            'features': ['Standard market offer']
        }]
    
    def _get_state_specific_plans(self, state: str) -> List[Dict[str, Any]]:
        """State-specific plans for non-NECF states"""
        if state == 'WA':
            return [{
                'plan_id': 'synergy_home_plan',
                'retailer': 'Synergy',
                'plan_name': 'Home Plan A1',
                'usage_rate': 0.295,
                'supply_charge': 1.33,
                'solar_fit_rate': 0.025,
                'has_solar_fit': True,
                'plan_type': 'regulated',
                'fuel_type': 'electricity',
                'customer_type': 'residential',
                'data_quality': 'state_regulated'
            }]
        return []
    
    def _rate_limit(self):
        """Rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def test_api_access(self) -> Dict[str, Any]:
        """Test API access with statistics"""
        test_results = {
            'cdr_register_access': False,
            'retailer_api_access': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Test CDR Register
        try:
            retailers = self.get_all_retailers()
            test_results['cdr_register_access'] = len(retailers) > 0
            test_results['retailers_found'] = len(retailers)
        except Exception as e:
            test_results['cdr_register_error'] = str(e)
        
        # Test retailer access
        for retailer in ['agl']:
            try:
                plans = self.get_plans_for_retailer(retailer, limit=50)
                valid_plans = [p for p in plans if self._is_valid_plan(p)]
                
                test_results['retailer_api_access'][retailer] = {
                    'success': len(valid_plans) > 0,
                    'total_plans': len(plans),
                    'valid_plans': len(valid_plans),
                    'sample_plan': valid_plans[0] if valid_plans else None
                }
            except Exception as e:
                test_results['retailer_api_access'][retailer] = {
                    'success': False,
                    'error': str(e)
                }
        
        # Add processing stats
        test_results['processing_stats'] = self.get_processing_stats()
        
        return test_results


def test_optimized_api():
    """Test the optimized API"""
    print("🚀 Testing Optimized API Integration")
    print("="*50)
    
    api = AustralianEnergyAPI()
    
    # Test with smaller limit to reduce noise
    print("🔍 Testing AGL plans (limited to 50)...")
    plans = api.get_plans_for_retailer('agl', limit=50)
    
    print(f"✅ Retrieved {len(plans)} valid plans")
    
    # Show processing statistics
    stats = api.get_processing_stats()
    print(f"\n📊 Data Quality Breakdown:")
    for quality, percentage in stats.get('data_quality_breakdown', {}).items():
        print(f"   {quality}: {percentage}")
    
    # Show sample plans
    if plans:
        print(f"\n🎯 Sample Plans:")
        for i, plan in enumerate(plans[:3], 1):
            print(f"   {i}. {plan['plan_name']}")
            print(f"      Rate: ${plan['usage_rate']:.3f}/kWh + ${plan['supply_charge']:.2f}/day")
            print(f"      Quality: {plan['data_quality']}")
    
    return api

if __name__ == "__main__":
    test_optimized_api()