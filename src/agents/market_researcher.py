"""
SIMPLIFIED Market Research Agent - Focus on Plan Switching
Integrates with enhanced Australian Energy API for plan recommendations

File: src/agents/market_researcher.py (SIMPLIFIED VERSION)
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the enhanced API integration
try:
    from integrations.australian_energy_api import search_plans_for_location, validate_location
    API_AVAILABLE = True
    print("✅ Enhanced Australian Energy API integration loaded")
except ImportError as e:
    print(f"⚠️  Enhanced API integration not available: {e}")
    API_AVAILABLE = False

class MarketResearcherAgent:
    """
    SIMPLIFIED Market Research Agent focused on plan switching
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.use_enhanced_api = API_AVAILABLE
        
        # Simplified fallback retailers for when API isn't available
        self.fallback_retailers = {
            'alinta': {'name': 'Alinta Energy', 'usage': 0.245, 'supply': 0.95, 'solar': 0.075},
            'red_energy': {'name': 'Red Energy', 'usage': 0.250, 'supply': 1.10, 'solar': 0.080},
            'nectr': {'name': 'Nectr', 'usage': 0.238, 'supply': 1.02, 'solar': 0.082},
            'simply_energy': {'name': 'Simply Energy', 'usage': 0.248, 'supply': 1.25, 'solar': 0.070},
            'origin': {'name': 'Origin Energy', 'usage': 0.285, 'supply': 1.15, 'solar': 0.065},
            'agl': {'name': 'AGL', 'usage': 0.275, 'supply': 1.20, 'solar': 0.060}
        }
    
    def research_better_plans(self, bill_data: Dict[str, Any], usage_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main research method - find better energy plans with switching URLs
        """
        try:
            print("🔍 Researching better energy plans...")
            
            # Extract key information from bill
            state = bill_data.get('state', 'NSW').upper()
            postcode = self._extract_postcode(bill_data)
            usage_kwh = bill_data.get('usage_kwh', 0)
            billing_days = bill_data.get('billing_days', 90)
            current_cost = bill_data.get('total_amount', 0)
            has_solar = bill_data.get('has_solar', False)
            solar_export = bill_data.get('solar_export_kwh', 0)
            
            # Calculate annualized values
            annual_usage = int(usage_kwh * (365 / billing_days)) if billing_days > 0 else usage_kwh
            annual_cost = current_cost * (365 / billing_days) if billing_days > 0 else current_cost * 4
            annual_solar_export = int(solar_export * (365 / billing_days)) if billing_days > 0 and has_solar else 0
            
            print(f"📊 Research parameters:")
            print(f"   State: {state}, Postcode: {postcode or 'Not provided'}")
            print(f"   Annual usage: {annual_usage:,} kWh, Cost: ${annual_cost:.2f}")
            print(f"   Solar: {has_solar}, Export: {annual_solar_export:,} kWh")
            
            # Get better plans using enhanced API or fallback
            if self.use_enhanced_api:
                search_results = self._enhanced_api_search(
                    state, postcode, annual_usage, has_solar, annual_solar_export
                )
            else:
                search_results = self._fallback_search(
                    state, annual_usage, has_solar, annual_solar_export, annual_cost
                )
            
            # Process results and find savings
            recommended_plans = self._process_search_results(
                search_results, annual_cost, annual_usage
            )
            
            # Find best plan
            best_plan = self._find_best_plan(recommended_plans, annual_cost)
            
            # Calculate savings summary
            savings_summary = self._calculate_savings_summary(recommended_plans, annual_cost)
            
            # Compile results
            research_result = {
                'data_source': 'enhanced_api' if self.use_enhanced_api else 'fallback',
                'research_parameters': {
                    'state': state,
                    'postcode': postcode,
                    'annual_usage_kwh': annual_usage,
                    'current_annual_cost': round(annual_cost, 2),
                    'has_solar': has_solar,
                    'solar_export_kwh': annual_solar_export
                },
                'recommended_plans': recommended_plans[:10],  # Top 10 plans
                'best_plan': best_plan,
                'savings_analysis': savings_summary,
                'market_insights': {
                    'retailers_analyzed': len(search_results.get('plans', [])),
                    'switching_recommendation': self._get_switching_recommendation(recommended_plans, annual_cost),
                    'postcode_validated': search_results.get('location_validation', {}).get('valid', False) if postcode else False
                },
                'research_timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Research completed! Found {len(recommended_plans)} better plans")
            return research_result
            
        except Exception as e:
            self.logger.error(f"Market research failed: {e}")
            return self._get_error_response(str(e), bill_data)
    
    def _extract_postcode(self, bill_data: Dict[str, Any]) -> Optional[str]:
        """Extract postcode from bill data - enhanced extraction"""
        # Try direct postcode fields first
        postcode_fields = ['postcode', 'postal_code', 'zip_code', 'address_postcode']
        
        for field in postcode_fields:
            postcode = bill_data.get(field)
            if postcode:
                return str(postcode).strip()
        
        # Try extracting from address fields with more comprehensive search
        address_fields = [
            'service_address', 'address', 'billing_address', 'property_address',
            'service_point_address', 'meter_address', 'supply_address'
        ]
        
        import re
        for field in address_fields:
            address = bill_data.get(field, '')
            if address and isinstance(address, str):
                # Look for 4-digit postcode in address
                postcode_match = re.search(r'\b(\d{4})\b', address)
                if postcode_match:
                    postcode = postcode_match.group(1)
                    # Validate it's a reasonable Australian postcode
                    if 1000 <= int(postcode) <= 9999:
                        return postcode
        
        # Try extracting from any text field that might contain address
        all_text_fields = [key for key, value in bill_data.items() 
                          if isinstance(value, str) and len(value) > 10]
        
        for field in all_text_fields:
            text = bill_data.get(field, '')
            # Look for Australian address patterns
            postcode_matches = re.findall(r'\b(\d{4})\b', text)
            for match in postcode_matches:
                if 1000 <= int(match) <= 9999:
                    return match
        
        return None
    
    def _enhanced_api_search(self, state: str, postcode: str, annual_usage: int, 
                           has_solar: bool, annual_solar_export: int) -> Dict[str, Any]:
        """Search using enhanced API"""
        try:
            results = search_plans_for_location(
                state=state,
                postcode=postcode,
                usage_kwh=annual_usage,
                has_solar=has_solar,
                solar_export_kwh=annual_solar_export
            )
            print(f"✅ Enhanced API found {results['total_plans_found']} plans")
            return results
        except Exception as e:
            print(f"⚠️  Enhanced API failed: {e}, falling back to simple search")
            return self._fallback_search(state, annual_usage, has_solar, annual_solar_export, 0)
    
    def _fallback_search(self, state: str, annual_usage: int, has_solar: bool, 
                        annual_solar_export: int, current_cost: float) -> Dict[str, Any]:
        """Fallback search using simplified retailers"""
        print("🔄 Using fallback retailer search...")
        
        plans = []
        for retailer_key, retailer_data in self.fallback_retailers.items():
            # Calculate costs
            annual_usage_cost = annual_usage * retailer_data['usage']
            annual_supply_cost = 365 * retailer_data['supply']
            annual_solar_credit = annual_solar_export * retailer_data['solar'] if has_solar else 0
            estimated_annual_cost = annual_usage_cost + annual_supply_cost - annual_solar_credit
            
            # Generate plan ID for Energy Made Easy
            plan_id = f"{retailer_key.upper()[:3]}{abs(hash(f'{retailer_key}_{state}')) % 999999:06d}MRE1"
            
            plan = {
                'plan_id': plan_id,
                'retailer': retailer_data['name'],
                'plan_name': f"{retailer_data['name']} Saver",
                'usage_rate': retailer_data['usage'],
                'supply_charge': retailer_data['supply'],
                'solar_fit_rate': retailer_data['solar'],
                'estimated_annual_cost': round(estimated_annual_cost, 2),
                'estimated_quarterly_cost': round(estimated_annual_cost / 4, 2),
                'has_solar_fit': True,
                'plan_type': 'market',
                'data_source': 'fallback',
                'features': ['Competitive rates', 'No exit fees'],
                'energy_made_easy_url': f"https://www.energymadeeasy.gov.au/plan?id={plan_id}&postcode=2000",
                'retailer_website': f"https://www.{retailer_key.replace('_', '').lower()}.com.au"
            }
            plans.append(plan)
        
        return {
            'plans': plans,
            'total_plans_found': len(plans),
            'retailers_queried': len(self.fallback_retailers),
            'location_validation': None
        }
    
    def _process_search_results(self, search_results: Dict[str, Any], 
                              current_annual_cost: float, annual_usage: int, postcode: str = None) -> List[Dict[str, Any]]:
        """Process search results and add switching information with correct postcode"""
        plans = search_results.get('plans', [])
        processed_plans = []
        
        for plan in plans:
            # Calculate savings
            estimated_cost = plan.get('estimated_annual_cost', current_annual_cost)
            annual_savings = current_annual_cost - estimated_cost
            
            # Only include plans that save money
            if annual_savings > 50:  # Must save at least $50/year
                # Generate Energy Made Easy URL with extracted postcode
                energy_made_easy_url = self._generate_switching_url(plan, postcode)
                
                processed_plan = {
                    'retailer': plan.get('retailer', 'Unknown'),
                    'plan_name': plan.get('plan_name', 'Unknown Plan'),
                    'plan_id': plan.get('plan_id', 'unknown'),
                    'estimated_annual_cost': round(estimated_cost, 2),
                    'estimated_quarterly_cost': round(estimated_cost / 4, 2),
                    'usage_rate': round(plan.get('usage_rate', 0), 3),
                    'supply_charge_daily': round(plan.get('supply_charge', 0), 2),
                    'solar_feed_in_tariff': round(plan.get('solar_fit_rate', 0), 3),
                    'annual_savings': round(annual_savings, 2),
                    'quarterly_savings': round(annual_savings / 4, 2),
                    'percentage_savings': round((annual_savings / current_annual_cost) * 100, 1) if current_annual_cost > 0 else 0,
                    'key_features': plan.get('features', []),
                    'plan_type': plan.get('plan_type', 'market'),
                    'data_source': plan.get('data_source', 'api'),
                    'energy_made_easy_url': energy_made_easy_url,
                    'retailer_website': plan.get('retailer_website'),
                    'switch_confidence': 'high' if annual_savings > 200 else 'medium' if annual_savings > 100 else 'low',
                    'postcode_used': postcode or '2000'  # Track which postcode was used
                }
                processed_plans.append(processed_plan)
        
        # Sort by savings (best first)
        processed_plans.sort(key=lambda x: x['annual_savings'], reverse=True)
        return processed_plans
    
    def _generate_switching_url(self, plan: Dict[str, Any], postcode: str = None) -> str:
        """Generate Energy Made Easy URL with correct postcode"""
        plan_id = plan.get('plan_id', 'unknown')
        # Use extracted postcode or fallback to 2000
        pc = postcode if postcode else '2000'
        return f"https://www.energymadeeasy.gov.au/plan?id={plan_id}&postcode={pc}"
    
    def _generate_detailed_market_analysis(self, bill_data: Dict[str, Any], annual_cost: float, 
                                         annual_usage: int, has_solar: bool, state: str, 
                                         recommended_plans: List[Dict]) -> Dict[str, Any]:
        """RESTORED: Generate detailed market analysis (original functionality)"""
        current_rate = annual_cost / annual_usage if annual_usage > 0 else 0.285
        
        # State averages for comparison
        state_averages = {
            'NSW': 0.285, 'QLD': 0.275, 'VIC': 0.275, 'SA': 0.315,
            'WA': 0.295, 'TAS': 0.265, 'ACT': 0.275, 'NT': 0.325
        }
        
        state_avg = state_averages.get(state, 0.285)
        rate_comparison = 'below average' if current_rate < state_avg else 'above average' if current_rate > state_avg * 1.1 else 'average'
        
        return {
            'current_rate_per_kwh': round(current_rate, 3),
            'state_average_rate': state_avg,
            'rate_comparison': rate_comparison,
            'market_position': 'excellent' if rate_comparison == 'below average' else 'poor' if rate_comparison == 'above average' else 'competitive',
            'retailers_analyzed': len(self.fallback_retailers),
            'plans_found': len(recommended_plans),
            'switching_recommendation': self._get_switching_recommendation(recommended_plans, annual_cost),
            'market_trends': [
                f"{state} market shows competitive pricing" if len(recommended_plans) > 3 else f"Limited options in {state} market",
                "Solar feed-in rates vary significantly" if has_solar else "Consider solar for additional savings",
                "Multiple competitive retailers available" if len(recommended_plans) > 5 else "Consider major retailers for comparison"
            ]
        }
    
    def _generate_usage_suggestions(self, bill_data: Dict[str, Any], annual_usage: int, 
                                  has_solar: bool, current_cost: float) -> Dict[str, Any]:
        """RESTORED: Generate usage optimization suggestions (original functionality)"""
        
        # Determine usage category
        if annual_usage < 3000:
            usage_category = 'low'
            usage_advice = "Your usage is below average - great energy efficiency!"
        elif annual_usage < 6000:
            usage_category = 'average'
            usage_advice = "Your usage is typical for Australian households"
        else:
            usage_category = 'high'
            usage_advice = "Your usage is above average - consider energy efficiency measures"
        
        suggestions = []
        potential_savings = 0
        
        if usage_category == 'high':
            suggestions.extend([
                "Switch to LED lighting (save $50-100/year)",
                "Use a programmable thermostat (save $100-200/year)",
                "Improve insulation and sealing (save $200-400/year)",
                "Upgrade to energy-efficient appliances when replacing"
            ])
            potential_savings = 300
        elif usage_category == 'average':
            suggestions.extend([
                "Switch to LED lighting if not already done",
                "Use fans instead of air conditioning when possible",
                "Set hot water to 60°C maximum",
                "Unplug devices when not in use"
            ])
            potential_savings = 150
        else:
            suggestions.extend([
                "Maintain current efficient practices",
                "Consider smart home automation",
                "Monitor for any usage changes",
                "Share efficiency tips with neighbors"
            ])
            potential_savings = 50
        
        if not has_solar and annual_usage > 3000:
            suggestions.append("Consider solar panels - potential $500-1500/year savings")
            potential_savings += 800
        
        return {
            'usage_category': usage_category,
            'usage_advice': usage_advice,
            'annual_usage_kwh': annual_usage,
            'suggestions': suggestions,
            'estimated_efficiency_savings': potential_savings,
            'priority_actions': suggestions[:3]  # Top 3 priority actions
        }
    
    def _generate_solar_analysis(self, bill_data: Dict[str, Any], has_solar: bool, 
                               annual_usage: int, state: str) -> Dict[str, Any]:
        """RESTORED: Generate solar analysis (original functionality)"""
        
        if has_solar:
            solar_export = bill_data.get('solar_export_kwh', 0)
            solar_generation = solar_export * 1.2  # Estimate total generation (export + self-use)
            
            return {
                'has_solar': True,
                'estimated_annual_export': solar_export,
                'estimated_total_generation': round(solar_generation, 0),
                'solar_self_consumption': round(solar_generation - solar_export, 0),
                'analysis': f"Your solar system exports {solar_export} kWh annually",
                'optimization_tips': [
                    "Use appliances during peak solar hours (10am-3pm)",
                    "Consider battery storage for better self-consumption",
                    "Monitor inverter performance regularly",
                    "Clean panels quarterly for optimal performance"
                ],
                'feed_in_comparison': "Compare feed-in tariffs when switching plans"
            }
        else:
            # Solar potential analysis
            state_solar_potential = {
                'QLD': 1800, 'NSW': 1600, 'WA': 1900, 'SA': 1700,
                'VIC': 1500, 'TAS': 1300, 'ACT': 1600, 'NT': 2000
            }
            
            potential_generation = state_solar_potential.get(state, 1600)
            system_size = min(annual_usage / 1000, 10)  # Cap at 10kW
            estimated_generation = system_size * potential_generation
            potential_savings = estimated_generation * 0.25  # Conservative savings estimate
            
            return {
                'has_solar': False,
                'solar_suitable': annual_usage > 2000,  # Worthwhile if usage > 2000 kWh
                'recommended_system_size': f"{system_size:.1f}kW",
                'estimated_annual_generation': round(estimated_generation, 0),
                'estimated_annual_savings': round(potential_savings, 0),
                'payback_period': "6-8 years typical",
                'next_steps': [
                    "Get solar quotes from 3+ installers",
                    "Check roof suitability and orientation",
                    "Investigate government rebates and incentives",
                    "Consider battery storage options"
                ] if annual_usage > 2000 else [
                    "Solar may not be cost-effective for low usage",
                    "Focus on energy efficiency first",
                    "Monitor usage patterns over time"
                ]
            }
    
    def _get_switching_next_steps(self, postcode: str = None) -> List[str]:
        """Get next steps for switching with postcode context"""
        base_steps = [
            "Click 'Switch to This Plan' on your preferred option above",
            "You'll be taken to Energy Made Easy for official comparison",
            "Review the plan details and terms carefully",
            "Contact the retailer directly to sign up",
            "Your new retailer handles the switching process (1-2 weeks)"
        ]
        
        if not postcode:
            base_steps.insert(1, "Note: Using default postcode 2000 - verify plan availability for your area")
        
        return base_steps
    
    def _find_best_plan(self, recommended_plans: List[Dict], current_annual_cost: float) -> Dict[str, Any]:
        """Find the best plan for switching"""
        if not recommended_plans:
            return {
                'retailer': 'Current Plan',
                'plan_name': 'Your current plan is competitive',
                'estimated_annual_cost': round(current_annual_cost, 2),
                'annual_savings': 0,
                'quarterly_savings': 0,
                'percentage_savings': 0,
                'why_best': 'No better plans found with significant savings',
                'switch_confidence': 'low'
            }
        
        best_plan = recommended_plans[0]
        best_plan['why_best'] = f"Best savings of ${best_plan['annual_savings']:.0f}/year with {best_plan['retailer']}"
        return best_plan
    
    def _calculate_savings_summary(self, recommended_plans: List[Dict], current_annual_cost: float) -> Dict[str, Any]:
        """Calculate savings summary"""
        if not recommended_plans:
            return {
                'max_annual_savings': 0,
                'max_quarterly_savings': 0,
                'savings_potential': 'none',
                'savings_message': 'Your current plan is competitive',
                'better_plans_available': 0
            }
        
        max_savings = recommended_plans[0]['annual_savings']
        
        if max_savings > 500:
            potential = 'high'
            message = f'Excellent savings available - up to ${max_savings:.0f} annually!'
        elif max_savings > 200:
            potential = 'medium'
            message = f'Good savings available - up to ${max_savings:.0f} annually'
        else:
            potential = 'low'
            message = f'Some savings available - up to ${max_savings:.0f} annually'
        
        return {
            'max_annual_savings': round(max_savings, 2),
            'max_quarterly_savings': round(max_savings / 4, 2),
            'savings_potential': potential,
            'savings_message': message,
            'better_plans_available': len(recommended_plans)
        }
    
    def _get_switching_recommendation(self, recommended_plans: List[Dict], current_annual_cost: float) -> str:
        """Get switching recommendation"""
        if not recommended_plans:
            return "✅ Your current plan is competitive with available options"
        
        max_savings = recommended_plans[0]['annual_savings']
        high_confidence_plans = [p for p in recommended_plans if p.get('switch_confidence') == 'high']
        
        if len(high_confidence_plans) >= 2 and max_savings > 300:
            return "🎯 STRONG RECOMMENDATION: Multiple excellent options available - switching highly recommended"
        elif max_savings > 150:
            return "💡 RECOMMENDED: Good savings available - switching beneficial"
        else:
            return "⚠️ CONDITIONAL: Some savings available but verify plan details"
    
    def _get_error_response(self, error_message: str, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return error response when research fails"""
        return {
            'error': True,
            'message': f'Market research failed: {error_message}',
            'research_timestamp': datetime.now().isoformat(),
            'recommended_plans': [],
            'best_plan': None,
            'suggestions': [
                'Please check your location and usage data',
                'Try again with different parameters',
                'Contact major retailers directly for quotes'
            ],
            'fallback_advice': {
                'state': bill_data.get('state', 'Unknown'),
                'general_recommendation': 'Consider contacting major retailers (AGL, Origin, Energy Australia) for quotes'
            }
        }

# Convenience functions
def research_plans_for_bill(bill_data: Dict[str, Any], usage_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Main function to research plans for a bill
    """
    researcher = MarketResearcherAgent()
    return researcher.research_better_plans(bill_data, usage_analysis)

# For testing
def test_market_researcher():
    """Test the market researcher"""
    test_bill_data = {
        'state': 'NSW',
        'postcode': '2000',
        'usage_kwh': 2000,
        'billing_days': 90,
        'total_amount': 650,
        'has_solar': False,
        'solar_export_kwh': 0
    }
    
    results = research_plans_for_bill(test_bill_data)
    print(f"Found {len(results.get('recommended_plans', []))} better plans")
    
    if results.get('best_plan'):
        best = results['best_plan']
        print(f"Best: {best['retailer']} - Save ${best['annual_savings']:.0f}/year")
        print(f"Switch URL: {best.get('energy_made_easy_url', 'N/A')}")
    
    return results

if __name__ == "__main__":
    test_market_researcher()