"""
Fixed Bill Analyzer Agent - Solar detection and cost benchmark improvements
File: src/agents/bill_analyzer.py (UPDATED)
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.bill_parser import AustralianBillParser


class BillAnalyzerAgent:
    """
    Specialized agent for analyzing Australian energy bills
    Uses the bill parser and adds intelligence layer for insights
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parser = AustralianBillParser()
        
        # Australian household usage benchmarks (kWh per day)
        self.usage_benchmarks = {
            'NSW': {'low': 7.5, 'medium': 15.0, 'high': 25.0},
            'VIC': {'low': 7.0, 'medium': 14.0, 'high': 23.0},
            'QLD': {'low': 8.0, 'medium': 16.0, 'high': 27.0},
            'SA': {'low': 6.5, 'medium': 13.0, 'high': 22.0},
            'WA': {'low': 8.5, 'medium': 17.0, 'high': 28.0},
            'TAS': {'low': 6.0, 'medium': 12.0, 'high': 20.0},
            'NT': {'low': 9.0, 'medium': 18.0, 'high': 30.0},
            'ACT': {'low': 7.0, 'medium': 14.0, 'high': 24.0},
        }
        
        # FIXED: Updated Australian electricity cost benchmarks ($ per kWh) - 2024 market rates
        self.cost_benchmarks = {
            'excellent': 0.22,    # Very competitive rate (solar, competitive plans)
            'good': 0.28,         # Good competitive rate
            'average': 0.32,      # Market average 2024
            'poor': 0.38,         # Above average
            'very_poor': 0.45     # High rate (default tariffs, poor plans)
        }
        
        print(f"💡 Cost Benchmarks: Excellent ≤${self.cost_benchmarks['excellent']:.3f}, "
              f"Good ≤${self.cost_benchmarks['good']:.3f}, "
              f"Average ≤${self.cost_benchmarks['average']:.3f}, "
              f"Poor ≤${self.cost_benchmarks['poor']:.3f}, "
              f"Very Poor >${self.cost_benchmarks['poor']:.3f}")
    
    def analyze_bill(self, file_content: bytes, file_type: str, privacy_mode: bool = False) -> Dict[str, Any]:
        """Main analysis method - parses bill and provides intelligent insights"""
        try:
            # Step 1: Parse the bill using our working parser
            print("🔍 Parsing energy bill...")
            parsed_data = self.parser.parse_bill(file_content, file_type, privacy_mode)
            
            if parsed_data.get('extraction_method') == 'fallback':
                print("⚠️  Parser used fallback data - analysis may be limited")
            
            # FIXED: Debug solar detection
            print(f"🐛 DEBUG Solar Detection:")
            print(f"   has_solar (parser): {parsed_data.get('has_solar')}")
            print(f"   solar_export_kwh: {parsed_data.get('solar_export_kwh')}")
            print(f"   solar_credit_amount: {parsed_data.get('solar_credit_amount')}")
            print(f"   feed_in_tariff: {parsed_data.get('feed_in_tariff')}")
            
            # Step 2: Analyze usage patterns
            print("📊 Analyzing usage patterns...")
            usage_analysis = self._analyze_usage_patterns(parsed_data)
            
            # Step 3: Analyze costs and efficiency
            print("💰 Analyzing costs and efficiency...")
            cost_analysis = self._analyze_costs(parsed_data)
            
            # Step 4: Solar analysis (if applicable)
            print("☀️ Checking for solar system...")
            solar_analysis = self._analyze_solar_system(parsed_data)
            
            # Step 5: Generate recommendations
            print("💡 Generating recommendations...")
            recommendations = self._generate_recommendations(parsed_data, usage_analysis, cost_analysis, solar_analysis)
            
            # Step 6: Calculate efficiency score
            efficiency_score = self._calculate_efficiency_score(usage_analysis, cost_analysis, solar_analysis)
            
            # Compile final analysis
            analysis_result = {
                # Core bill data
                'bill_data': parsed_data,
                
                # Analysis results
                'usage_profile': {
                    'total_kwh': parsed_data.get('usage_kwh'),
                    'billing_days': parsed_data.get('billing_days'),
                    'daily_average': parsed_data.get('daily_average_kwh'),
                    'usage_category': usage_analysis.get('category'),
                    'usage_percentile': usage_analysis.get('percentile'),
                    'comparison_to_average': usage_analysis.get('comparison')
                },
                
                'cost_breakdown': {
                    'total_cost': parsed_data.get('total_amount'),
                    'cost_per_kwh': parsed_data.get('cost_per_kwh'),
                    'supply_charge': parsed_data.get('supply_charge'),
                    'usage_charge': parsed_data.get('usage_charge'),
                    'cost_rating': cost_analysis.get('rating'),
                    'cost_comparison': cost_analysis.get('comparison')
                },
                
                'solar_analysis': solar_analysis,
                
                'efficiency_score': efficiency_score,
                
                'recommendations': recommendations,
                
                # Metadata
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.1',  # Updated version
                'confidence': parsed_data.get('confidence', 0.0)
            }
            
            print("✅ Bill analysis completed successfully!")
            return analysis_result
            
        except Exception as e:
            self.logger.error(f"Bill analysis failed: {e}")
            return self._get_error_response(str(e))
    
    def _analyze_usage_patterns(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze usage patterns and compare to benchmarks"""
        
        usage_kwh = bill_data.get('usage_kwh')
        billing_days = bill_data.get('billing_days')
        state = bill_data.get('state', 'NSW')
        daily_usage = bill_data.get('daily_average_kwh')
        
        if not usage_kwh or not billing_days:
            return {'error': 'Insufficient usage data'}
        
        # Get benchmarks for this state
        benchmarks = self.usage_benchmarks.get(state, self.usage_benchmarks['NSW'])
        
        # Categorize usage
        if daily_usage <= benchmarks['low']:
            category = 'low'
            percentile = 25
            comparison = f"Your usage is {benchmarks['low'] - daily_usage:.1f} kWh/day below average"
        elif daily_usage <= benchmarks['medium']:
            category = 'medium'
            percentile = 50
            comparison = "Your usage is around the state average"
        elif daily_usage <= benchmarks['high']:
            category = 'high'
            percentile = 75
            comparison = f"Your usage is {daily_usage - benchmarks['medium']:.1f} kWh/day above average"
        else:
            category = 'very_high'
            percentile = 90
            comparison = f"Your usage is {daily_usage - benchmarks['high']:.1f} kWh/day well above average"
        
        # Seasonal adjustment (basic)
        seasonal_note = self._get_seasonal_note(bill_data.get('billing_period'))
        
        return {
            'category': category,
            'percentile': percentile,
            'comparison': comparison,
            'daily_usage': daily_usage,
            'state_benchmarks': benchmarks,
            'seasonal_note': seasonal_note,
            'annual_projection': int(usage_kwh * (365 / billing_days)) if billing_days else None
        }
    
    def _analyze_costs(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """FIXED: Analyze cost efficiency with updated benchmarks and better validation"""
        
        cost_per_kwh = bill_data.get('cost_per_kwh')
        total_amount = bill_data.get('total_amount')
        supply_charge = bill_data.get('supply_charge')
        usage_charge = bill_data.get('usage_charge')
        usage_kwh = bill_data.get('usage_kwh')
        
        if not cost_per_kwh:
            return {'error': 'Insufficient cost data'}
        
        # FIXED: Validate cost_per_kwh - if it's unreasonably high, recalculate
        if cost_per_kwh > 1.0:  # More than $1/kWh is likely an error
            print(f"⚠️  WARNING: Cost per kWh seems too high: ${cost_per_kwh:.3f}")
            print(f"   Total: ${total_amount}, Usage: {usage_kwh} kWh")
            
            # Try to recalculate with usage charge only (excluding supply charge)
            if usage_charge and usage_kwh:
                recalculated_rate = usage_charge / usage_kwh
                print(f"   Recalculated rate (usage only): ${recalculated_rate:.3f}/kWh")
                if 0.15 <= recalculated_rate <= 0.60:  # Reasonable range
                    cost_per_kwh = recalculated_rate
                    print(f"   Using recalculated rate: ${cost_per_kwh:.3f}/kWh")
        
        # Rate the cost per kWh with updated benchmarks
        if cost_per_kwh <= self.cost_benchmarks['excellent']:
            rating = 'excellent'
            comparison = "You have an excellent electricity rate!"
        elif cost_per_kwh <= self.cost_benchmarks['good']:
            rating = 'good'
            comparison = "You have a good electricity rate"
        elif cost_per_kwh <= self.cost_benchmarks['average']:
            rating = 'average'
            comparison = "Your rate is around market average"
        elif cost_per_kwh <= self.cost_benchmarks['poor']:
            rating = 'poor'
            comparison = "Your rate is above market average"
        else:
            rating = 'very_poor'
            comparison = "Your rate is significantly above market average"
        
        # Calculate potential savings
        good_rate = self.cost_benchmarks['good']
        potential_savings_per_kwh = max(0, cost_per_kwh - good_rate)
        
        # Calculate cost breakdown percentages
        if total_amount and supply_charge and usage_charge:
            supply_percentage = (supply_charge / total_amount) * 100
            usage_percentage = (usage_charge / total_amount) * 100
        else:
            supply_percentage = None
            usage_percentage = None
        
        # Annual cost projection
        billing_days = bill_data.get('billing_days')
        annual_cost = int(total_amount * (365 / billing_days)) if billing_days and total_amount else None
        
        return {
            'rating': rating,
            'comparison': comparison,
            'cost_per_kwh': cost_per_kwh,
            'market_benchmark': self.cost_benchmarks['average'],
            'potential_savings_per_kwh': potential_savings_per_kwh,
            'cost_breakdown': {
                'supply_percentage': supply_percentage,
                'usage_percentage': usage_percentage
            },
            'annual_projection': annual_cost
        }
    
    def _analyze_solar_system(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """FIXED: Analyze solar system with improved detection logic"""
        
        # IMPROVED: Check multiple indicators for solar presence
        solar_export = bill_data.get('solar_export_kwh', 0)
        solar_credit = bill_data.get('solar_credit_amount', 0)
        feed_in_tariff = bill_data.get('feed_in_tariff', 0)
        
        # FIXED: Better solar detection logic
        has_solar = bool(solar_export or solar_credit or feed_in_tariff)
        
        # Additional check: sometimes parser flag is wrong, trust the data
        parser_says_solar = bill_data.get('has_solar', False)
        
        print(f"🐛 Solar Detection Logic:")
        print(f"   Solar export: {solar_export} kWh")
        print(f"   Solar credit: ${solar_credit}")
        print(f"   Feed-in tariff: ${feed_in_tariff}/kWh")
        print(f"   Parser flag: {parser_says_solar}")
        print(f"   Final decision: {has_solar}")
        
        if not has_solar:
            return {
                'has_solar': False,
                'recommendation': 'Consider installing solar panels to reduce your electricity costs'
            }
        
        # Solar system analysis
        usage_kwh = bill_data.get('usage_kwh', 0)
        billing_days = bill_data.get('billing_days', 90)
        
        # Calculate solar metrics
        if solar_export and usage_kwh:
            export_ratio = (solar_export / usage_kwh) * 100
            self_consumption_estimate = max(0, usage_kwh - solar_export)
        else:
            export_ratio = 0
            self_consumption_estimate = usage_kwh
        
        # Daily solar generation estimate
        daily_solar_export = solar_export / billing_days if billing_days else 0
        
        # Annual solar savings projection
        annual_solar_savings = solar_credit * (365 / billing_days) if billing_days else 0
        
        # IMPROVED: Solar performance assessment with better categories
        if export_ratio > 80:
            performance = 'excellent'
            performance_note = 'Your solar system generates significantly more than you use - consider a battery'
        elif export_ratio > 50:
            performance = 'very_good'
            performance_note = 'Your solar system is performing very well'
        elif export_ratio > 20:
            performance = 'good'
            performance_note = 'Your solar system provides good savings'
        elif export_ratio > 5:
            performance = 'moderate'
            performance_note = 'Your solar system provides some savings'
        elif solar_credit > 0:  # Has solar but low export
            performance = 'low_export'
            performance_note = 'You have solar but most generation is self-consumed'
        else:
            performance = 'unknown'
            performance_note = 'Solar performance data not clear'
        
        return {
            'has_solar': True,
            'solar_export_kwh': solar_export,
            'solar_credit_amount': solar_credit,
            'feed_in_tariff': feed_in_tariff,
            'export_ratio_percent': round(export_ratio, 1),
            'daily_export_average': round(daily_solar_export, 1),
            'annual_savings_projection': round(annual_solar_savings, 2),
            'performance_rating': performance,
            'performance_note': performance_note,
            'self_consumption_estimate': self_consumption_estimate,
            'battery_recommendation': export_ratio > 60  # Suggest battery if high export
        }
    
    def _generate_recommendations(self, bill_data: Dict[str, Any], usage_analysis: Dict[str, Any], 
                                cost_analysis: Dict[str, Any], solar_analysis: Dict[str, Any]) -> List[str]:
        """Generate personalized recommendations based on analysis"""
        
        recommendations = []
        
        # Usage-based recommendations
        usage_category = usage_analysis.get('category')
        if usage_category == 'very_high':
            recommendations.append(
                "Your electricity usage is well above average. Consider energy-efficient appliances "
                "and reducing usage during peak hours."
            )
        elif usage_category == 'high':
            recommendations.append(
                "Your usage is above average. Small changes like LED lighting and efficient appliances "
                "could reduce your bills."
            )
        elif usage_category == 'low':
            recommendations.append(
                "Great job! Your usage is below average. Focus on getting the best electricity rate."
            )
        
        # Cost-based recommendations with better calculation
        cost_rating = cost_analysis.get('rating')
        if cost_rating in ['poor', 'very_poor']:
            potential_savings_per_kwh = cost_analysis.get('potential_savings_per_kwh', 0)
            usage_kwh = bill_data.get('usage_kwh', 0)
            billing_days = bill_data.get('billing_days', 90)
            
            if potential_savings_per_kwh > 0 and usage_kwh > 0:
                annual_usage = usage_kwh * (365 / billing_days)
                annual_savings = potential_savings_per_kwh * annual_usage
                recommendations.append(
                    f"Your electricity rate is {cost_rating}. Shopping for a better plan could save you "
                    f"approximately ${annual_savings:.0f} per year."
                )
        elif cost_rating == 'average':
            recommendations.append(
                "Your rate is average. Compare plans to see if you can get a better deal."
            )
        
        # IMPROVED: Solar recommendations based on actual detection
        if not solar_analysis.get('has_solar'):
            daily_usage = usage_analysis.get('daily_usage', 0)
            if daily_usage > 10:  # Good candidate for solar
                recommendations.append(
                    "With your usage pattern, solar panels could significantly reduce your electricity costs. "
                    "Consider getting a solar quote."
                )
        else:
            # Solar system exists - provide optimization advice
            export_ratio = solar_analysis.get('export_ratio_percent', 0)
            if solar_analysis.get('battery_recommendation'):
                recommendations.append(
                    "Your solar system exports a lot of energy. Consider a battery system "
                    "to store excess solar for evening use and maximize your savings."
                )
            elif export_ratio < 20:
                recommendations.append(
                    "You're consuming most of your solar generation during the day. This is excellent! "
                    "Consider shifting more usage to daylight hours to maximize solar benefits."
                )
        
        # Tariff recommendations
        tariff_type = bill_data.get('tariff_type')
        if tariff_type == 'single_rate' and usage_analysis.get('daily_usage', 0) > 15:
            recommendations.append(
                "Consider a time-of-use tariff to potentially save money by using more electricity "
                "during off-peak hours."
            )
        
        # State-specific recommendations
        state = bill_data.get('state')
        if state == 'QLD' and not solar_analysis.get('has_solar'):
            recommendations.append(
                "Queensland has excellent solar conditions. Solar panels could significantly "
                "reduce your electricity costs."
            )
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _calculate_efficiency_score(self, usage_analysis: Dict[str, Any], cost_analysis: Dict[str, Any], 
                                  solar_analysis: Dict[str, Any]) -> float:
        """Calculate overall efficiency score out of 100"""
        
        score = 0
        
        # Usage efficiency (40 points max)
        usage_category = usage_analysis.get('category')
        if usage_category == 'low':
            score += 40
        elif usage_category == 'medium':
            score += 30
        elif usage_category == 'high':
            score += 20
        else:  # very_high
            score += 10
        
        # Cost efficiency (40 points max)
        cost_rating = cost_analysis.get('rating')
        if cost_rating == 'excellent':
            score += 40
        elif cost_rating == 'good':
            score += 32
        elif cost_rating == 'average':
            score += 24
        elif cost_rating == 'poor':
            score += 16
        else:  # very_poor
            score += 8
        
        # Solar bonus (20 points max)
        if solar_analysis.get('has_solar'):
            performance = solar_analysis.get('performance_rating')
            if performance == 'excellent':
                score += 20
            elif performance == 'very_good':
                score += 16
            elif performance == 'good':
                score += 12
            elif performance in ['moderate', 'low_export']:
                score += 8
            else:
                score += 4
        else:
            # No penalty for not having solar, but no bonus either
            pass
        
        return min(100, score)  # Cap at 100
    
    def _get_seasonal_note(self, billing_period: Optional[Dict[str, str]]) -> str:
        """Generate seasonal usage note"""
        if not billing_period:
            return "Consider seasonal usage patterns when comparing bills"
        
        # This is a simplified seasonal analysis
        return "Usage can vary significantly between seasons due to heating and cooling needs"
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response when analysis fails"""
        return {
            'error': True,
            'message': f'Bill analysis failed: {error_message}',
            'analysis_timestamp': datetime.now().isoformat(),
            'recommendations': [
                'Please ensure the bill file is readable and contains energy usage data',
                'Try uploading a clearer image or PDF of your electricity bill'
            ]
        }
    
    def get_analysis_summary(self, analysis_result: Dict[str, Any]) -> str:
        """Generate a human-readable summary of the analysis"""
        
        if analysis_result.get('error'):
            return f"Analysis Error: {analysis_result.get('message')}"
        
        usage_profile = analysis_result.get('usage_profile', {})
        cost_breakdown = analysis_result.get('cost_breakdown', {})
        solar_analysis = analysis_result.get('solar_analysis', {})
        efficiency_score = analysis_result.get('efficiency_score', 0)
        
        summary_parts = []
        
        # Usage summary
        daily_avg = usage_profile.get('daily_average')
        usage_category = usage_profile.get('usage_category')
        if daily_avg and usage_category:
            summary_parts.append(
                f"Your daily usage averages {daily_avg:.1f} kWh ({usage_category} usage category)."
            )
        
        # Cost summary
        cost_per_kwh = cost_breakdown.get('cost_per_kwh')
        cost_rating = cost_breakdown.get('cost_rating')
        if cost_per_kwh and cost_rating:
            summary_parts.append(
                f"Your rate of ${cost_per_kwh:.3f}/kWh is rated as {cost_rating}."
            )
        
        # Solar summary
        if solar_analysis.get('has_solar'):
            export_ratio = solar_analysis.get('export_ratio_percent', 0)
            summary_parts.append(
                f"Your solar system exports {export_ratio:.1f}% of your usage."
            )
        
        # Efficiency score
        summary_parts.append(f"Overall efficiency score: {efficiency_score:.0f}/100.")
        
        return " ".join(summary_parts)


# Utility function for easy testing
def analyze_bill_file(file_path: str, privacy_mode: bool = False) -> Dict[str, Any]:
    """
    Convenience function to analyze a bill file
    
    Args:
        file_path: Path to the bill file
        privacy_mode: Whether to redact personal information
        
    Returns:
        Complete bill analysis
    """
    analyzer = BillAnalyzerAgent()
    
    with open(file_path, 'rb') as f:
        file_content = f.read()
    
    file_type = 'pdf' if file_path.lower().endswith('.pdf') else 'image'
    
    return analyzer.analyze_bill(file_content, file_type, privacy_mode)