"""
Fixed Bill Analyzer Agent - Solar detection and cost benchmark improvements
File: src/agents/bill_analyzer.py (UPDATED)
"""
from utils.bill_parser import AustralianBillParser
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


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
            # Very competitive rate (solar, competitive plans)
            'excellent': 0.22,
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
            print(f"🔍 Starting bill analysis...")
            print(f"   File type: {file_type}")
            print(f"   File size: {len(file_content)} bytes")
            print(f"   Privacy mode: {privacy_mode}")

            # Step 1: Parse the bill using our parser with enhanced error handling
            print("📄 Parsing energy bill...")
            try:
                parsed_data = self.parser.parse_bill(
                    file_content, file_type, privacy_mode)
                print(
                    f"✅ Parser completed. Method: {parsed_data.get('extraction_method', 'unknown')}")

                # Debug: Print key parsed data
                print(f"🐛 PARSED DATA DEBUG:")
                print(f"   Retailer: {parsed_data.get('retailer')}")
                print(f"   Usage (kWh): {parsed_data.get('usage_kwh')}")
                print(f"   Total amount: ${parsed_data.get('total_amount')}")
                print(f"   Billing days: {parsed_data.get('billing_days')}")
                print(f"   Has solar: {parsed_data.get('has_solar')}")
                print(
                    f"   Confidence: {parsed_data.get('confidence', 'unknown')}")

            except Exception as parser_error:
                print(f"❌ Parser failed: {parser_error}")
                # Return a structured error response instead of crashing
                return self._get_parser_error_response(str(parser_error), file_type)

            # Check if we got minimal required data
            if not self._validate_parsed_data(parsed_data):
                print("⚠️  Parsed data insufficient, generating fallback analysis")
                return self._get_fallback_analysis(parsed_data, file_type)

            if parsed_data.get('extraction_method') == 'fallback':
                print("⚠️  Parser used fallback data - analysis may be limited")

            # Step 2: Analyze usage patterns with error handling
            print("📊 Analyzing usage patterns...")
            try:
                usage_analysis = self._analyze_usage_patterns(parsed_data)
            except Exception as e:
                print(f"⚠️  Usage analysis failed: {e}")
                usage_analysis = self._get_fallback_usage_analysis(parsed_data)

            # Step 3: Analyze costs and efficiency with error handling
            print("💰 Analyzing costs and efficiency...")
            try:
                cost_analysis = self._analyze_costs(parsed_data)
            except Exception as e:
                print(f"⚠️  Cost analysis failed: {e}")
                cost_analysis = self._get_fallback_cost_analysis(parsed_data)

            # Step 4: Solar analysis with error handling
            print("☀️ Checking for solar system...")
            try:
                solar_analysis = self._analyze_solar_system(parsed_data)
            except Exception as e:
                print(f"⚠️  Solar analysis failed: {e}")
                solar_analysis = {'has_solar': False, 'error': str(e)}

            # Step 5: Generate recommendations with error handling
            print("💡 Generating recommendations...")
            try:
                recommendations = self._generate_recommendations(
                    parsed_data, usage_analysis, cost_analysis, solar_analysis)
            except Exception as e:
                print(f"⚠️  Recommendations generation failed: {e}")
                recommendations = [
                    "Analysis completed with limited data. Please try uploading a clearer bill."]

            # Step 6: Calculate efficiency score with error handling
            try:
                efficiency_score = self._calculate_efficiency_score(
                    usage_analysis, cost_analysis, solar_analysis)
            except Exception as e:
                print(f"⚠️  Efficiency score calculation failed: {e}")
                efficiency_score = 50  # Default score

            # Compile final analysis with comprehensive error handling
            analysis_result = {
                # Core bill data
                'bill_data': parsed_data,

                # Analysis results
                'usage_profile': {
                    'total_kwh': parsed_data.get('usage_kwh'),
                    'billing_days': parsed_data.get('billing_days'),
                    'daily_average': parsed_data.get('daily_average_kwh'),
                    'usage_category': usage_analysis.get('category', 'unknown'),
                    'usage_percentile': usage_analysis.get('percentile', 50),
                    'comparison_to_average': usage_analysis.get('comparison', 'Data not available')
                },

                'cost_breakdown': {
                    'total_cost': parsed_data.get('total_amount'),
                    'cost_per_kwh': parsed_data.get('cost_per_kwh'),
                    'supply_charge': parsed_data.get('supply_charge'),
                    'usage_charge': parsed_data.get('usage_charge'),
                    'cost_rating': cost_analysis.get('rating', 'unknown'),
                    'cost_comparison': cost_analysis.get('comparison', 'Unable to analyze')
                },

                'solar_analysis': solar_analysis,

                'efficiency_score': efficiency_score,

                'recommendations': recommendations,

                # Metadata
                'analysis_timestamp': datetime.now().isoformat(),
                'analyzer_version': '1.2',  # Updated version with error handling
                'confidence': parsed_data.get('confidence', 0.5),
                'analysis_quality': self._assess_analysis_quality(parsed_data, usage_analysis, cost_analysis)
            }

            print("✅ Bill analysis completed successfully!")
            print(
                f"   Quality assessment: {analysis_result['analysis_quality']}")
            print(f"   Confidence: {analysis_result['confidence']}")

            return analysis_result

        except Exception as e:
            self.logger.error(f"Bill analysis failed: {e}")
            print(f"❌ CRITICAL: Bill analysis failed: {e}")
            return self._get_critical_error_response(str(e))

    def _validate_parsed_data(self, parsed_data: Dict[str, Any]) -> bool:
        """Check if parsed data contains minimum required information"""

        required_fields = ['usage_kwh', 'total_amount', 'billing_days']
        missing_fields = []

        for field in required_fields:
            if not parsed_data.get(field):
                missing_fields.append(field)

        if missing_fields:
            print(f"⚠️  Missing required fields: {missing_fields}")
            return False

        # Check for reasonable values
        usage_kwh = parsed_data.get('usage_kwh', 0)
        total_amount = parsed_data.get('total_amount', 0)
        billing_days = parsed_data.get('billing_days', 0)

        if usage_kwh <= 0 or usage_kwh > 10000:
            print(f"⚠️  Unreasonable usage: {usage_kwh} kWh")
            return False

        if total_amount <= 0 or total_amount > 5000:
            print(f"⚠️  Unreasonable total amount: ${total_amount}")
            return False

        if billing_days <= 0 or billing_days > 400:
            print(f"⚠️  Unreasonable billing period: {billing_days} days")
            return False

        return True

    def _get_parser_error_response(self, error_message: str, file_type: str) -> Dict[str, Any]:
        """Return structured response when parser fails"""

        return {
            'error': True,
            'error_type': 'parser_failure',
            'message': f'Unable to extract data from {file_type} file: {error_message}',
            'bill_data': {},
            'usage_profile': {'error': 'Parser failed'},
            'cost_breakdown': {'error': 'Parser failed'},
            'solar_analysis': {'has_solar': False, 'error': 'Parser failed'},
            'efficiency_score': 0,
            'recommendations': [
                'The bill format could not be processed automatically',
                'Try uploading a clearer image or different file format',
                'Ensure the bill is complete and all text is visible',
                'Contact support if the problem persists'
            ],
            'analysis_timestamp': datetime.now().isoformat(),
            'analyzer_version': '1.2',
            'confidence': 0.0
        }

    def _get_fallback_analysis(self, parsed_data: Dict[str, Any], file_type: str) -> Dict[str, Any]:
        """Return limited analysis when data is insufficient"""

        return {
            'error': False,
            'message': 'Limited analysis due to insufficient data extraction',
            'bill_data': parsed_data,
            'usage_profile': {
                'total_kwh': parsed_data.get('usage_kwh'),
                'billing_days': parsed_data.get('billing_days'),
                'daily_average': parsed_data.get('daily_average_kwh'),
                'usage_category': 'unknown',
                'usage_percentile': 50,
                'comparison_to_average': 'Unable to determine due to limited data'
            },
            'cost_breakdown': {
                'total_cost': parsed_data.get('total_amount'),
                'cost_per_kwh': parsed_data.get('cost_per_kwh'),
                'cost_rating': 'unknown',
                'cost_comparison': 'Unable to analyze due to limited data'
            },
            'solar_analysis': {'has_solar': False, 'note': 'Solar analysis requires more complete data'},
            'efficiency_score': 25,  # Low score for incomplete data
            'recommendations': [
                'Bill data was partially extracted but incomplete',
                'Try uploading a higher quality image or PDF',
                'Ensure all pages of multi-page bills are included',
                'For better analysis, upload bills with clearly visible usage and cost information'
            ],
            'analysis_timestamp': datetime.now().isoformat(),
            'analyzer_version': '1.2',
            'confidence': 0.3,
            'analysis_quality': 'limited'
        }

    def _get_fallback_usage_analysis(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback usage analysis when main analysis fails"""

        usage_kwh = parsed_data.get('usage_kwh', 0)
        billing_days = parsed_data.get('billing_days', 90)

        if usage_kwh and billing_days:
            daily_average = usage_kwh / billing_days
            return {
                'category': 'unknown',
                'percentile': 50,
                'comparison': f'Daily usage: {daily_average:.1f} kWh (unable to compare to benchmarks)',
                'daily_usage': daily_average,
                'error': 'Limited usage analysis'
            }

        return {
            'category': 'unknown',
            'percentile': 50,
            'comparison': 'Usage data not available',
            'error': 'Insufficient usage data'
        }

    def _get_fallback_cost_analysis(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback cost analysis when main analysis fails"""

        total_amount = parsed_data.get('total_amount')
        usage_kwh = parsed_data.get('usage_kwh')

        if total_amount and usage_kwh:
            cost_per_kwh = total_amount / usage_kwh
            return {
                'rating': 'unknown',
                'comparison': f'Estimated rate: ${cost_per_kwh:.3f}/kWh (unable to benchmark)',
                'cost_per_kwh': cost_per_kwh,
                'error': 'Limited cost analysis'
            }

        return {
            'rating': 'unknown',
            'comparison': 'Cost data not available',
            'error': 'Insufficient cost data'
        }

    def _assess_analysis_quality(self, parsed_data: Dict[str, Any], usage_analysis: Dict[str, Any], cost_analysis: Dict[str, Any]) -> str:
        """Assess the overall quality of the analysis"""

        quality_score = 0

        # Check data completeness
        if parsed_data.get('usage_kwh') and parsed_data.get('total_amount') and parsed_data.get('billing_days'):
            quality_score += 3

        if parsed_data.get('retailer'):
            quality_score += 1

        if parsed_data.get('cost_per_kwh'):
            quality_score += 1

        # Check analysis completeness
        if usage_analysis.get('category') != 'unknown':
            quality_score += 2

        if cost_analysis.get('rating') != 'unknown':
            quality_score += 2

        # Determine quality level
        if quality_score >= 8:
            return 'excellent'
        elif quality_score >= 6:
            return 'good'
        elif quality_score >= 4:
            return 'fair'
        elif quality_score >= 2:
            return 'limited'
        else:
            return 'poor'

    def _get_critical_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return response for critical analysis failures"""

        return {
            'error': True,
            'error_type': 'critical_failure',
            'message': f'Critical analysis failure: {error_message}',
            'bill_data': {},
            'usage_profile': {'error': 'Analysis failed'},
            'cost_breakdown': {'error': 'Analysis failed'},
            'solar_analysis': {'has_solar': False, 'error': 'Analysis failed'},
            'efficiency_score': 0,
            'recommendations': [
                'A critical error occurred during bill analysis',
                'Please try uploading the bill again',
                'If the problem persists, try a different file format',
                'Contact technical support for assistance'
            ],
            'analysis_timestamp': datetime.now().isoformat(),
            'analyzer_version': '1.2',
            'confidence': 0.0,
            'analysis_quality': 'failed'
        }

    def _analyze_usage_patterns(self, bill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze usage patterns and compare to benchmarks"""

        usage_kwh = bill_data.get('usage_kwh')
        billing_days = bill_data.get('billing_days')
        state = bill_data.get('state', 'NSW')
        daily_usage = bill_data.get('daily_average_kwh')

        if not usage_kwh or not billing_days:
            return {'error': 'Insufficient usage data'}

        # Get benchmarks for this state
        benchmarks = self.usage_benchmarks.get(
            state, self.usage_benchmarks['NSW'])

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
        seasonal_note = self._get_seasonal_note(
            bill_data.get('billing_period'))

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
            print(
                f"⚠️  WARNING: Cost per kWh seems too high: ${cost_per_kwh:.3f}")
            print(f"   Total: ${total_amount}, Usage: {usage_kwh} kWh")

            # Try to recalculate with usage charge only (excluding supply charge)
            if usage_charge and usage_kwh:
                recalculated_rate = usage_charge / usage_kwh
                print(
                    f"   Recalculated rate (usage only): ${recalculated_rate:.3f}/kWh")
                if 0.15 <= recalculated_rate <= 0.60:  # Reasonable range
                    cost_per_kwh = recalculated_rate
                    print(
                        f"   Using recalculated rate: ${cost_per_kwh:.3f}/kWh")

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
        annual_cost = int(total_amount * (365 / billing_days)
                          ) if billing_days and total_amount else None

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
        annual_solar_savings = solar_credit * \
            (365 / billing_days) if billing_days else 0

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
            potential_savings_per_kwh = cost_analysis.get(
                'potential_savings_per_kwh', 0)
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
        summary_parts.append(
            f"Overall efficiency score: {efficiency_score:.0f}/100.")

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
