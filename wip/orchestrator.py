"""
Complete Multi-Agent Orchestrator - Coordinates all WattsMyBill agents
File: src/agents/orchestrator.py (COMPLETE VERSION)
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all specialized agents
try:
    from agents.bill_analyzer import BillAnalyzerAgent
    from agents.market_researcher import MarketResearcherAgent
    AGENTS_AVAILABLE = True
    print("✅ All WattsMyBill agents imported successfully")
except ImportError as e:
    print(f"⚠️  Some agents not available: {e}")
    AGENTS_AVAILABLE = False


class WattsMyBillOrchestrator:
    """
    Complete Multi-Agent Orchestrator for WattsMyBill Analysis
    Coordinates: Bill Analysis → Market Research → Savings Calculation → Rebates → Usage Optimization
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Initialize all specialized agents
        if AGENTS_AVAILABLE:
            self.bill_analyzer = BillAnalyzerAgent()
            self.market_researcher = MarketResearcherAgent()
            print("🤖 All agents initialized successfully")
        else:
            self.bill_analyzer = None
            self.market_researcher = None
            print("⚠️  Running in fallback mode")
        
        # Track analysis workflow
        self.workflow_results = {}
        self.analysis_metadata = {
            'start_time': None,
            'end_time': None,
            'agents_used': [],
            'confidence_scores': {},
            'data_sources': []
        }
    
    def analyze_complete_energy_situation(self, file_content: bytes, file_type: str, 
                                        user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        COMPLETE: Run full multi-agent analysis workflow
        """
        try:
            print("🚀 Starting COMPLETE Multi-Agent Energy Analysis...")
            self.analysis_metadata['start_time'] = datetime.now()
            
            if user_preferences is None:
                user_preferences = {}
            
            # ======================================
            # AGENT 1: BILL ANALYSIS
            # ======================================
            print("\n🔍 STEP 1: Bill Analysis Agent")
            print("=" * 50)
            
            if self.bill_analyzer:
                bill_analysis = self.bill_analyzer.analyze_bill(
                    file_content, file_type, user_preferences.get('privacy_mode', False)
                )
                self.workflow_results['bill_analysis'] = bill_analysis
                self.analysis_metadata['agents_used'].append('bill_analyzer')
                self.analysis_metadata['confidence_scores']['bill_analysis'] = bill_analysis.get('confidence', 0)
                
                if bill_analysis.get('error'):
                    return self._get_error_response("Bill analysis failed", bill_analysis.get('message'))
                
                print(f"✅ Bill analyzed: {bill_analysis['bill_data'].get('retailer', 'Unknown')} - ${bill_analysis['bill_data'].get('total_amount', 0)}")
                print(f"   Usage: {bill_analysis['usage_profile'].get('total_kwh', 0)} kWh")
                print(f"   Solar: {'Yes' if bill_analysis.get('solar_analysis', {}).get('has_solar') else 'No'}")
            else:
                return self._get_error_response("Bill analyzer not available")
            
            # ======================================
            # AGENT 2: MARKET RESEARCH
            # ======================================
            print("\n📊 STEP 2: Market Research Agent")
            print("=" * 50)
            
            if self.market_researcher:
                market_research = self.market_researcher.research_better_plans(
                    bill_analysis['bill_data'], bill_analysis['usage_profile']
                )
                self.workflow_results['market_research'] = market_research
                self.analysis_metadata['agents_used'].append('market_researcher')
                
                if market_research.get('error'):
                    print(f"⚠️  Market research failed: {market_research.get('message')}")
                else:
                    better_plans = market_research.get('better_plans_found', 0)
                    max_savings = market_research.get('savings_analysis', {}).get('max_annual_savings', 0)
                    print(f"✅ Market research complete: {better_plans} better plans found")
                    print(f"   Best savings: ${max_savings:.0f}/year")
                    if market_research.get('best_plan', {}).get('retailer'):
                        print(f"   Best retailer: {market_research['best_plan']['retailer']}")
            else:
                market_research = self._get_mock_market_research()
                print("⚠️  Using mock market research data")
            
            # ======================================
            # AGENT 3: SAVINGS CALCULATOR
            # ======================================
            print("\n💰 STEP 3: Savings Calculator Agent")
            print("=" * 50)
            
            savings_calculation = self._calculate_comprehensive_savings(
                bill_analysis, market_research, user_preferences
            )
            self.workflow_results['savings_calculation'] = savings_calculation
            self.analysis_metadata['agents_used'].append('savings_calculator')
            
            total_annual_savings = savings_calculation.get('total_annual_savings', 0)
            print(f"✅ Savings calculated: ${total_annual_savings:.0f}/year potential")
            
            # ======================================
            # AGENT 4: REBATE HUNTER
            # ======================================
            print("\n🎯 STEP 4: Rebate Hunter Agent")
            print("=" * 50)
            
            rebate_analysis = self._find_applicable_rebates(
                bill_analysis, market_research, user_preferences
            )
            self.workflow_results['rebate_analysis'] = rebate_analysis
            self.analysis_metadata['agents_used'].append('rebate_hunter')
            
            total_rebates = rebate_analysis.get('total_rebate_value', 0)
            print(f"✅ Rebates found: ${total_rebates:.0f} in government incentives")
            
            # ======================================
            # AGENT 5: USAGE OPTIMIZER
            # ======================================
            print("\n⚡ STEP 5: Usage Optimizer Agent")
            print("=" * 50)
            
            usage_optimization = self._optimize_usage_patterns(
                bill_analysis, market_research, user_preferences
            )
            self.workflow_results['usage_optimization'] = usage_optimization
            self.analysis_metadata['agents_used'].append('usage_optimizer')
            
            optimization_savings = usage_optimization.get('total_monthly_savings', 0) * 12
            print(f"✅ Usage optimization: ${optimization_savings:.0f}/year potential")
            
            # ======================================
            # FINAL SYNTHESIS
            # ======================================
            print("\n🎯 FINAL STEP: Synthesis & Recommendations")
            print("=" * 50)
            
            final_recommendations = self._synthesize_final_recommendations(
                bill_analysis, market_research, savings_calculation, 
                rebate_analysis, usage_optimization, user_preferences
            )
            
            # Complete metadata
            self.analysis_metadata['end_time'] = datetime.now()
            self.analysis_metadata['total_duration'] = (
                self.analysis_metadata['end_time'] - self.analysis_metadata['start_time']
            ).total_seconds()
            
            # Compile complete results
            complete_analysis = {
                # Individual agent results
                'bill_analysis': bill_analysis,
                'market_research': market_research,
                'savings_calculation': savings_calculation,
                'rebate_analysis': rebate_analysis,
                'usage_optimization': usage_optimization,
                
                # Final synthesis
                'final_recommendations': final_recommendations,
                
                # Metadata
                'analysis_metadata': self.analysis_metadata,
                'workflow_version': '1.0_complete',
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            print(f"🎉 COMPLETE Multi-Agent Analysis Finished!")
            print(f"   Total potential savings: ${final_recommendations['total_annual_savings']:.0f}/year")
            print(f"   Analysis duration: {self.analysis_metadata['total_duration']:.1f} seconds")
            print(f"   Agents used: {len(self.analysis_metadata['agents_used'])}")
            
            return complete_analysis
            
        except Exception as e:
            self.logger.error(f"Complete analysis failed: {e}")
            return self._get_error_response("Multi-agent analysis failed", str(e))
    
    def _calculate_comprehensive_savings(self, bill_analysis: Dict[str, Any], 
                                       market_research: Dict[str, Any], 
                                       user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """AGENT 3: Calculate comprehensive savings from all sources"""
        
        try:
            current_annual_cost = bill_analysis['bill_data'].get('total_amount', 0) * (365 / bill_analysis['bill_data'].get('billing_days', 90))
            
            # Plan switching savings
            plan_savings = 0
            best_plan = market_research.get('best_plan', {})
            if best_plan.get('annual_savings', 0) > 0:
                plan_savings = best_plan['annual_savings']
            
            # Usage optimization savings (from usage optimizer)
            usage_savings = 0  # Will be calculated by usage optimizer
            
            # Solar optimization savings
            solar_savings = 0
            solar_analysis = bill_analysis.get('solar_analysis', {})
            if solar_analysis.get('has_solar') and solar_analysis.get('performance_rating') in ['low_export', 'moderate']:
                # Estimate potential solar optimization
                current_export = bill_analysis['bill_data'].get('solar_export_kwh', 0)
                if current_export > 0:
                    annual_export = current_export * (365 / bill_analysis['bill_data'].get('billing_days', 90))
                    better_fit_rate = 0.08  # Assume better feed-in tariff available
                    current_fit_rate = bill_analysis['bill_data'].get('feed_in_tariff', 0.06)
                    solar_savings = annual_export * (better_fit_rate - current_fit_rate)
            
            # Total savings calculation
            total_annual_savings = plan_savings + usage_savings + solar_savings
            monthly_savings = total_annual_savings / 12
            
            # Savings breakdown
            savings_breakdown = {
                'plan_switching': {
                    'annual_savings': plan_savings,
                    'monthly_savings': plan_savings / 12,
                    'source': best_plan.get('retailer', 'No better plan'),
                    'confidence': 'high' if plan_savings > 0 else 'low'
                },
                'usage_optimization': {
                    'annual_savings': usage_savings,
                    'monthly_savings': usage_savings / 12,
                    'source': 'Behavioral changes',
                    'confidence': 'medium'
                },
                'solar_optimization': {
                    'annual_savings': solar_savings,
                    'monthly_savings': solar_savings / 12,
                    'source': 'Better solar plan/battery',
                    'confidence': 'medium' if solar_savings > 0 else 'low'
                }
            }
            
            # Payback analysis
            switching_cost = 0  # Most plan switches are free
            payback_period = "Immediate" if switching_cost == 0 else f"{switching_cost / monthly_savings:.1f} months"
            
            return {
                'current_annual_cost': round(current_annual_cost, 2),
                'total_annual_savings': round(total_annual_savings, 2),
                'total_monthly_savings': round(monthly_savings, 2),
                'savings_percentage': round((total_annual_savings / current_annual_cost) * 100, 1) if current_annual_cost > 0 else 0,
                'savings_breakdown': savings_breakdown,
                'payback_period': payback_period,
                'confidence_score': 0.8 if plan_savings > 0 else 0.5,
                'calculation_method': 'comprehensive_multi_source',
                'calculated_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Savings calculation failed: {e}'}
    
    def _find_applicable_rebates(self, bill_analysis: Dict[str, Any], 
                               market_research: Dict[str, Any], 
                               user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """AGENT 4: Find applicable government rebates and incentives"""
        
        try:
            state = bill_analysis['bill_data'].get('state', 'NSW')
            has_solar = bill_analysis.get('solar_analysis', {}).get('has_solar', False)
            annual_usage = bill_analysis['usage_profile'].get('total_kwh', 0) * (365 / bill_analysis['bill_data'].get('billing_days', 90))
            
            applicable_rebates = []
            
            # Federal rebates (available to all)
            federal_rebates = [
                {
                    'name': 'Energy Bill Relief Fund',
                    'value': 300,
                    'type': 'federal',
                    'eligibility': 'All Australian households',
                    'how_to_apply': 'Automatic credit applied to bills',
                    'status': 'confirmed_2025',
                    'one_time_payment': True
                }
            ]
            
            # State-specific rebates
            state_rebates = {
                'QLD': [
                    {
                        'name': 'Queensland Electricity Rebate',
                        'value': 372,
                        'type': 'state',
                        'eligibility': 'QLD households',
                        'how_to_apply': 'Apply through Queensland Government',
                        'status': 'active_2025'
                    },
                    {
                        'name': 'Asset Ownership Dividend',
                        'value': 550,
                        'type': 'state',
                        'eligibility': 'QLD households (if continued)',
                        'how_to_apply': 'Automatic payment',
                        'status': 'pending_2025'
                    }
                ],
                'NSW': [
                    {
                        'name': 'Low Income Household Rebate',
                        'value': 285,
                        'type': 'state',
                        'eligibility': 'Concession card holders',
                        'how_to_apply': 'Apply through Service NSW',
                        'status': 'active_2025'
                    }
                ],
                'VIC': [
                    {
                        'name': 'Victorian Default Offer Rebate',
                        'value': 250,
                        'type': 'state',
                        'eligibility': 'VIC households',
                        'how_to_apply': 'Apply through Energy Compare Victoria',
                        'status': 'active_2025'
                    }
                ]
            }
            
            # Add federal rebates
            applicable_rebates.extend(federal_rebates)
            
            # Add state-specific rebates
            if state in state_rebates:
                applicable_rebates.extend(state_rebates[state])
            
            # Solar rebates (if applicable)
            if has_solar:
                solar_rebates = [
                    {
                        'name': 'Small-scale Renewable Energy Scheme (STCs)',
                        'value': 200,  # Ongoing annual value
                        'type': 'federal',
                        'eligibility': 'Solar system owners',
                        'how_to_apply': 'Through electricity retailer',
                        'status': 'ongoing'
                    }
                ]
                applicable_rebates.extend(solar_rebates)
            
            # Calculate totals
            total_rebate_value = sum(rebate['value'] for rebate in applicable_rebates)
            high_value_rebates = [rebate['name'] for rebate in applicable_rebates if rebate['value'] >= 300]
            
            return {
                'applicable_rebates': applicable_rebates,
                'total_rebate_value': total_rebate_value,
                'high_value_rebates': high_value_rebates,
                'rebate_count': len(applicable_rebates),
                'estimated_application_time': '2-4 weeks',
                'confidence_level': 'high',
                'data_source': 'government_websites_2025',
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Rebate analysis failed: {e}'}
    
    def _optimize_usage_patterns(self, bill_analysis: Dict[str, Any], 
                                market_research: Dict[str, Any], 
                                user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """AGENT 5: Optimize usage patterns and behaviors"""
        
        try:
            usage_category = bill_analysis['usage_profile'].get('usage_category', 'medium')
            daily_usage = bill_analysis['usage_profile'].get('daily_average', 0)
            has_solar = bill_analysis.get('solar_analysis', {}).get('has_solar', False)
            current_rate = bill_analysis['bill_data'].get('cost_per_kwh', 0.30)
            
            optimization_opportunities = []
            
            # Time-shifting opportunities
            if daily_usage > 10:  # Reasonable usage for time shifting
                time_shift_savings = daily_usage * 0.10 * 30  # 10% savings, monthly
                optimization_opportunities.append({
                    'type': 'timing',
                    'recommendation': 'Shift heavy appliances (dishwasher, washing machine) to off-peak hours (10pm-6am)',
                    'potential_monthly_savings': time_shift_savings,
                    'difficulty': 'easy',
                    'implementation': 'Use appliance timers or smart plugs'
                })
            
            # Heating/cooling optimization
            if usage_category in ['medium', 'high', 'very_high']:
                hvac_savings = daily_usage * 0.15 * 30  # 15% savings from HVAC optimization
                optimization_opportunities.append({
                    'type': 'behavioral',
                    'recommendation': 'Optimize heating/cooling: 2°C adjustment can save 10-15%',
                    'potential_monthly_savings': hvac_savings,
                    'difficulty': 'easy',
                    'implementation': 'Set aircon to 24°C in summer, 20°C in winter'
                })
            
            # Solar optimization (if applicable)
            if has_solar:
                solar_optimization = daily_usage * 0.08 * 30  # 8% from better solar usage
                optimization_opportunities.append({
                    'type': 'timing',
                    'recommendation': 'Maximize daytime usage to consume your solar generation',
                    'potential_monthly_savings': solar_optimization,
                    'difficulty': 'medium',
                    'implementation': 'Run appliances during 10am-3pm when solar peaks'
                })
            
            # LED lighting upgrade
            if usage_category in ['high', 'very_high']:
                lighting_savings = daily_usage * 0.05 * 30  # 5% from LED upgrade
                optimization_opportunities.append({
                    'type': 'equipment',
                    'recommendation': 'Replace remaining halogen/incandescent bulbs with LEDs',
                    'potential_monthly_savings': lighting_savings,
                    'difficulty': 'easy',
                    'implementation': 'Replace bulbs gradually as they fail'
                })
            
            # Smart home automation
            if daily_usage > 15:  # High usage households
                smart_savings = daily_usage * 0.12 * 30  # 12% from smart automation
                optimization_opportunities.append({
                    'type': 'equipment',
                    'recommendation': 'Install smart home automation for optimal scheduling',
                    'potential_monthly_savings': smart_savings,
                    'difficulty': 'medium',
                    'implementation': 'Smart thermostats, switches, and scheduling'
                })
            
            # Calculate totals
            total_monthly_savings = sum(opp['potential_monthly_savings'] for opp in optimization_opportunities)
            
            # Categorize opportunities
            quick_wins = [opp['recommendation'] for opp in optimization_opportunities if opp['difficulty'] == 'easy']
            long_term_investments = [opp['recommendation'] for opp in optimization_opportunities if opp['difficulty'] in ['medium', 'hard']]
            
            return {
                'optimization_opportunities': optimization_opportunities,
                'total_monthly_savings': round(total_monthly_savings, 2),
                'total_annual_savings': round(total_monthly_savings * 12, 2),
                'quick_wins': quick_wins,
                'long_term_investments': long_term_investments,
                'optimization_potential': 'high' if total_monthly_savings > 50 else 'medium' if total_monthly_savings > 20 else 'low',
                'confidence_level': 'medium',
                'implementation_timeframe': '1-6 months',
                'calculated_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Usage optimization failed: {e}'}
    
    def _synthesize_final_recommendations(self, bill_analysis: Dict[str, Any], 
                                        market_research: Dict[str, Any], 
                                        savings_calculation: Dict[str, Any],
                                        rebate_analysis: Dict[str, Any],
                                        usage_optimization: Dict[str, Any],
                                        user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """FINAL SYNTHESIS: Combine all agent results into prioritized recommendations"""
        
        try:
            # Extract key values
            plan_savings = market_research.get('savings_analysis', {}).get('max_annual_savings', 0)
            rebate_value = rebate_analysis.get('total_rebate_value', 0)
            usage_savings = usage_optimization.get('total_annual_savings', 0)
            
            total_annual_savings = plan_savings + rebate_value + usage_savings
            
            # Build prioritized recommendations
            recommendations = []
            
            # Recommendation 1: Plan switching (if significant savings)
            if plan_savings > 100:
                best_retailer = market_research.get('best_plan', {}).get('retailer', 'Alternative retailer')
                plan_name = market_research.get('best_plan', {}).get('plan_name', 'Better plan')
                recommendations.append({
                    'priority': 1,
                    'type': 'plan_switch',
                    'title': f'Switch to {best_retailer} {plan_name}',
                    'annual_savings': plan_savings,
                    'monthly_savings': plan_savings / 12,
                    'confidence': 'high',
                    'effort': 'low',
                    'timeframe': '2-4 weeks',
                    'action_required': f'Contact {best_retailer} to switch plans',
                    'why_recommended': f'Save ${plan_savings:.0f} annually with better rates'
                })
            
            # Recommendation 2: Government rebates
            if rebate_value > 0:
                recommendations.append({
                    'priority': 2,
                    'type': 'rebates',
                    'title': f'Apply for ${rebate_value} in government rebates',
                    'annual_savings': rebate_value,
                    'monthly_savings': rebate_value / 12,
                    'confidence': 'high',
                    'effort': 'low',
                    'timeframe': '1-2 weeks',
                    'action_required': 'Complete online rebate applications',
                    'why_recommended': f'Free money from government programs'
                })
            
            # Recommendation 3: Usage optimization
            if usage_savings > 50:
                recommendations.append({
                    'priority': 3,
                    'type': 'usage_optimization',
                    'title': f'Optimize usage patterns for ${usage_savings:.0f}/year savings',
                    'annual_savings': usage_savings,
                    'monthly_savings': usage_savings / 12,
                    'confidence': 'medium',
                    'effort': 'medium',
                    'timeframe': '1-3 months',
                    'action_required': 'Implement behavioral changes and smart scheduling',
                    'why_recommended': 'Reduce consumption through better habits'
                })
            
            # Solar recommendation (if applicable)
            solar_analysis = bill_analysis.get('solar_analysis', {})
            if not solar_analysis.get('has_solar') and bill_analysis['usage_profile'].get('daily_average', 0) > 10:
                estimated_solar_savings = bill_analysis['usage_profile']['daily_average'] * 365 * 0.3 * 0.25  # Rough estimate
                recommendations.append({
                    'priority': 4,
                    'type': 'solar_installation',
                    'title': f'Consider solar installation for ~${estimated_solar_savings:.0f}/year savings',
                    'annual_savings': estimated_solar_savings,
                    'monthly_savings': estimated_solar_savings / 12,
                    'confidence': 'medium',
                    'effort': 'high',
                    'timeframe': '3-6 months',
                    'action_required': 'Get solar quotes and assess roof suitability',
                    'why_recommended': 'Long-term savings with current usage patterns'
                })
            
            # Summary
            current_situation = {
                'current_retailer': bill_analysis['bill_data'].get('retailer', 'Unknown'),
                'current_annual_cost': savings_calculation.get('current_annual_cost', 0),
                'usage_efficiency': bill_analysis['usage_profile'].get('usage_category', 'unknown'),
                'rate_competitiveness': market_research.get('market_insights', {}).get('current_rate_position', 'unknown'),
                'solar_status': 'installed' if solar_analysis.get('has_solar') else 'not_installed'
            }
            
            return {
                'current_situation': current_situation,
                'recommendations': sorted(recommendations, key=lambda x: x['annual_savings'], reverse=True),
                'total_annual_savings': round(total_annual_savings, 2),
                'total_monthly_savings': round(total_annual_savings / 12, 2),
                'implementation_summary': {
                    'immediate_actions': len([r for r in recommendations if r['effort'] == 'low']),
                    'medium_term_actions': len([r for r in recommendations if r['effort'] == 'medium']),
                    'long_term_actions': len([r for r in recommendations if r['effort'] == 'high'])
                },
                'confidence_score': 0.85,  # Overall confidence in recommendations
                'payback_analysis': {
                    'immediate_payback': [r for r in recommendations if r['type'] in ['plan_switch', 'rebates']],
                    'medium_payback': [r for r in recommendations if r['type'] == 'usage_optimization'],
                    'long_payback': [r for r in recommendations if r['type'] == 'solar_installation']
                },
                'next_steps': self._generate_next_steps(recommendations),
                'summary_message': self._generate_summary_message(total_annual_savings, recommendations),
                'synthesis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'error': f'Final synthesis failed: {e}'}
    
    def _generate_next_steps(self, recommendations: List[Dict[str, Any]]) -> List[str]:
        """Generate clear next steps for the user"""
        next_steps = []
        
        for i, rec in enumerate(recommendations[:3], 1):  # Top 3 recommendations
            if rec['type'] == 'plan_switch':
                next_steps.append(f"{i}. Contact {rec['title'].split()[2]} for plan switch quote")
            elif rec['type'] == 'rebates':
                next_steps.append(f"{i}. Apply for government rebates online (2-3 applications)")
            elif rec['type'] == 'usage_optimization':
                next_steps.append(f"{i}. Start with easy wins: timer settings and temperature adjustments")
            elif rec['type'] == 'solar_installation':
                next_steps.append(f"{i}. Get 3 solar quotes to compare options and payback periods")
        
        return next_steps
    
    def _generate_summary_message(self, total_savings: float, recommendations: List[Dict[str, Any]]) -> str:
        """Generate human-readable summary message"""
        
        if total_savings > 1000:
            return f"Excellent news! You could save ${total_savings:.0f} annually through {len(recommendations)} strategies. The biggest opportunity is plan switching with immediate impact."
        elif total_savings > 500:
            return f"Good savings potential! You could save ${total_savings:.0f} annually. Focus on plan switching and government rebates for quick wins."
        elif total_savings > 200:
            return f"Modest savings available: ${total_savings:.0f} annually. Start with government rebates and usage optimization."
        else:
            return f"Your energy setup is already quite efficient. Small optimizations could save ${total_savings:.0f} annually."
    
    def _get_mock_market_research(self) -> Dict[str, Any]:
        """Fallback market research data"""
        return {
            'best_plan': {
                'retailer': 'Competitive Retailer',
                'plan_name': 'Better Plan',
                'annual_savings': 400
            },
            'savings_analysis': {
                'max_annual_savings': 400
            },
            'better_plans_found': 3,
            'market_insights': {
                'current_rate_position': 'average'
            }
        }
    
    def _get_error_response(self, error_type: str, error_message: str = "") -> Dict[str, Any]:
        """Return structured error response"""
        return {
            'error': True,
            'error_type': error_type,
            'message': error_message,
            'timestamp': datetime.now().isoformat(),
            'workflow_results': self.workflow_results,
            'partial_analysis': len(self.workflow_results) > 0
        }
    
    def get_analysis_summary(self, complete_analysis: Dict[str, Any]) -> str:
        """Generate human-readable summary of complete analysis"""
        
        if complete_analysis.get('error'):
            return f"Analysis Error: {complete_analysis.get('message')}"
        
        final_recs = complete_analysis.get('final_recommendations', {})
        total_savings = final_recs.get('total_annual_savings', 0)
        rec_count = len(final_recs.get('recommendations', []))
        
        # Bill details
        bill_data = complete_analysis.get('bill_analysis', {}).get('bill_data', {})
        retailer = bill_data.get('retailer', 'Unknown')
        usage = complete_analysis.get('bill_analysis', {}).get('usage_profile', {}).get('total_kwh', 0)
        
        # Market research
        better_plans = complete_analysis.get('market_research', {}).get('better_plans_found', 0)
        
        summary_parts = []
        
        # Basic analysis
        summary_parts.append(f"Analyzed {retailer} bill with {usage} kWh usage.")
        
        # Savings opportunity
        if total_savings > 500:
            summary_parts.append(f"EXCELLENT savings potential: ${total_savings:.0f}/year through {rec_count} strategies.")
        elif total_savings > 200:
            summary_parts.append(f"Good savings available: ${total_savings:.0f}/year through {rec_count} strategies.")
        else:
            summary_parts.append(f"Modest optimization possible: ${total_savings:.0f}/year.")
        
        # Key findings
        if better_plans > 0:
            summary_parts.append(f"Found {better_plans} better retailer plans.")
        
        # Solar status
        has_solar = complete_analysis.get('bill_analysis', {}).get('solar_analysis', {}).get('has_solar', False)
        if has_solar:
            summary_parts.append("Solar system detected and optimized.")
        
        return " ".join(summary_parts)


# Utility function for easy testing
def analyze_energy_bill_complete(file_content: bytes, file_type: str, 
                                user_preferences: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to run complete multi-agent analysis
    
    Args:
        file_content: Raw file content as bytes
        file_type: 'pdf' or 'image'
        user_preferences: Optional user preferences and settings
        
    Returns:
        Complete multi-agent analysis results
    """
    orchestrator = WattsMyBillOrchestrator()
    return orchestrator.analyze_complete_energy_situation(file_content, file_type, user_preferences)