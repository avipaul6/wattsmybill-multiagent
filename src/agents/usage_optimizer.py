"""
Energy Usage Optimizer Agent
File: src/agents/usage_optimizer.py
"""
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class UsageOptimizerAgent:
    """
    Specialized agent for optimizing energy usage patterns and behaviors
    Focuses on practical, actionable recommendations for Australian households
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Australian household usage benchmarks and patterns
        self.usage_benchmarks = {
            'daily_averages': {
                'NSW': {'low': 7.5, 'medium': 15.0, 'high': 25.0},
                'VIC': {'low': 7.0, 'medium': 14.0, 'high': 23.0},
                'QLD': {'low': 8.0, 'medium': 16.0, 'high': 27.0},
                'SA': {'low': 6.5, 'medium': 13.0, 'high': 22.0},
                'WA': {'low': 8.5, 'medium': 17.0, 'high': 28.0},
                'TAS': {'low': 6.0, 'medium': 12.0, 'high': 20.0},
                'NT': {'low': 9.0, 'medium': 18.0, 'high': 30.0},
                'ACT': {'low': 7.0, 'medium': 14.0, 'high': 24.0}
            }
        }
        
        # Appliance usage patterns and optimization potential
        self.appliance_optimization = {
            'heating_cooling': {
                'usage_percentage': 40,  # 40% of typical household usage
                'optimization_potential': 20,  # 20% savings possible
                'difficulty': 'easy',
                'season_dependent': True
            },
            'water_heating': {
                'usage_percentage': 25,
                'optimization_potential': 15,
                'difficulty': 'medium',
                'season_dependent': False
            },
            'appliances': {
                'usage_percentage': 20,
                'optimization_potential': 25,
                'difficulty': 'easy',
                'season_dependent': False
            },
            'lighting': {
                'usage_percentage': 10,
                'optimization_potential': 80,  # LED conversion
                'difficulty': 'easy',
                'season_dependent': False
            },
            'other': {
                'usage_percentage': 5,
                'optimization_potential': 10,
                'difficulty': 'hard',
                'season_dependent': False
            }
        }
        
        # Time-of-use optimization opportunities
        self.time_of_use_patterns = {
            'peak_hours': {
                'typical_times': '4pm-9pm weekdays',
                'rate_multiplier': 1.5,
                'shift_potential': 30  # 30% of usage can be shifted
            },
            'off_peak_hours': {
                'typical_times': '10pm-6am',
                'rate_multiplier': 0.7,
                'shift_potential': 40
            },
            'shoulder_hours': {
                'typical_times': '6am-4pm, 9pm-10pm',
                'rate_multiplier': 1.0,
                'shift_potential': 20
            }
        }
        
        # Solar optimization strategies
        self.solar_optimization = {
            'peak_generation': {
                'typical_times': '10am-3pm',
                'generation_percentage': 70,
                'self_consumption_opportunity': 60
            },
            'load_shifting': {
                'potential_savings': 15,  # % savings from optimal timing
                'appliances': ['dishwasher', 'washing_machine', 'pool_pump', 'electric_vehicle']
            }
        }
        
        # State-specific considerations
        self.state_considerations = {
            'QLD': {
                'climate': 'subtropical',
                'peak_season': 'summer',
                'cooling_dominant': True,
                'solar_potential': 'excellent',
                'time_of_use_available': True
            },
            'NSW': {
                'climate': 'temperate',
                'peak_season': 'summer/winter',
                'heating_cooling_balanced': True,
                'solar_potential': 'good',
                'time_of_use_available': True
            },
            'VIC': {
                'climate': 'temperate',
                'peak_season': 'winter',
                'heating_dominant': True,
                'solar_potential': 'good',
                'time_of_use_available': True
            },
            'SA': {
                'climate': 'mediterranean',
                'peak_season': 'summer',
                'cooling_dominant': True,
                'solar_potential': 'excellent',
                'time_of_use_available': True
            },
            'WA': {
                'climate': 'mediterranean',
                'peak_season': 'summer',
                'cooling_dominant': True,
                'solar_potential': 'excellent',
                'time_of_use_available': False  # Different market structure
            }
        }
    
    def optimize_energy_usage(self, bill_analysis: Dict[str, Any], 
                            preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Main method to generate personalized energy usage optimization recommendations
        
        Args:
            bill_analysis: Analysis from BillAnalyzerAgent
            preferences: User preferences and constraints
            
        Returns:
            Dictionary with optimization opportunities and recommendations
        """
        try:
            if preferences is None:
                preferences = {}
            
            print("⚡ Analyzing usage patterns for optimization opportunities...")
            
            # Extract key data from bill analysis
            usage_data = self._extract_usage_data(bill_analysis)
            
            # Analyze current usage patterns
            usage_analysis = self._analyze_usage_patterns(usage_data)
            
            # Generate optimization opportunities
            opportunities = []
            
            # 1. HVAC optimization (biggest impact)
            hvac_opportunities = self._analyze_hvac_optimization(usage_data, usage_analysis)
            opportunities.extend(hvac_opportunities)
            
            # 2. Time-shifting opportunities
            time_shift_opportunities = self._analyze_time_shifting(usage_data, usage_analysis)
            opportunities.extend(time_shift_opportunities)
            
            # 3. Solar optimization (if applicable)
            if usage_data.get('has_solar'):
                solar_opportunities = self._analyze_solar_optimization(usage_data, usage_analysis)
                opportunities.extend(solar_opportunities)
            
            # 4. Appliance efficiency
            appliance_opportunities = self._analyze_appliance_efficiency(usage_data, usage_analysis)
            opportunities.extend(appliance_opportunities)
            
            # 5. Behavioral changes
            behavioral_opportunities = self._analyze_behavioral_changes(usage_data, usage_analysis)
            opportunities.extend(behavioral_opportunities)
            
            # Calculate totals and prioritize
            total_monthly_savings = sum(opp['potential_monthly_savings'] for opp in opportunities)
            total_annual_savings = sum(opp['potential_annual_savings'] for opp in opportunities)
            
            # Categorize by difficulty and timeline
            quick_wins = [opp for opp in opportunities if opp['difficulty'] == 'easy']
            medium_term = [opp for opp in opportunities if opp['difficulty'] == 'medium']
            long_term = [opp for opp in opportunities if opp['difficulty'] == 'hard']
            
            # Generate implementation plan
            implementation_plan = self._generate_implementation_plan(opportunities, preferences)
            
            # Calculate optimization score
            optimization_score = self._calculate_optimization_score(opportunities, usage_analysis)
            
            result = {
                'optimization_opportunities': sorted(opportunities, key=lambda x: x['potential_annual_savings'], reverse=True),
                'total_monthly_savings': round(total_monthly_savings, 2),
                'total_annual_savings': round(total_annual_savings, 2),
                'optimization_score': optimization_score,
                'usage_category_analyzed': usage_analysis.get('category'),
                'state_specific_recommendations': usage_data.get('state'),
                'solar_optimizations_included': usage_data.get('has_solar', False),
                
                'categorized_opportunities': {
                    'quick_wins': [opp['recommendation'] for opp in quick_wins],
                    'medium_term_projects': [opp['recommendation'] for opp in medium_term],
                    'long_term_investments': [opp['recommendation'] for opp in long_term]
                },
                
                'implementation_plan': implementation_plan,
                'confidence_level': 'high' if len(opportunities) >= 3 else 'medium',
                'agent_version': '1.0_usage_optimizer',
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Found {len(opportunities)} optimization opportunities for ${total_annual_savings:.0f} annual savings")
            return result
            
        except Exception as e:
            self.logger.error(f"Usage optimization failed: {e}")
            return self._get_error_response(str(e))
    
    def _extract_usage_data(self, bill_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant usage data from bill analysis"""
        try:
            # Handle different bill analysis formats
            if 'analysis' in bill_analysis:
                analysis = bill_analysis['analysis']
            else:
                analysis = bill_analysis
            
            usage_profile = analysis.get('usage_profile', {})
            cost_breakdown = analysis.get('cost_breakdown', {})
            solar_analysis = analysis.get('solar_analysis', {})
            bill_data = analysis.get('bill_data', {})
            
            return {
                'daily_usage': usage_profile.get('daily_average', 0),
                'total_usage': usage_profile.get('total_kwh', 0),
                'usage_category': usage_profile.get('usage_category', 'medium'),
                'annual_usage': usage_profile.get('annual_projection', 0),
                'cost_per_kwh': cost_breakdown.get('cost_per_kwh', 0.30),
                'total_cost': cost_breakdown.get('total_cost', 0),
                'billing_days': bill_data.get('billing_days', 90),
                'state': bill_data.get('state', 'QLD'),
                'tariff_type': bill_data.get('tariff_type', 'single_rate'),
                'has_solar': solar_analysis.get('has_solar', False),
                'solar_export_ratio': solar_analysis.get('export_ratio_percent', 0),
                'solar_performance': solar_analysis.get('performance_rating', 'none')
            }
        except Exception as e:
            self.logger.warning(f"Could not extract usage data: {e}")
            return {
                'daily_usage': 15,  # Default values
                'usage_category': 'medium',
                'cost_per_kwh': 0.30,
                'state': 'QLD',
                'has_solar': False
            }
    
    def _analyze_usage_patterns(self, usage_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze usage patterns to identify optimization potential"""
        daily_usage = usage_data.get('daily_usage', 15)
        state = usage_data.get('state', 'QLD')
        usage_category = usage_data.get('usage_category', 'medium')
        
        # Get state benchmarks
        state_benchmarks = self.usage_benchmarks['daily_averages'].get(state, self.usage_benchmarks['daily_averages']['QLD'])
        
        # Determine usage efficiency
        if daily_usage <= state_benchmarks['low']:
            efficiency = 'high'
            optimization_potential = 'low'
        elif daily_usage <= state_benchmarks['medium']:
            efficiency = 'medium'
            optimization_potential = 'medium'
        else:
            efficiency = 'low'
            optimization_potential = 'high'
        
        return {
            'category': usage_category,
            'efficiency': efficiency,
            'optimization_potential': optimization_potential,
            'state_benchmark': state_benchmarks,
            'above_average': daily_usage > state_benchmarks['medium'],
            'climate_zone': self.state_considerations.get(state, {}).get('climate', 'temperate')
        }
    
    def _analyze_hvac_optimization(self, usage_data: Dict[str, Any], usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze heating/cooling optimization opportunities"""
        opportunities = []
        
        daily_usage = usage_data.get('daily_usage', 15)
        cost_per_kwh = usage_data.get('cost_per_kwh', 0.30)
        state = usage_data.get('state', 'QLD')
        
        # HVAC typically 40% of household usage
        hvac_usage = daily_usage * 0.4
        hvac_monthly_cost = hvac_usage * 30 * cost_per_kwh
        
        state_info = self.state_considerations.get(state, {})
        
        # Temperature adjustment opportunities
        if daily_usage > 10:  # Only for moderate+ usage
            temp_savings = hvac_monthly_cost * 0.15  # 15% savings from 2°C adjustment
            opportunities.append({
                'type': 'behavioral',
                'recommendation': f'Adjust thermostat by 2°C: 24°C summer, 20°C winter for {state}',
                'potential_monthly_savings': round(temp_savings, 2),
                'potential_annual_savings': round(temp_savings * 12, 2),
                'difficulty': 'easy',
                'implementation': f'Set air conditioning to 24°C in summer, heating to 20°C in winter',
                'priority': 'high',
                'category': 'hvac_optimization',
                'state_specific': True,
                'estimated_effort': '5 minutes'
            })
        
        # Insulation and sealing
        if usage_analysis.get('above_average'):
            insulation_savings = hvac_monthly_cost * 0.20  # 20% from better insulation
            opportunities.append({
                'type': 'investment',
                'recommendation': 'Improve home insulation and seal air leaks',
                'potential_monthly_savings': round(insulation_savings, 2),
                'potential_annual_savings': round(insulation_savings * 12, 2),
                'difficulty': 'hard',
                'implementation': 'Professional energy audit, ceiling/wall insulation, door/window sealing',
                'priority': 'medium',
                'category': 'hvac_optimization',
                'upfront_cost_estimate': '$2000-5000',
                'payback_period': '3-5 years'
            })
        
        # Smart thermostat
        if daily_usage > 15:
            smart_savings = hvac_monthly_cost * 0.10  # 10% from smart control
            opportunities.append({
                'type': 'equipment',
                'recommendation': 'Install smart thermostat with scheduling',
                'potential_monthly_savings': round(smart_savings, 2),
                'potential_annual_savings': round(smart_savings * 12, 2),
                'difficulty': 'medium',
                'implementation': 'Install programmable or smart thermostat, set efficient schedules',
                'priority': 'medium',
                'category': 'hvac_optimization',
                'upfront_cost_estimate': '$200-500',
                'payback_period': '1-2 years'
            })
        
        return opportunities
    
    def _analyze_time_shifting(self, usage_data: Dict[str, Any], usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze time-of-use shifting opportunities"""
        opportunities = []
        
        daily_usage = usage_data.get('daily_usage', 15)
        cost_per_kwh = usage_data.get('cost_per_kwh', 0.30)
        tariff_type = usage_data.get('tariff_type', 'single_rate')
        state = usage_data.get('state', 'QLD')
        
        # Only recommend if time-of-use tariffs are available
        state_info = self.state_considerations.get(state, {})
        if not state_info.get('time_of_use_available', True):
            return opportunities
        
        # Appliance shifting (30% of usage can be shifted)
        shiftable_usage = daily_usage * 0.3
        
        if tariff_type == 'single_rate' and daily_usage > 10:
            # Recommend switching to time-of-use
            potential_savings = shiftable_usage * 30 * cost_per_kwh * 0.25  # 25% savings on shifted usage
            opportunities.append({
                'type': 'tariff_change',
                'recommendation': f'Switch to time-of-use tariff and shift appliance usage to off-peak hours',
                'potential_monthly_savings': round(potential_savings, 2),
                'potential_annual_savings': round(potential_savings * 12, 2),
                'difficulty': 'easy',
                'implementation': 'Contact retailer for time-of-use tariff, use appliance timers',
                'priority': 'high',
                'category': 'time_shifting',
                'best_times': 'Off-peak: 10pm-6am, Shoulder: 6am-4pm',
                'appliances': ['dishwasher', 'washing machine', 'clothes dryer', 'pool pump']
            })
        
        elif tariff_type == 'time_of_use':
            # Optimize existing time-of-use
            optimization_savings = shiftable_usage * 30 * cost_per_kwh * 0.15  # 15% additional savings
            opportunities.append({
                'type': 'timing',
                'recommendation': 'Optimize appliance usage timing for maximum off-peak benefits',
                'potential_monthly_savings': round(optimization_savings, 2),
                'potential_annual_savings': round(optimization_savings * 12, 2),
                'difficulty': 'easy',
                'implementation': 'Use smart plugs/timers, shift more usage to 10pm-6am',
                'priority': 'medium',
                'category': 'time_shifting',
                'current_tariff': 'time_of_use'
            })
        
        return opportunities
    
    def _analyze_solar_optimization(self, usage_data: Dict[str, Any], usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze solar system optimization opportunities"""
        opportunities = []
        
        if not usage_data.get('has_solar'):
            return opportunities
        
        daily_usage = usage_data.get('daily_usage', 15)
        cost_per_kwh = usage_data.get('cost_per_kwh', 0.30)
        export_ratio = usage_data.get('solar_export_ratio', 0)
        solar_performance = usage_data.get('solar_performance', 'unknown')
        
        # Load shifting to maximize self-consumption
        if export_ratio > 40:  # High export - opportunity to use more during day
            load_shift_savings = daily_usage * 0.2 * cost_per_kwh * 30  # 20% load shifting
            opportunities.append({
                'type': 'timing',
                'recommendation': 'Shift more electricity usage to daytime during peak solar generation',
                'potential_monthly_savings': round(load_shift_savings, 2),
                'potential_annual_savings': round(load_shift_savings * 12, 2),
                'difficulty': 'medium',
                'implementation': 'Run appliances 10am-3pm: dishwasher, washing machine, pool pump',
                'priority': 'high',
                'category': 'solar_optimization',
                'current_export_ratio': f'{export_ratio}%',
                'optimal_usage_times': '10am-3pm (peak solar generation)'
            })
        
        # Battery storage consideration
        if export_ratio > 60:  # Very high export
            battery_savings = daily_usage * 0.25 * cost_per_kwh * 30  # 25% savings potential
            opportunities.append({
                'type': 'investment',
                'recommendation': 'Consider battery storage to capture excess solar generation',
                'potential_monthly_savings': round(battery_savings, 2),
                'potential_annual_savings': round(battery_savings * 12, 2),
                'difficulty': 'hard',
                'implementation': 'Get battery system quotes, consider 10-15kWh capacity',
                'priority': 'medium',
                'category': 'solar_optimization',
                'upfront_cost_estimate': '$8000-15000',
                'payback_period': '7-12 years',
                'additional_benefits': 'Backup power, grid independence'
            })
        
        # Solar system maintenance/optimization
        if solar_performance in ['moderate', 'low_export']:
            maintenance_savings = daily_usage * 0.05 * cost_per_kwh * 30  # 5% from maintenance
            opportunities.append({
                'type': 'maintenance',
                'recommendation': 'Optimize solar system performance through cleaning and maintenance',
                'potential_monthly_savings': round(maintenance_savings, 2),
                'potential_annual_savings': round(maintenance_savings * 12, 2),
                'difficulty': 'easy',
                'implementation': 'Regular panel cleaning, system health check, inverter monitoring',
                'priority': 'low',
                'category': 'solar_optimization',
                'frequency': 'Quarterly cleaning, annual inspection'
            })
        
        return opportunities
    
    def _analyze_appliance_efficiency(self, usage_data: Dict[str, Any], usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze appliance efficiency opportunities"""
        opportunities = []
        
        daily_usage = usage_data.get('daily_usage', 15)
        cost_per_kwh = usage_data.get('cost_per_kwh', 0.30)
        
        # LED lighting conversion
        lighting_usage = daily_usage * 0.1  # 10% for lighting
        if lighting_usage > 1:  # If significant lighting usage
            led_savings = lighting_usage * 30 * cost_per_kwh * 0.8  # 80% savings from LED
            opportunities.append({
                'type': 'equipment',
                'recommendation': 'Replace remaining incandescent/halogen bulbs with LED lights',
                'potential_monthly_savings': round(led_savings, 2),
                'potential_annual_savings': round(led_savings * 12, 2),
                'difficulty': 'easy',
                'implementation': 'Replace old bulbs with LED equivalents, focus on most-used areas first',
                'priority': 'high',
                'category': 'appliance_efficiency',
                'upfront_cost_estimate': '$100-300',
                'payback_period': '6-12 months'
            })
        
        # Hot water system optimization
        if daily_usage > 12:  # Moderate+ usage
            water_heating_usage = daily_usage * 0.25  # 25% for water heating
            water_savings = water_heating_usage * 30 * cost_per_kwh * 0.15  # 15% savings
            opportunities.append({
                'type': 'behavioral',
                'recommendation': 'Optimize hot water usage: shorter showers, efficient settings',
                'potential_monthly_savings': round(water_savings, 2),
                'potential_annual_savings': round(water_savings * 12, 2),
                'difficulty': 'easy',
                'implementation': 'Set hot water to 60°C, use eco-mode, shorter showers (4-6 minutes)',
                'priority': 'medium',
                'category': 'appliance_efficiency'
            })
        
        # Energy-efficient appliances
        if usage_analysis.get('above_average'):
            appliance_savings = daily_usage * 0.15 * cost_per_kwh * 30  # 15% from efficient appliances
            opportunities.append({
                'type': 'investment',
                'recommendation': 'Upgrade to energy-efficient appliances when replacing old ones',
                'potential_monthly_savings': round(appliance_savings, 2),
                'potential_annual_savings': round(appliance_savings * 12, 2),
                'difficulty': 'hard',
                'implementation': 'Choose 5+ star energy rated: fridge, washing machine, dishwasher',
                'priority': 'low',
                'category': 'appliance_efficiency',
                'timing': 'When current appliances need replacement',
                'focus_appliances': ['refrigerator', 'washing_machine', 'dishwasher']
            })
        
        return opportunities
    
    def _analyze_behavioral_changes(self, usage_data: Dict[str, Any], usage_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze behavioral change opportunities"""
        opportunities = []
        
        daily_usage = usage_data.get('daily_usage', 15)
        cost_per_kwh = usage_data.get('cost_per_kwh', 0.30)
        
        # Standby power reduction
        standby_savings = daily_usage * 0.1 * cost_per_kwh * 30  # 10% from standby reduction
        opportunities.append({
            'type': 'behavioral',
            'recommendation': 'Reduce standby power consumption by switching off devices at power point',
            'potential_monthly_savings': round(standby_savings, 2),
            'potential_annual_savings': round(standby_savings * 12, 2),
            'difficulty': 'easy',
            'implementation': 'Use power boards with switches, unplug chargers, turn off TVs/computers completely',
            'priority': 'medium',
            'category': 'behavioral_changes',
            'estimated_effort': '5-10 minutes daily'
        })
        
        # Natural lighting and ventilation
        if daily_usage > 10:
            natural_savings = daily_usage * 0.08 * cost_per_kwh * 30  # 8% from natural alternatives
            opportunities.append({
                'type': 'behavioral',
                'recommendation': 'Maximize natural lighting and ventilation before using electrical alternatives',
                'potential_monthly_savings': round(natural_savings, 2),
                'potential_annual_savings': round(natural_savings * 12, 2),
                'difficulty': 'easy',
                'implementation': 'Open blinds/curtains for light, use fans before air conditioning',
                'priority': 'low',
                'category': 'behavioral_changes'
            })
        
        return opportunities
    
    def _generate_implementation_plan(self, opportunities: List[Dict[str, Any]], preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured implementation plan"""
        
        # Sort opportunities by priority and ease
        quick_wins = [opp for opp in opportunities if opp['difficulty'] == 'easy']
        medium_term = [opp for opp in opportunities if opp['difficulty'] == 'medium']
        long_term = [opp for opp in opportunities if opp['difficulty'] == 'hard']
        
        # Create timeline
        timeline = {
            'immediate_actions': [
                {
                    'timeframe': 'This week',
                    'actions': [opp['recommendation'] for opp in quick_wins[:3]],
                    'expected_savings': sum(opp['potential_monthly_savings'] for opp in quick_wins[:3])
                }
            ],
            'short_term_projects': [
                {
                    'timeframe': '1-3 months',
                    'actions': [opp['recommendation'] for opp in medium_term[:2]],
                    'expected_savings': sum(opp['potential_monthly_savings'] for opp in medium_term[:2])
                }
            ],
            'long_term_investments': [
                {
                    'timeframe': '6-12 months',
                    'actions': [opp['recommendation'] for opp in long_term[:2]],
                    'expected_savings': sum(opp['potential_monthly_savings'] for opp in long_term[:2])
                }
            ]
        }
        
        return {
            'timeline': timeline,
            'total_quick_wins': len(quick_wins),
            'estimated_setup_time': f"{len(quick_wins) * 2}-{len(quick_wins) * 5} hours",
            'priority_order': [opp['recommendation'] for opp in sorted(opportunities, key=lambda x: (x['potential_annual_savings'], x['difficulty'] == 'easy'), reverse=True)[:5]]
        }
    
    def _calculate_optimization_score(self, opportunities: List[Dict[str, Any]], usage_analysis: Dict[str, Any]) -> int:
        """Calculate optimization potential score (0-100)"""
        
        if not opportunities:
            return 20  # Some optimization always possible
        
        # Base score from number of opportunities
        opportunity_score = min(50, len(opportunities) * 10)
        
        # Savings potential score
        total_savings = sum(opp['potential_annual_savings'] for opp in opportunities)
        if total_savings > 500:
            savings_score = 30
        elif total_savings > 200:
            savings_score = 20
        elif total_savings > 100:
            savings_score = 15
        else:
            savings_score = 10
        
        # Ease of implementation score
        easy_count = len([opp for opp in opportunities if opp['difficulty'] == 'easy'])
        ease_score = min(20, easy_count * 5)
        
        return min(100, opportunity_score + savings_score + ease_score)
    
    def get_optimization_summary(self, optimization_result: Dict[str, Any]) -> str:
        """Generate human-readable summary of optimization analysis"""
        
        if optimization_result.get('error'):
            return f"Optimization Error: {optimization_result.get('message')}"
        
        total_savings = optimization_result.get('total_annual_savings', 0)
        opportunity_count = len(optimization_result.get('optimization_opportunities', []))
        optimization_score = optimization_result.get('optimization_score', 0)
        
        quick_wins = len(optimization_result.get('categorized_opportunities', {}).get('quick_wins', []))
        
        summary_parts = []
        
        if total_savings > 0:
            summary_parts.append(f"Found {opportunity_count} optimization opportunities for ${total_savings:.0f} annual savings.")
        else:
            summary_parts.append("Your energy usage is already well optimized.")
        
        if quick_wins > 0:
            summary_parts.append(f"{quick_wins} quick wins available for immediate implementation.")
        
        summary_parts.append(f"Optimization potential score: {optimization_score}/100.")
        
        return " ".join(summary_parts)
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response when optimization fails"""
        return {
            'error': True,
            'message': f'Usage optimization failed: {error_message}',
            'analysis_timestamp': datetime.now().isoformat(),
            'optimization_opportunities': [],
            'total_annual_savings': 0,
            'suggestions': [
                'Please ensure bill analysis data is available',
                'Try again with valid usage information'
            ]
        }


# Utility function for easy testing
def optimize_usage_for_bill(bill_analysis: Dict[str, Any], preferences: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to optimize usage for a bill analysis
    
    Args:
        bill_analysis: Analysis from BillAnalyzerAgent
        preferences: User preferences and constraints
        
    Returns:
        Complete usage optimization results
    """
    optimizer = UsageOptimizerAgent()
    return optimizer.optimize_energy_usage(bill_analysis, preferences)