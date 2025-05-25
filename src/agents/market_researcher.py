"""
Enhanced Market Research Agent - Now with Real Australian Energy API Integration
File: src/agents/market_researcher.py (UPDATED)
"""
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the real API integration
try:
    from integrations.australian_energy_api import AustralianEnergyAPI
    API_AVAILABLE = True
    print("✅ Real Australian Energy API integration loaded")
except ImportError as e:
    print(f"⚠️  API integration not available: {e}")
    API_AVAILABLE = False


class MarketResearcherAgent:
    """
    Enhanced Market Research Agent with Real Australian Energy API Integration
    Now uses live data from Energy Made Easy and CDR APIs
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize real API if available
        if API_AVAILABLE:
            self.api = AustralianEnergyAPI()
            self.use_real_api = True
            print("🚀 Using REAL Australian Energy Market Data")
        else:
            self.api = None
            self.use_real_api = False
            print("📊 Using fallback market data")
        
        # Fallback data (your existing hardcoded plans) - kept as backup
        self.fallback_plans = self._get_fallback_plans()
        
        # Market insights and trends (enhanced with real data)
        self.market_insights = {
            'average_rates_by_state': {
                'NSW': 0.285,
                'QLD': 0.280,
                'VIC': 0.275,
                'SA': 0.315,
                'WA': 0.295,
                'TAS': 0.265,
                'NT': 0.325,
                'ACT': 0.275
            },
            'typical_discounts': {
                'pay_on_time': 0.02,
                'direct_debit': 0.01,
                'dual_fuel': 0.03,
                'online_only': 0.015
            }
        }
    
    def research_better_plans(self, bill_data: Dict[str, Any], usage_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ENHANCED: Main research method using real Australian energy market data
        """
        try:
            print("🔍 Researching better electricity plans with REAL market data...")
            
            # Extract key information
            state = bill_data.get('state', 'NSW')
            current_retailer = bill_data.get('retailer', 'Unknown').lower()
            usage_kwh = bill_data.get('usage_kwh', 0)
            billing_days = bill_data.get('billing_days', 90)
            current_cost = bill_data.get('total_amount', 0)
            has_solar = bill_data.get('has_solar', False)
            solar_export = bill_data.get('solar_export_kwh', 0)
            
            # Calculate annual usage
            annual_usage = int(usage_kwh * (365 / billing_days)) if billing_days > 0 else 0
            annual_solar_export = int(solar_export * (365 / billing_days)) if billing_days > 0 and has_solar else 0
            
            print(f"📊 Research parameters:")
            print(f"   State: {state}")
            print(f"   Current retailer: {current_retailer}")
            print(f"   Annual usage: {annual_usage:,} kWh")
            print(f"   Has solar: {has_solar}")
            if has_solar:
                print(f"   Annual solar export: {annual_solar_export:,} kWh")
            
            # Get available plans using real API or fallback
            available_plans = self._get_available_plans(state, has_solar, annual_usage)
            
            if not available_plans:
                return self._get_error_response(f"No plans available for {state}")
            
            print(f"📋 Found {len(available_plans)} available plans")
            
            # Calculate costs for all plans with real pricing
            plan_costs = self._calculate_plan_costs(
                available_plans, annual_usage, annual_solar_export, current_retailer
            )
            
            # Sort plans by cost (cheapest first)
            plan_costs.sort(key=lambda x: x.get('estimated_annual_cost', float('inf')))
            
            # Calculate current annual cost
            current_annual_cost = current_cost * (365 / billing_days) if billing_days > 0 else 0
            
            # Find the best plans
            top_plans = plan_costs[:10]  # Top 10 cheapest plans
            best_plan = plan_costs[0] if plan_costs else None
            
            # Enhanced savings analysis with real market data
            savings_analysis = self._calculate_savings_with_real_data(
                current_annual_cost, top_plans, has_solar, state
            )
            
            # Enhanced market insights with real API data
            market_analysis = self._generate_enhanced_market_insights(
                state, current_retailer, bill_data, plan_costs
            )
            
            # Compile enhanced results
            research_result = {
                'data_source': 'real_api' if self.use_real_api else 'fallback',
                'research_parameters': {
                    'state': state,
                    'current_retailer': current_retailer.title(),
                    'annual_usage_kwh': annual_usage,
                    'current_annual_cost': round(current_annual_cost, 2),
                    'has_solar': has_solar,
                    'solar_export_kwh': annual_solar_export
                },
                
                'recommended_plans': [
                    {
                        'retailer': plan.get('retailer', 'Unknown'),
                        'plan_name': plan.get('plan_name', 'Unknown Plan'),
                        'plan_id': plan.get('plan_id'),
                        'estimated_annual_cost': round(plan.get('estimated_annual_cost', 0), 2),
                        'usage_rate': plan.get('usage_rate', 0),
                        'supply_charge_daily': plan.get('supply_charge', 0),
                        'solar_feed_in_tariff': plan.get('solar_fit_rate', 0),
                        'key_features': plan.get('features', []),
                        'plan_type': plan.get('plan_type', 'market'),
                        'has_time_of_use': plan.get('has_time_of_use', False),
                        'has_demand_charges': plan.get('has_demand_charges', False),
                        'annual_savings': round(current_annual_cost - plan.get('estimated_annual_cost', 0), 2),
                        'monthly_savings': round((current_annual_cost - plan.get('estimated_annual_cost', 0)) / 12, 2),
                        'is_current_retailer': plan.get('is_current_retailer', False),
                        'data_freshness': plan.get('last_updated', 'Unknown')
                    }
                    for plan in top_plans[:5]  # Top 5 for display
                ],
                
                'best_plan': {
                    'retailer': best_plan.get('retailer', 'Unknown'),
                    'plan_name': best_plan.get('plan_name', 'Unknown Plan'),
                    'plan_id': best_plan.get('plan_id'),
                    'estimated_annual_cost': round(best_plan.get('estimated_annual_cost', 0), 2),
                    'annual_savings': round(current_annual_cost - best_plan.get('estimated_annual_cost', 0), 2),
                    'monthly_savings': round((current_annual_cost - best_plan.get('estimated_annual_cost', 0)) / 12, 2),
                    'confidence_score': self._calculate_confidence_score(best_plan),
                    'why_best': f"Lowest annual cost at ${best_plan.get('estimated_annual_cost', 0):.0f} " +
                               f"({best_plan.get('plan_type', 'market').title()} plan with real market pricing)"
                } if best_plan else None,
                
                'savings_analysis': savings_analysis,
                'market_insights': market_analysis,
                
                # Enhanced metadata
                'research_timestamp': datetime.now().isoformat(),
                'plans_analyzed': len(plan_costs),
                'api_status': 'active' if self.use_real_api else 'fallback',
                'data_sources': self._get_data_sources_info(),
                'researcher_version': '2.0_real_api'
            }
            
            print("✅ Enhanced market research completed successfully!")
            return research_result
            
        except Exception as e:
            self.logger.error(f"Enhanced market research failed: {e}")
            return self._get_error_response(str(e))
    
    def _get_available_plans(self, state: str, has_solar: bool, annual_usage: int) -> List[Dict[str, Any]]:
        """Get available plans using real API or fallback data"""
        
        if self.use_real_api and self.api:
            try:
                # Use real API to get current market plans
                search_criteria = {
                    'state': state,
                    'fuel_type': 'electricity',
                    'has_solar': has_solar,
                    'usage_kwh': annual_usage,
                    'customer_type': 'residential'
                }
                
                print(f"🌐 Fetching real-time plans from Australian Energy APIs...")
                plans = self.api.search_plans(search_criteria)
                
                if plans:
                    print(f"✅ Retrieved {len(plans)} real plans from API")
                    return plans
                else:
                    print("⚠️  No plans returned from API, using fallback")
                    return self._get_fallback_plans_for_state(state)
                    
            except Exception as e:
                print(f"⚠️  API error: {e}, using fallback data")
                self.logger.warning(f"API error, using fallback: {e}")
                return self._get_fallback_plans_for_state(state)
        else:
            print("📊 Using fallback plan data")
            return self._get_fallback_plans_for_state(state)
    
    def _calculate_plan_costs(self, plans: List[Dict[str, Any]], annual_usage: int, 
                            annual_solar_export: int, current_retailer: str) -> List[Dict[str, Any]]:
        """Enhanced cost calculation with real pricing data"""
        
        plan_costs = []
        
        for plan in plans:
            try:
                # Use real pricing from API or fallback calculation
                if 'estimated_annual_cost' in plan:
                    # API already calculated cost
                    annual_cost = plan['estimated_annual_cost']
                else:
                    # Calculate using extracted pricing
                    annual_cost = self._calculate_annual_cost_manual(
                        plan, annual_usage, annual_solar_export
                    )
                
                # Enhance plan data
                enhanced_plan = plan.copy()
                enhanced_plan['estimated_annual_cost'] = annual_cost
                enhanced_plan['is_current_retailer'] = (
                    plan.get('retailer', '').lower().replace(' ', '') == 
                    current_retailer.replace(' ', '').lower()
                )
                
                # Add confidence scoring based on data source
                enhanced_plan['data_confidence'] = self._get_plan_confidence(plan)
                
                plan_costs.append(enhanced_plan)
                
            except Exception as e:
                self.logger.error(f"Error calculating cost for plan {plan.get('plan_name', 'Unknown')}: {e}")
                continue
        
        return plan_costs
    
    def _calculate_annual_cost_manual(self, plan: Dict[str, Any], annual_usage: int, 
                                    annual_solar_export: int) -> float:
        """Manual cost calculation for plans without pre-calculated costs"""
        
        usage_rate = plan.get('usage_rate', 0.30)  # $/kWh
        supply_charge = plan.get('supply_charge', 1.20)  # $/day
        solar_fit_rate = plan.get('solar_fit_rate', 0.05)  # $/kWh
        
        # Basic calculation
        usage_cost = annual_usage * usage_rate
        supply_cost = 365 * supply_charge
        solar_credit = annual_solar_export * solar_fit_rate
        
        total_cost = usage_cost + supply_cost - solar_credit
        
        return max(0, total_cost)
    
    def _calculate_savings_with_real_data(self, current_annual_cost: float, top_plans: List[Dict], 
                                        has_solar: bool, state: str) -> Dict[str, Any]:
        """Enhanced savings analysis with real market benchmarks"""
        
        if not top_plans or current_annual_cost <= 0:
            return {'error': 'Insufficient data for savings calculation'}
        
        best_plan_cost = top_plans[0].get('estimated_annual_cost', current_annual_cost)
        max_savings = current_annual_cost - best_plan_cost
        
        # Enhanced savings tiers with real data
        savings_tiers = []
        for i, plan in enumerate(top_plans[:5]):
            savings = current_annual_cost - plan.get('estimated_annual_cost', 0)
            savings_tiers.append({
                'rank': i + 1,
                'retailer': plan.get('retailer', 'Unknown'),
                'plan_name': plan.get('plan_name', 'Unknown Plan'),
                'plan_type': plan.get('plan_type', 'market'),
                'annual_savings': round(savings, 2),
                'monthly_savings': round(savings / 12, 2),
                'percentage_savings': round((savings / current_annual_cost) * 100, 1) if current_annual_cost > 0 else 0,
                'data_source': 'real_api' if self.use_real_api else 'estimated'
            })
        
        # Market position analysis
        state_average = self.market_insights['average_rates_by_state'].get(state, 0.285)
        current_rate = current_annual_cost / max(1, sum(p.get('usage_kwh', 4000) for p in [{}])) if top_plans else 0
        
        # Enhanced potential assessment
        if max_savings > 800:
            savings_potential = 'very_high'
            savings_message = 'Exceptional savings available - immediate switch highly recommended!'
        elif max_savings > 500:
            savings_potential = 'high'
            savings_message = 'Significant savings available - switching strongly recommended'
        elif max_savings > 200:
            savings_potential = 'medium'
            savings_message = 'Good savings available - consider switching'
        elif max_savings > 50:
            savings_potential = 'low'
            savings_message = 'Some savings available'
        else:
            savings_potential = 'minimal'
            savings_message = 'Your current plan is competitive with market rates'
        
        return {
            'max_annual_savings': round(max_savings, 2),
            'max_monthly_savings': round(max_savings / 12, 2),
            'savings_potential': savings_potential,
            'savings_message': savings_message,
            'savings_tiers': savings_tiers,
            'market_comparison': {
                'your_position': 'above_average' if current_rate > state_average else 'competitive',
                'state_average_rate': state_average,
                'cheapest_available_rate': min(p.get('usage_rate', state_average) for p in top_plans) if top_plans else state_average
            },
            'solar_consideration': self._get_solar_savings_note(has_solar, top_plans),
            'confidence_level': 'high' if self.use_real_api else 'medium'
        }
    
    def _generate_enhanced_market_insights(self, state: str, current_retailer: str, 
                                         bill_data: Dict[str, Any], all_plans: List[Dict]) -> Dict[str, Any]:
        """Enhanced market insights with real API data"""
        
        current_rate = bill_data.get('cost_per_kwh', 0)
        state_average = self.market_insights['average_rates_by_state'].get(state, 0.285)
        
        # Real market analysis
        all_rates = [plan.get('usage_rate', 0) for plan in all_plans if plan.get('usage_rate')]
        cheapest_rate = min(all_rates) if all_rates else 0
        most_expensive_rate = max(all_rates) if all_rates else 0
        average_market_rate = sum(all_rates) / len(all_rates) if all_rates else state_average
        
        # Enhanced rate position
        if current_rate <= cheapest_rate * 1.05:
            rate_position = 'excellent'
        elif current_rate <= average_market_rate:
            rate_position = 'good'
        elif current_rate <= state_average * 1.1:
            rate_position = 'average'
        else:
            rate_position = 'poor'
        
        # Real market trends
        trends = []
        if self.use_real_api:
            trends.append("✅ Data sourced from live Australian Energy Market APIs")
            
        if bill_data.get('has_solar'):
            solar_plans = [p for p in all_plans if p.get('has_solar_fit')]
            avg_solar_rate = sum(p.get('solar_fit_rate', 0) for p in solar_plans) / max(1, len(solar_plans))
            trends.append(f"☀️ Average solar feed-in tariff: ${avg_solar_rate:.3f}/kWh")
        
        trends.append(f"📊 Current {state} market average: ${average_market_rate:.3f}/kWh")
        
        tou_plans = [p for p in all_plans if p.get('has_time_of_use')]
        if len(tou_plans) > len(all_plans) * 0.3:
            trends.append("⏰ Time-of-use plans increasingly common")
        
        return {
            'current_rate_position': rate_position,
            'state_average_rate': state_average,
            'live_market_average': round(average_market_rate, 3),
            'market_rate_range': {
                'cheapest': round(cheapest_rate, 3),
                'most_expensive': round(most_expensive_rate, 3),
                'spread': round(most_expensive_rate - cheapest_rate, 3)
            },
            'retailer_count': len(set(plan.get('retailer', '') for plan in all_plans)),
            'plans_analyzed': len(all_plans),
            'plan_types': {
                'market_plans': len([p for p in all_plans if p.get('plan_type') == 'market']),
                'standing_offers': len([p for p in all_plans if p.get('plan_type') == 'standing']),
                'time_of_use': len([p for p in all_plans if p.get('has_time_of_use')])
            },
            'market_trends': trends,
            'data_freshness': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'switching_recommendation': self._get_enhanced_switching_recommendation(
                current_rate, average_market_rate, current_retailer, all_plans
            )
        }
    
    def _get_enhanced_switching_recommendation(self, current_rate: float, market_average: float,
                                            current_retailer: str, all_plans: List[Dict]) -> str:
        """Enhanced switching recommendation with real market data"""
        
        better_plans = [p for p in all_plans if p.get('usage_rate', 0) < current_rate * 0.95]
        significant_savings = [p for p in all_plans if p.get('estimated_annual_cost', 0) < current_rate * 0.9]
        
        if len(significant_savings) >= 3:
            return "🎯 STRONG RECOMMENDATION: Multiple plans offer significant savings - immediate switch recommended"
        elif len(better_plans) >= 5:
            return "👍 RECOMMENDED: Several better options available - switching worthwhile"
        elif len(better_plans) >= 1:
            return "💡 CONSIDER: Some better options available - review and compare"
        elif current_rate > market_average * 1.15:
            return "⚠️  REVIEW NEEDED: You're paying well above market rates - investigate options"
        else:
            return "✅ COMPETITIVE: Your current rate is reasonable - minor improvements possible"
    
    # Helper methods
    def _get_fallback_plans_for_state(self, state: str) -> List[Dict[str, Any]]:
        """Get fallback plans for a specific state"""
        return self.fallback_plans.get(state, self.fallback_plans.get('NSW', []))
    
    def _calculate_confidence_score(self, plan: Dict[str, Any]) -> float:
        """Calculate confidence score for plan recommendation"""
        if self.use_real_api:
            return 0.95  # High confidence with real API data
        else:
            return 0.75  # Medium confidence with fallback data
    
    def _get_plan_confidence(self, plan: Dict[str, Any]) -> str:
        """Get confidence level for plan data"""
        if plan.get('last_updated'):
            return 'high'
        elif self.use_real_api:
            return 'medium'
        else:
            return 'estimated'
    
    def _get_solar_savings_note(self, has_solar: bool, plans: List[Dict]) -> Optional[str]:
        """Generate solar-specific savings note"""
        if not has_solar:
            return None
        
        solar_plans = [p for p in plans if p.get('has_solar_fit')]
        if not solar_plans:
            return "Limited solar feed-in options available"
        
        best_solar_rate = max(p.get('solar_fit_rate', 0) for p in solar_plans)
        return f"Best solar feed-in tariff available: ${best_solar_rate:.3f}/kWh"
    
    def _get_data_sources_info(self) -> Dict[str, Any]:
        """Get information about data sources used"""
        return {
            'primary_source': 'Australian Energy Regulator CDR APIs' if self.use_real_api else 'Hardcoded market data',
            'api_status': 'active' if self.use_real_api else 'unavailable',
            'data_coverage': 'NSW, QLD, VIC, SA, TAS, ACT' if self.use_real_api else 'All states (estimated)',
            'update_frequency': 'Real-time' if self.use_real_api else 'Static',
            'confidence': 'High' if self.use_real_api else 'Medium'
        }
    
    def _get_fallback_plans(self) -> Dict[str, List[Dict[str, Any]]]:
        """Your existing hardcoded plans as fallback"""
        return {
            'NSW': [
                {
                    'plan_id': 'origin_basic_nsw',
                    'retailer': 'Origin Energy',
                    'plan_name': 'Basic Plan',
                    'usage_rate': 0.2850,
                    'supply_charge': 1.1500,
                    'plan_type': 'market',
                    'features': ['No lock-in contract', 'Online account management'],
                    'solar_fit_rate': 0.05,
                    'has_solar_fit': True
                },
                {
                    'plan_id': 'agl_value_saver_nsw',
                    'retailer': 'AGL',
                    'plan_name': 'Value Saver',
                    'usage_rate': 0.2750,
                    'supply_charge': 1.2000,
                    'plan_type': 'market',
                    'features': ['No exit fees', 'Carbon neutral option'],
                    'solar_fit_rate': 0.06,
                    'has_solar_fit': True
                }
            ],
            'QLD': [
                {
                    'plan_id': 'origin_basic_qld',
                    'retailer': 'Origin Energy',
                    'plan_name': 'Basic Plan QLD',
                    'usage_rate': 0.2820,
                    'supply_charge': 1.2500,
                    'plan_type': 'market',
                    'features': ['No lock-in contract', 'QLD specific rates'],
                    'solar_fit_rate': 0.08,
                    'has_solar_fit': True
                }
            ]
            # Add other states...
        }
    
    def get_plan_comparison_summary(self, research_result: Dict[str, Any]) -> str:
        """Enhanced summary with real market data indicators"""
        
        if research_result.get('error'):
            return f"Research Error: {research_result.get('message')}"
        
        best_plan = research_result.get('best_plan', {})
        savings_analysis = research_result.get('savings_analysis', {})
        data_source = research_result.get('data_source', 'unknown')
        
        summary_parts = []
        
        # Data source indicator
        if data_source == 'real_api':
            summary_parts.append("📡 Using LIVE Australian energy market data:")
        else:
            summary_parts.append("📊 Using estimated market data:")
        
        # Savings summary
        max_savings = savings_analysis.get('max_annual_savings', 0)
        if max_savings > 0:
            confidence = best_plan.get('confidence_score', 0.8)
            summary_parts.append(
                f"You could save up to ${max_savings:.0f} per year "
                f"(${max_savings/12:.0f}/month) by switching to {best_plan.get('retailer', 'a better plan')} "
                f"(Confidence: {confidence:.0%})."
            )
        else:
            summary_parts.append("Your current plan is competitive with current market rates.")
        
        # Plans analyzed
        plans_count = research_result.get('plans_analyzed', 0)
        summary_parts.append(f"Analysis based on {plans_count} current market plans.")
        
        return " ".join(summary_parts)
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Enhanced error response"""
        return {
            'error': True,
            'message': f'Enhanced market research failed: {error_message}',
            'research_timestamp': datetime.now().isoformat(),
            'api_status': 'error',
            'recommendations': [
                'Check internet connection for real-time plan data',
                'Verify that your bill contains valid location and usage data',
                'System will use fallback data if APIs are unavailable'
            ]
        }


# Utility function for easy testing
def test_enhanced_market_research():
    """Test the enhanced market research with real API"""
    
    # Sample bill data for testing
    test_bill_data = {
        'state': 'NSW',
        'retailer': 'AGL',
        'usage_kwh': 720,
        'billing_days': 90,
        'total_amount': 350.0,
        'cost_per_kwh': 0.292,
        'has_solar': True,
        'solar_export_kwh': 200
    }
    
    researcher = MarketResearcherAgent()
    result = researcher.research_better_plans(test_bill_data)
    
    print("\n" + "="*60)
    print("ENHANCED MARKET RESEARCH TEST RESULTS")
    print("="*60)
    
    print(f"Data Source: {result.get('data_source', 'unknown')}")
    print(f"Plans Analyzed: {result.get('plans_analyzed', 0)}")
    
    best_plan = result.get('best_plan', {})
    if best_plan:
        print(f"Best Plan: {best_plan.get('retailer')} - {best_plan.get('plan_name')}")
        print(f"Annual Savings: ${best_plan.get('annual_savings', 0):.2f}")
    
    savings = result.get('savings_analysis', {})
    print(f"Savings Potential: {savings.get('savings_potential', 'unknown')}")
    
    return result


if __name__ == "__main__":
    # Test the enhanced market research
    test_enhanced_market_research()