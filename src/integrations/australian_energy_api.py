"""
Real Australian Energy Plans API Integration
Based on Consumer Data Standards Australia and AER APIs

File: src/integrations/australian_energy_api.py
"""
import requests
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import time
from dataclasses import dataclass

class AustralianEnergyAPI:
    """
    Integrates with official Australian energy APIs to get real plan data
    
    Public APIs Available:
    1. AER Energy Product Reference Data (CDR APIs) - PUBLIC ACCESS
    2. Energy Made Easy Reference Data - LIMITED ACCESS
    3. Consumer Data Right Register - PUBLIC ACCESS
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Official Australian Energy API Endpoints
        self.endpoints = {
            # AER Consumer Data Right APIs (Public Access)
            'aer_plans_base': 'https://cdr.energymadeeasy.gov.au',
            'cdr_register': 'https://api.cdr.gov.au/cdr-register/v1',
            
            # Retailer-specific CDR endpoints (discovered from research)
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
            'x-v': '1',  # API version (mandatory for CDR APIs)
            'Accept': 'application/json',
            'User-Agent': 'WattsMyBill/1.0 (Australian Energy Analysis Tool)'
        }
        
        # States covered by National Energy Customer Framework
        self.necf_states = ['NSW', 'QLD', 'SA', 'TAS', 'ACT', 'VIC']
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
    def get_all_retailers(self) -> List[Dict[str, Any]]:
        """
        Get list of all energy retailers from CDR Register
        This is publicly available data
        """
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
                
                self.logger.info(f"Found {len(energy_retailers)} energy retailers")
                return energy_retailers
                
            else:
                self.logger.error(f"Failed to get retailers: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error getting retailers: {e}")
            return []
    
    def get_plans_for_retailer(self, retailer_key: str, state: str = None) -> List[Dict[str, Any]]:
        """
        Get energy plans for a specific retailer using CDR APIs
        
        Args:
            retailer_key: Retailer identifier (e.g., 'agl', 'origin')
            state: Optional state filter
            
        Returns:
            List of energy plans with pricing and features
        """
        try:
            if retailer_key not in self.endpoints['retailer_endpoints']:
                self.logger.warning(f"Retailer {retailer_key} not supported")
                return []
            
            url = self.endpoints['retailer_endpoints'][retailer_key]
            
            # CDR API parameters
            params = {
                'type': 'ALL',  # STANDING, MARKET, ALL
                'fuelType': 'ELECTRICITY',  # ELECTRICITY, GAS, DUAL_FUEL, ALL
                'effective': 'CURRENT',  # CURRENT, FUTURE, ALL
                'page': 1,
                'page-size': 1000  # Maximum allowed
            }
            
            if state:
                # Note: State filtering may need to be done post-request
                # as not all CDR APIs support state parameter
                pass
            
            self._rate_limit()
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                plans = data.get('data', {}).get('plans', [])
                
                # Process and normalize plan data
                processed_plans = []
                for plan in plans:
                    processed_plan = self._process_plan_data(plan, retailer_key)
                    if processed_plan:
                        processed_plans.append(processed_plan)
                
                self.logger.info(f"Retrieved {len(processed_plans)} plans for {retailer_key}")
                return processed_plans
                
            else:
                self.logger.error(f"Failed to get plans for {retailer_key}: {response.status_code}")
                # Try fallback method
                return self._get_plans_fallback(retailer_key, state)
                
        except Exception as e:
            self.logger.error(f"Error getting plans for {retailer_key}: {e}")
            return self._get_plans_fallback(retailer_key, state)
    
    def get_plan_details(self, retailer_key: str, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific energy plan
        
        Args:
            retailer_key: Retailer identifier
            plan_id: Specific plan ID
            
        Returns:
            Detailed plan information including tariff structure
        """
        try:
            base_url = self.endpoints['retailer_endpoints'].get(retailer_key)
            if not base_url:
                return None
            
            # CDR Plan Detail endpoint
            url = f"{base_url}/{plan_id}"
            
            self._rate_limit()
            response = requests.get(url, headers=self.headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                plan_detail = data.get('data', {})
                
                return self._process_plan_detail(plan_detail, retailer_key)
                
            else:
                self.logger.error(f"Failed to get plan details: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting plan details: {e}")
            return None
    
    def get_all_plans_for_state(self, state: str) -> List[Dict[str, Any]]:
        """
        Get all available energy plans for a specific state
        
        Args:
            state: Australian state code (NSW, QLD, VIC, etc.)
            
        Returns:
            List of all available plans across all retailers
        """
        if state not in self.necf_states:
            self.logger.warning(f"State {state} not covered by National Energy Customer Framework")
            return self._get_state_specific_plans(state)
        
        all_plans = []
        
        # Get plans from all major retailers
        retailers = ['agl', 'origin', 'energyaustralia', 'alinta', 'red_energy', 'simply_energy']
        
        for retailer in retailers:
            try:
                plans = self.get_plans_for_retailer(retailer, state)
                
                # Filter plans available in the specified state
                state_plans = [plan for plan in plans if self._plan_available_in_state(plan, state)]
                all_plans.extend(state_plans)
                
                # Be respectful with API calls
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"Error getting plans for {retailer} in {state}: {e}")
                continue
        
        self.logger.info(f"Retrieved {len(all_plans)} total plans for {state}")
        return all_plans
    
    def search_plans(self, criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for energy plans based on specific criteria
        
        Args:
            criteria: Search criteria including:
                - state: Australian state
                - fuel_type: 'electricity', 'gas', 'dual'
                - has_solar: Boolean for solar feed-in tariff
                - usage_kwh: Annual usage for cost calculation
                - plan_type: 'market', 'standing'
                
        Returns:
            Filtered and ranked list of suitable plans
        """
        state = criteria.get('state', 'NSW')
        fuel_type = criteria.get('fuel_type', 'electricity')
        has_solar = criteria.get('has_solar', False)
        usage_kwh = criteria.get('usage_kwh', 4000)
        
        # Get all plans for the state
        all_plans = self.get_all_plans_for_state(state)
        
        # Filter based on criteria
        filtered_plans = []
        for plan in all_plans:
            if self._plan_matches_criteria(plan, criteria):
                # Calculate estimated annual cost
                plan['estimated_annual_cost'] = self._calculate_plan_cost(plan, usage_kwh, has_solar)
                filtered_plans.append(plan)
        
        # Sort by estimated cost (cheapest first)
        filtered_plans.sort(key=lambda x: x.get('estimated_annual_cost', float('inf')))
        
        return filtered_plans[:20]  # Return top 20 plans
    
    def _process_plan_data(self, plan_data: Dict[str, Any], retailer_key: str) -> Optional[Dict[str, Any]]:
        """Process raw CDR plan data into normalized format"""
        try:
            # Extract key information from CDR plan structure
            plan_id = plan_data.get('planId')
            
            # Basic plan information
            processed = {
                'plan_id': plan_id,
                'retailer': retailer_key.replace('_', ' ').title(),
                'plan_name': plan_data.get('displayName', plan_data.get('planId')),
                'description': plan_data.get('description', ''),
                'plan_type': plan_data.get('type', 'MARKET').lower(),
                'fuel_type': plan_data.get('fuelType', 'ELECTRICITY').lower(),
                'effective_from': plan_data.get('effectiveFrom'),
                'effective_to': plan_data.get('effectiveTo'),
                'last_updated': plan_data.get('lastUpdated'),
                'customer_type': plan_data.get('customerType', 'RESIDENTIAL').lower(),
                'brand': plan_data.get('brand'),
                'application_uri': plan_data.get('applicationUri'),
                
                # Tariff information (simplified for MVP)
                'has_time_of_use': False,
                'has_demand_charges': False,
                'has_solar_fit': False,
                'usage_rate': None,
                'supply_charge': None,
                'solar_fit_rate': None,
                
                # Features and eligibility
                'features': [],
                'eligibility': plan_data.get('eligibility', []),
                'fees': plan_data.get('fees', []),
                'discounts': plan_data.get('discounts', []),
                
                # Geographic availability
                'distribution_zones': plan_data.get('geography', {}).get('distributors', []),
                'excluded_postcodes': plan_data.get('geography', {}).get('excludedPostcodes', []),
                
                # Raw data for advanced processing
                'raw_data': plan_data
            }
            
            # Extract tariff details
            self._extract_tariff_details(processed, plan_data)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Error processing plan data: {e}")
            return None
    
    def _extract_tariff_details(self, processed_plan: Dict[str, Any], raw_data: Dict[str, Any]):
        """Extract tariff structure from CDR plan data"""
        try:
            # Look for electricity tariffs
            electricity_contract = raw_data.get('electricityContract', {})
            tariffs = electricity_contract.get('tariffs', [])
            
            for tariff in tariffs:
                tariff_type = tariff.get('type', '')
                
                # Extract usage rates
                rates = tariff.get('rates', [])
                for rate in rates:
                    rate_type = rate.get('rateBlockUType', '')
                    
                    if rate_type == 'singleRate':
                        single_rate = rate.get('singleRate', {})
                        if single_rate.get('unitPrice'):
                            processed_plan['usage_rate'] = float(single_rate['unitPrice'])
                    
                    elif rate_type == 'timeOfUseRates':
                        processed_plan['has_time_of_use'] = True
                        # Process time-of-use rates
                        tou_rates = rate.get('timeOfUseRates', [])
                        # Store TOU structure for advanced processing
                        processed_plan['tou_rates'] = tou_rates
                
                # Extract daily supply charge
                daily_supply = tariff.get('dailySupplyCharges')
                if daily_supply:
                    processed_plan['supply_charge'] = float(daily_supply)
                
                # Check for demand charges
                if tariff.get('demandCharges'):
                    processed_plan['has_demand_charges'] = True
            
            # Extract solar feed-in tariff
            feed_in_tariffs = electricity_contract.get('solarFeedInTariff', [])
            if feed_in_tariffs:
                processed_plan['has_solar_fit'] = True
                # Use the first available feed-in rate
                first_fit = feed_in_tariffs[0]
                if first_fit.get('singleTariff', {}).get('amount'):
                    processed_plan['solar_fit_rate'] = float(first_fit['singleTariff']['amount'])
            
        except Exception as e:
            self.logger.error(f"Error extracting tariff details: {e}")
    
    def _calculate_plan_cost(self, plan: Dict[str, Any], usage_kwh: int, has_solar: bool = False, solar_export_kwh: int = 0) -> float:
        """Calculate estimated annual cost for a plan"""
        try:
            usage_rate = plan.get('usage_rate', 0.30)  # Default rate if not available
            supply_charge = plan.get('supply_charge', 1.20)  # Default daily supply charge
            solar_fit_rate = plan.get('solar_fit_rate', 0.05) if has_solar else 0
            
            # Basic cost calculation
            annual_usage_cost = usage_kwh * usage_rate
            annual_supply_cost = 365 * supply_charge
            annual_solar_credit = solar_export_kwh * solar_fit_rate if has_solar else 0
            
            total_cost = annual_usage_cost + annual_supply_cost - annual_solar_credit
            
            return max(0, total_cost)  # Ensure non-negative
            
        except Exception as e:
            self.logger.error(f"Error calculating plan cost: {e}")
            return float('inf')
    
    def _plan_available_in_state(self, plan: Dict[str, Any], state: str) -> bool:
        """Check if a plan is available in the specified state"""
        # This is a simplified check - in practice, you'd need to check
        # distribution zones and excluded postcodes
        distribution_zones = plan.get('distribution_zones', [])
        
        # State-to-distributor mapping (simplified)
        state_distributors = {
            'NSW': ['Ausgrid', 'Endeavour Energy', 'Essential Energy'],
            'QLD': ['Energex', 'Ergon Energy'],
            'VIC': ['CitiPower', 'Powercor', 'Jemena', 'AusNet Services', 'United Energy'],
            'SA': ['SA Power Networks'],
            'TAS': ['TasNetworks'],
            'ACT': ['Evoenergy']
        }
        
        state_distributors_list = state_distributors.get(state, [])
        
        # Check if any plan distributors match state distributors
        if not distribution_zones:
            return True  # Assume available if no restriction specified
        
        return any(dist in state_distributors_list for dist in distribution_zones)
    
    def _plan_matches_criteria(self, plan: Dict[str, Any], criteria: Dict[str, Any]) -> bool:
        """Check if a plan matches search criteria"""
        # Fuel type check
        fuel_type = criteria.get('fuel_type', 'electricity')
        if plan.get('fuel_type') != fuel_type:
            return False
        
        # Solar requirement
        has_solar = criteria.get('has_solar', False)
        if has_solar and not plan.get('has_solar_fit', False):
            return False
        
        # Customer type
        customer_type = criteria.get('customer_type', 'residential')
        if plan.get('customer_type') != customer_type:
            return False
        
        return True
    
    def _get_plans_fallback(self, retailer_key: str, state: str = None) -> List[Dict[str, Any]]:
        """Fallback method when CDR API is unavailable"""
        self.logger.info(f"Using fallback data for {retailer_key}")
        
        # Return hard-coded plan data as fallback
        # This would come from your existing market_researcher.py data
        fallback_plans = {
            'agl': [
                {
                    'plan_id': 'agl_value_saver',
                    'retailer': 'AGL',
                    'plan_name': 'Value Saver',
                    'usage_rate': 0.275,
                    'supply_charge': 1.20,
                    'solar_fit_rate': 0.06,
                    'has_solar_fit': True,
                    'plan_type': 'market',
                    'fuel_type': 'electricity'
                }
            ],
            'origin': [
                {
                    'plan_id': 'origin_basic',
                    'retailer': 'Origin',
                    'plan_name': 'Basic Plan',
                    'usage_rate': 0.285,
                    'supply_charge': 1.15,
                    'solar_fit_rate': 0.05,
                    'has_solar_fit': True,
                    'plan_type': 'market',
                    'fuel_type': 'electricity'
                }
            ]
        }
        
        return fallback_plans.get(retailer_key, [])
    
    def _get_state_specific_plans(self, state: str) -> List[Dict[str, Any]]:
        """Get plans for states not covered by NECF (WA, NT)"""
        if state == 'WA':
            # Western Australia - Synergy and Horizon Power
            return [
                {
                    'plan_id': 'synergy_home_plan',
                    'retailer': 'Synergy',
                    'plan_name': 'Home Plan A1',
                    'usage_rate': 0.295,
                    'supply_charge': 1.33,
                    'solar_fit_rate': 0.025,
                    'has_solar_fit': True,
                    'plan_type': 'regulated',
                    'fuel_type': 'electricity'
                }
            ]
        elif state == 'NT':
            # Northern Territory - Territory Generation
            return [
                {
                    'plan_id': 'territory_gen_standard',
                    'retailer': 'Territory Generation',
                    'plan_name': 'Standard Tariff',
                    'usage_rate': 0.325,
                    'supply_charge': 1.45,
                    'solar_fit_rate': 0.08,
                    'has_solar_fit': True,
                    'plan_type': 'regulated',
                    'fuel_type': 'electricity'
                }
            ]
        
        return []
    
    def _rate_limit(self):
        """Implement rate limiting for API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def test_api_access(self) -> Dict[str, Any]:
        """Test API access and return status"""
        test_results = {
            'cdr_register_access': False,
            'retailer_api_access': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Test CDR Register access
        try:
            retailers = self.get_all_retailers()
            test_results['cdr_register_access'] = len(retailers) > 0
            test_results['retailers_found'] = len(retailers)
        except Exception as e:
            test_results['cdr_register_error'] = str(e)
        
        # Test retailer API access
        test_retailers = ['agl', 'origin']
        for retailer in test_retailers:
            try:
                plans = self.get_plans_for_retailer(retailer)
                test_results['retailer_api_access'][retailer] = {
                    'success': len(plans) > 0,
                    'plans_found': len(plans)
                }
            except Exception as e:
                test_results['retailer_api_access'][retailer] = {
                    'success': False,
                    'error': str(e)
                }
        
        return test_results


# Integration with your existing market researcher
def integrate_with_market_researcher():
    """
    Integration function to update your MarketResearcherAgent
    with real API data
    """
    api = AustralianEnergyAPI()
    
    # Test API access
    test_results = api.test_api_access()
    print("API Test Results:")
    print(json.dumps(test_results, indent=2))
    
    # Example: Get all plans for NSW
    nsw_plans = api.get_all_plans_for_state('NSW')
    print(f"\nFound {len(nsw_plans)} plans in NSW")
    
    # Example: Search for plans with specific criteria
    search_criteria = {
        'state': 'NSW',
        'fuel_type': 'electricity',
        'has_solar': True,
        'usage_kwh': 4000,
        'customer_type': 'residential'
    }
    
    matching_plans = api.search_plans(search_criteria)
    print(f"Found {len(matching_plans)} plans matching criteria")
    
    return api, nsw_plans, matching_plans


if __name__ == "__main__":
    # Test the API integration
    api, plans, matches = integrate_with_market_researcher()
    
    if plans:
        print("\nExample plan:")
        print(json.dumps(plans[0], indent=2))