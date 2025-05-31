"""
ENHANCED Market Research Agent - ETL Service Integration
Integrates with BigQuery ETL data warehouse while maintaining API fallback
File: src/agents/market_researcher.py
"""
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ETL Service Integration
try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound, Forbidden
    BIGQUERY_AVAILABLE = True
    print("✅ BigQuery ETL integration available")
except ImportError as e:
    print(f"⚠️  BigQuery not available: {e}")
    BIGQUERY_AVAILABLE = False

# Fallback to API integration
try:
    from integrations.australian_energy_api import AustralianEnergyAPI
    API_AVAILABLE = True
    print("✅ API fallback integration loaded")
except ImportError as e:
    print(f"⚠️  API integration not available: {e}")
    API_AVAILABLE = False


class ETLEnergyService:
    """
    ETL Data Service - Interfaces with BigQuery data warehouse
    """

    def __init__(self, project_id: str = "wattsmybill-dev", dataset_id: str = "energy_plans"):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.client = None
        self.connected = False

        # Performance settings
        self.use_materialized_views = True
        self.max_plans_limit = 30

        if BIGQUERY_AVAILABLE:
            try:
                self.client = bigquery.Client(project=project_id)
                self.client.query("SELECT 1").result()
                self.connected = True
                print(f"🔗 Connected to BigQuery: {project_id}.{dataset_id}")
                self._check_materialized_views()
            except Exception as e:
                print(f"⚠️  BigQuery connection failed: {e}")
                self.connected = False

        # Optimized queries
        self.queries = {
            'fast_market_plans': f"""
                SELECT 
                plan_id, retailer, pricing_model, is_fixed,
                usage_rate, supply_charge, solar_fit_rate,
                state_coverage, features, data_quality_score, extracted_at
                    FROM `{project_id}.{dataset_id}.v_best_plans_per_retailer`
                    WHERE state_coverage = @state OR state_coverage = 'MULTI'
                    ORDER BY data_quality_score DESC, usage_rate ASC
                    LIMIT @limit
            """,

            'standard_market_plans': f"""
                WITH RankedPlans AS (
                    SELECT 
                        pcd.plan_id, pcd.retailer, pcd.pricing_model, pcd.is_fixed, pcd.extracted_at,
                        trc.unit_price as usage_rate,
                        COALESCE(AVG(CASE WHEN trc2.rate_type = 'SUPPLY' THEN trc2.unit_price END) 
                                 OVER (PARTITION BY pcd.plan_id), 1.10) as supply_charge,
                        sft.unit_price as solar_fit_rate,
                        ROW_NUMBER() OVER (
                            PARTITION BY pcd.retailer 
                            ORDER BY CASE WHEN trc.unit_price IS NOT NULL THEN 1 ELSE 2 END,
                                     pcd.extracted_at DESC, trc.unit_price ASC
                        ) as rn
                    FROM `{project_id}.{dataset_id}.plan_contract_details` pcd
                    LEFT JOIN `{project_id}.{dataset_id}.tariff_rates_comprehensive` trc 
                        ON pcd.plan_id = trc.plan_id AND trc.rate_type = 'USAGE'
                        AND trc.unit_price BETWEEN 0.1 AND 0.8
                    LEFT JOIN `{project_id}.{dataset_id}.tariff_rates_comprehensive` trc2
                        ON pcd.plan_id = trc2.plan_id
                    LEFT JOIN `{project_id}.{dataset_id}.solar_feed_in_tariffs` sft 
                        ON pcd.plan_id = sft.plan_id AND sft.unit_price BETWEEN 0.0 AND 0.5
                    WHERE pcd.fuel_type = 'ELECTRICITY'
                    AND pcd.extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                    AND pcd.retailer IS NOT NULL
                )
                SELECT plan_id, retailer, pricing_model, is_fixed,
                       usage_rate, supply_charge, solar_fit_rate, extracted_at
                FROM RankedPlans 
                WHERE rn <= 2 AND usage_rate IS NOT NULL
                ORDER BY usage_rate ASC
                LIMIT @limit
            """
        }

    def _check_materialized_views(self):
        """Check if views exist and are accessible"""
        try:
            # Check for regular view instead
            view_query = f"""
                SELECT COUNT(*) as row_count
                FROM `{self.project_id}.{self.dataset_id}.v_best_plans_per_retailer`
                LIMIT 1
            """
            result = self.client.query(view_query).result()
            row_count = list(result)[0].row_count
            
            if row_count > 0:
                print(f"✅ Optimized views available ({row_count} plans)")
                self.use_materialized_views = True  # We'll use views instead
            else:
                print("⚠️  Views exist but empty - using standard queries")
                self.use_materialized_views = False
        except Exception as e:
            print(f"📊 Views not available - using standard queries")
            self.use_materialized_views = False

    def get_comprehensive_market_data(self, state: str = None, limit: int = 30) -> List[Dict[str, Any]]:
        """Get comprehensive market data with optimized performance"""
        if not self.connected:
            return []

        try:
            if self.use_materialized_views:
                query = self.queries['fast_market_plans']
                print(
                    f"🚀 Using optimized materialized view query (limit: {limit})")
            else:
                query = self.queries['standard_market_plans']
                print(f"📊 Using standard optimized query (limit: {limit})")

            state_mapping = {
                'NSW': 'NSW', 'QLD': 'QLD', 'VIC': 'VIC',
                'SA': 'SA', 'TAS': 'TAS', 'ACT': 'ACT',
                'WA': 'MULTI', 'NT': 'MULTI'
            }

            query_state = state_mapping.get(state, state) if state else 'NSW'

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter(
                        "state", "STRING", query_state),
                    bigquery.ScalarQueryParameter("limit", "INT64", limit),
                ],
                use_query_cache=True,
                maximum_bytes_billed=10**9
            )

            start_time = time.time()
            query_job = self.client.query(query, job_config=job_config)
            results = query_job.result(timeout=30)
            query_time = time.time() - start_time

            plans = []
            for row in results:
                plan = self._process_optimized_plan_row(row)
                if plan and self._is_valid_optimized_plan(plan):
                    plans.append(plan)

            print(
                f"⚡ ETL query completed in {query_time:.2f}s: {len(plans)} valid plans")

            if len(plans) < 10 and self.use_materialized_views:
                supplemental_plans = self._get_supplemental_plans(state, 15)
                plans.extend(supplemental_plans)
                print(f"📈 Added {len(supplemental_plans)} supplemental plans")

            return plans
        except Exception as e:
            print(f"⚠️  Optimized ETL query failed: {e}")
            return []

    def _process_optimized_plan_row(self, row) -> Dict[str, Any]:
        """Process a row from optimized materialized view query"""
        try:
            if hasattr(row, 'features') and row.features:
                features = [f for f in row.features if f is not None]
            else:
                features = self._generate_plan_features(
                    getattr(row, 'pricing_model', 'SINGLE_RATE'),
                    getattr(row, 'is_fixed', False)
                )

            plan = {
                'plan_id': row.plan_id,
                'retailer': row.retailer,
                'plan_name': self._generate_plan_name(row.plan_id, row.retailer),
                'pricing_model': getattr(row, 'pricing_model', 'SINGLE_RATE'),
                'is_fixed': getattr(row, 'is_fixed', False),
                'usage_rate': float(row.usage_rate) if row.usage_rate else None,
                'supply_charge': float(row.supply_charge) if row.supply_charge else self._estimate_supply_charge(row.retailer),
                'solar_fit_rate': float(row.solar_fit_rate) if row.solar_fit_rate else self._estimate_solar_rate(row.retailer),
                'has_solar_fit': True,
                'plan_type': 'market',
                'fuel_type': 'electricity',
                'customer_type': 'residential',
                'data_source': 'etl_optimized',
                'extracted_at': row.extracted_at.isoformat() if row.extracted_at else None,
                'features': features,
                'has_time_of_use': 'Time of use' in ' '.join(features),
                'has_demand_charges': False,
                'data_quality_score': getattr(row, 'data_quality_score', 2)
            }
            return plan
        except Exception as e:
            print(f"⚠️  Failed to process plan row: {e}")
            return None

    def _is_valid_optimized_plan(self, plan: Dict[str, Any]) -> bool:
        """Validate optimized plan data"""
        return (
            plan.get('usage_rate') is not None and
            plan.get('supply_charge') is not None and
            0.10 <= plan.get('usage_rate', 0) <= 0.80 and
            0.50 <= plan.get('supply_charge', 0) <= 3.00 and
            plan.get('retailer') and
            plan.get('plan_name')
        )

    def _get_supplemental_plans(self, state: str, limit: int) -> List[Dict[str, Any]]:
        """Get supplemental plans if main query returns few results"""
        try:
            supplemental_query = f"""
                SELECT DISTINCT
                    pcd.plan_id, pcd.retailer, pcd.pricing_model, pcd.is_fixed,
                    trc.unit_price as usage_rate,
                    1.10 as supply_charge,
                    COALESCE(sft.unit_price, 0.06) as solar_fit_rate,
                    pcd.extracted_at
                FROM `{self.project_id}.{self.dataset_id}.plan_contract_details` pcd
                LEFT JOIN `{self.project_id}.{self.dataset_id}.tariff_rates_comprehensive` trc 
                    ON pcd.plan_id = trc.plan_id AND trc.rate_type = 'USAGE'
                LEFT JOIN `{self.project_id}.{self.dataset_id}.solar_feed_in_tariffs` sft 
                    ON pcd.plan_id = sft.plan_id
                WHERE pcd.fuel_type = 'ELECTRICITY'
                AND trc.unit_price BETWEEN 0.15 AND 0.60
                AND pcd.retailer IN ('AGL', 'ORIGIN', 'ENERGYAUSTRALIA', 'ALINTA', 'RED_ENERGY')
                AND pcd.extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 14 DAY)
                ORDER BY trc.unit_price ASC
                LIMIT {limit}
            """

            job_config = bigquery.QueryJobConfig(use_query_cache=True)
            query_job = self.client.query(
                supplemental_query, job_config=job_config)
            results = query_job.result(timeout=15)

            plans = []
            for row in results:
                plan = self._process_optimized_plan_row(row)
                if plan and self._is_valid_optimized_plan(plan):
                    plan['data_source'] = 'etl_supplemental'
                    plans.append(plan)

            return plans
        except Exception as e:
            print(f"⚠️  Supplemental query failed: {e}")
            return []

    def _generate_plan_name(self, plan_id: str, retailer: str) -> str:
        """Generate readable plan name from plan_id"""
        if not plan_id or not retailer:
            return 'Unknown Plan'

        if 'MRE' in plan_id:
            return f"{retailer} Market Plan"
        elif 'STD' in plan_id:
            return f"{retailer} Standard Plan"
        elif 'GRN' in plan_id:
            return f"{retailer} Green Plan"
        else:
            return f"{retailer} Energy Plan"

    def _generate_plan_features(self, pricing_model: str, is_fixed: bool) -> List[str]:
        """Generate plan features based on attributes"""
        features = []

        if pricing_model == 'SINGLE_RATE':
            features.append('Simple pricing')
        elif pricing_model == 'TIME_OF_USE':
            features.append('Time of use pricing')

        if is_fixed:
            features.append('Fixed rate period')
        else:
            features.append('Variable rates')

        features.extend(['Market offer', 'Solar compatible'])
        return features

    def _estimate_supply_charge(self, retailer: str) -> float:
        """Estimate supply charge based on retailer"""
        retailer_estimates = {
            'AGL': 1.15, 'ORIGIN': 1.20, 'ENERGYAUSTRALIA': 1.10,
            'ALINTA': 1.05, 'RED_ENERGY': 1.25, 'SIMPLY_ENERGY': 1.35,
            'AMBER': 1.02, 'POWERSHOP': 1.05
        }
        return retailer_estimates.get(retailer.upper(), 1.10)

    def _estimate_solar_rate(self, retailer: str) -> float:
        """Estimate solar feed-in rate based on retailer"""
        retailer_solar_estimates = {
            'AGL': 0.06, 'ORIGIN': 0.05, 'ENERGYAUSTRALIA': 0.05,
            'ALINTA': 0.06, 'RED_ENERGY': 0.07, 'SIMPLY_ENERGY': 0.05,
            'AMBER': 0.00, 'POWERSHOP': 0.072
        }
        return retailer_solar_estimates.get(retailer.upper(), 0.06)

    def test_connection(self) -> Dict[str, Any]:
        """Test ETL service connection and data availability"""
        test_results = {
            'connected': self.connected,
            'timestamp': datetime.now().isoformat()
        }

        if not self.connected:
            test_results['error'] = 'BigQuery connection not available'
            return test_results

        try:
            plan_count_query = f"""
                SELECT COUNT(*) as total_plans
                FROM `{self.project_id}.{self.dataset_id}.plan_contract_details`
                WHERE fuel_type = 'ELECTRICITY'
                AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
            """

            result = self.client.query(plan_count_query).result()
            total_plans = list(result)[0].total_plans

            test_results.update({
                'total_plans_available': total_plans,
                'data_freshness': 'Last 7 days',
                'sample_retailers': self._get_sample_retailers()
            })
        except Exception as e:
            test_results['error'] = str(e)

        return test_results

    def _get_sample_retailers(self) -> List[str]:
        """Get sample of available retailers"""
        try:
            retailer_query = f"""
                SELECT DISTINCT retailer
                FROM `{self.project_id}.{self.dataset_id}.plan_contract_details`
                WHERE fuel_type = 'ELECTRICITY'
                AND extracted_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
                ORDER BY retailer LIMIT 10
            """
            result = self.client.query(retailer_query).result()
            return [row.retailer for row in result]
        except Exception:
            return []


class MarketResearcherAgent:
    """
    ENHANCED Market Research Agent with ETL Integration + API Fallback
    """

    def __init__(self, project_id: str = "wattsmybill-dev", dataset_id: str = "energy_plans"):
        self.logger = logging.getLogger(__name__)

        # Initialize ETL service (primary data source)
        self.etl_service = ETLEnergyService(project_id, dataset_id)
        self.use_etl = self.etl_service.connected

        # Initialize API service (fallback data source)
        if API_AVAILABLE:
            self.api = AustralianEnergyAPI()
            self.use_api_fallback = True
            print("🔄 ETL + API fallback configuration ready")
        else:
            self.api = None
            self.use_api_fallback = False
            print("📊 ETL-only configuration")

        # Enhanced fallback rates (market-competitive)
        self.competitive_retailer_rates = {
            'agl': {'usage_rate': 0.275, 'supply_charge': 1.15, 'solar_fit_rate': 0.06, 'plan_name': 'Value Saver'},
            'origin': {'usage_rate': 0.285, 'supply_charge': 1.20, 'solar_fit_rate': 0.05, 'plan_name': 'Origin Basic'},
            'energyaustralia': {'usage_rate': 0.295, 'supply_charge': 1.10, 'solar_fit_rate': 0.05, 'plan_name': 'Secure Saver'},
            'alinta': {'usage_rate': 0.265, 'supply_charge': 1.05, 'solar_fit_rate': 0.06, 'plan_name': 'Home Deal Plus'},
            'red_energy': {'usage_rate': 0.270, 'supply_charge': 1.25, 'solar_fit_rate': 0.07, 'plan_name': 'Living Energy'},
            'simply_energy': {'usage_rate': 0.259, 'supply_charge': 1.35, 'solar_fit_rate': 0.05, 'plan_name': 'Simply Plus'},
            'amber': {'usage_rate': 0.325, 'supply_charge': 1.02, 'solar_fit_rate': 0.00, 'plan_name': 'Wholesale Plan'},
            'powershop': {'usage_rate': 0.252, 'supply_charge': 1.05, 'solar_fit_rate': 0.072, 'plan_name': 'Power Plus'}
        }

        # Market insights and trends
        self.market_insights = {
            'average_rates_by_state': {
                'NSW': 0.285, 'QLD': 0.275, 'VIC': 0.275, 'SA': 0.315,
                'WA': 0.295, 'TAS': 0.265, 'NT': 0.325, 'ACT': 0.275
            }
        }

        print(f"🏭 Market Researcher initialized:")
        print(
            f"   ETL Service: {'✅ Connected' if self.use_etl else '❌ Unavailable'}")
        print(
            f"   API Fallback: {'✅ Available' if self.use_api_fallback else '❌ Unavailable'}")

    def research_better_plans(self, bill_data: Dict[str, Any], usage_analysis: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        ENHANCED: Main research method with ETL + API integration
        """
        try:
            print("🔍 Researching better electricity plans with ETL + API integration...")

            # Extract key information
            state = bill_data.get('state', 'NSW')
            current_retailer = bill_data.get('retailer', 'Unknown').lower()
            usage_kwh = bill_data.get('usage_kwh', 0)
            billing_days = bill_data.get('billing_days', 90)
            current_cost = bill_data.get('total_amount', 0)
            has_solar = bill_data.get('has_solar', False)
            solar_export = bill_data.get('solar_export_kwh', 0)

            # Calculate current cost per kWh
            current_cost_per_kwh = self._calculate_current_rate(bill_data)

            # Calculate annual usage
            annual_usage = int(usage_kwh * (365 / billing_days)
                               ) if billing_days > 0 else 0
            annual_solar_export = int(
                solar_export * (365 / billing_days)) if billing_days > 0 and has_solar else 0
            current_annual_cost = current_cost * \
                (365 / billing_days) if billing_days > 0 else 0

            print(f"📊 Research parameters:")
            print(f"   State: {state}")
            print(f"   Current retailer: {current_retailer}")
            print(f"   Current rate: ${current_cost_per_kwh:.3f}/kWh")
            print(f"   Current annual cost: ${current_annual_cost:.2f}")
            print(f"   Annual usage: {annual_usage:,} kWh")
            print(f"   Has solar: {has_solar}")
            if has_solar:
                print(f"   Annual solar export: {annual_solar_export:,} kWh")

            # Get plans from all available sources (OPTIMIZED)
            available_plans = self._get_multi_source_plans(
                state, has_solar, annual_usage, current_retailer)

            if not available_plans:
                return self._get_error_response(f"No plans available for {state}")

            print(
                f"📋 Found {len(available_plans)} plans from multiple sources")

            # Calculate costs for all plans
            plan_costs = self._calculate_enhanced_plan_costs(
                available_plans, annual_usage, annual_solar_export, current_annual_cost
            )

            # Sort plans by cost (cheapest first)
            plan_costs.sort(key=lambda x: x.get(
                'estimated_annual_cost', float('inf')))

            # Find genuinely better plans
            better_plans = [
                p for p in plan_costs
                if p.get('estimated_annual_cost', float('inf')) < current_annual_cost - 50
                and not p.get('is_current_retailer', False)
            ]

            print(f"💰 Found {len(better_plans)} genuinely better plans")
            for plan in better_plans[:3]:
                savings = current_annual_cost - \
                    plan.get('estimated_annual_cost', 0)
                data_source = plan.get('data_source', 'unknown')
                print(
                    f"   {plan.get('retailer')} {plan.get('plan_name')}: ${plan.get('estimated_annual_cost'):.2f} (saves ${savings:.2f}) [{data_source}]")

            # Get top plans
            top_plans = better_plans[:10] if better_plans else plan_costs[:8]
            best_plan = better_plans[0] if better_plans else None

            # Enhanced analysis
            savings_analysis = self._calculate_enhanced_savings(
                current_annual_cost, top_plans, better_plans, has_solar, state
            )

            market_analysis = self._generate_market_insights(
                state, current_retailer, bill_data, plan_costs, better_plans, current_cost_per_kwh
            )
            # Compile results with enhanced metadata
            research_result = {
                'data_source': 'etl_api_hybrid' if self.use_etl and self.use_api_fallback else 'etl_only' if self.use_etl else 'api_fallback',
                'research_parameters': {
                    'state': state,
                    'current_retailer': current_retailer.title(),
                    'current_rate_per_kwh': round(current_cost_per_kwh, 3),
                    'annual_usage_kwh': annual_usage,
                    'current_annual_cost': round(current_annual_cost, 2),
                    'has_solar': has_solar,
                    'solar_export_kwh': annual_solar_export
                },

                'recommended_plans': [
                    {
                        'retailer': plan.get('retailer', 'Unknown'),
                        'plan_name': plan.get('plan_name', 'Unknown Plan'),
                        'plan_id': plan.get('plan_id', 'unknown_plan'),
                        'estimated_annual_cost': round(plan.get('estimated_annual_cost', 0), 2),
                        'usage_rate': round(plan.get('usage_rate', 0), 3),
                        'supply_charge_daily': round(plan.get('supply_charge', 0), 2),
                        'solar_feed_in_tariff': round(plan.get('solar_fit_rate', 0), 3),
                        'key_features': plan.get('features', []),
                        'plan_type': plan.get('plan_type', 'market'),
                        'has_time_of_use': plan.get('has_time_of_use', False),
                        'has_demand_charges': plan.get('has_demand_charges', False),
                        'annual_savings': round(current_annual_cost - plan.get('estimated_annual_cost', 0), 2),
                        'monthly_savings': round((current_annual_cost - plan.get('estimated_annual_cost', 0)) / 12, 2),
                        'percentage_savings': round(((current_annual_cost - plan.get('estimated_annual_cost', 0)) / current_annual_cost) * 100, 1) if current_annual_cost > 0 else 0,
                        'is_current_retailer': plan.get('is_current_retailer', False),
                        'data_source': plan.get('data_source', 'fallback'),
                        'confidence_score': self._calculate_confidence_score(plan)
                    }
                    for plan in top_plans
                ],

                'best_plan': {
                    'retailer': best_plan.get('retailer', 'No Better Plan Found'),
                    'plan_name': best_plan.get('plan_name', 'Current plan is competitive'),
                    'plan_id': best_plan.get('plan_id', ''),
                    'estimated_annual_cost': round(best_plan.get('estimated_annual_cost', current_annual_cost), 2),
                    'annual_savings': round(current_annual_cost - best_plan.get('estimated_annual_cost', current_annual_cost), 2),
                    'monthly_savings': round((current_annual_cost - best_plan.get('estimated_annual_cost', current_annual_cost)) / 12, 2),
                    'percentage_savings': round(((current_annual_cost - best_plan.get('estimated_annual_cost', current_annual_cost)) / current_annual_cost) * 100, 1) if current_annual_cost > 0 else 0,
                    'confidence_score': self._calculate_confidence_score(best_plan) if best_plan else 0.5,
                    'why_best': self._get_why_best_explanation(best_plan, current_annual_cost, better_plans)
                } if best_plan else {
                    'retailer': 'Current Plan',
                    'plan_name': 'Your current plan is competitive',
                    'estimated_annual_cost': round(current_annual_cost, 2),
                    'annual_savings': 0,
                    'monthly_savings': 0,
                    'percentage_savings': 0,
                    'confidence_score': 0.8,
                    'why_best': 'Your current plan is already competitive with available market options'
                },

                'savings_analysis': savings_analysis,
                'market_insights': market_analysis,
                'better_plans_found': len(better_plans),

                # Enhanced metadata
                'research_timestamp': datetime.now().isoformat(),
                'plans_analyzed': len(plan_costs),
                'data_sources_used': self._get_data_sources_used(available_plans),
                'etl_status': 'connected' if self.use_etl else 'unavailable',
                'api_status': 'available' if self.use_api_fallback else 'unavailable',
                'researcher_version': '3.0_etl_hybrid'
            }

            print("✅ Enhanced ETL + API research completed successfully!")
            return research_result

        except Exception as e:
            self.logger.error(f"Enhanced market research failed: {e}")
            return self._get_error_response(str(e))

    def _get_multi_source_plans(self, state: str, has_solar: bool, annual_usage: int, current_retailer: str) -> List[Dict[str, Any]]:
        """OPTIMIZED: Get plans from all available sources with performance focus"""

        all_plans = []

        # Priority 1: ETL Service (primary data source) - OPTIMIZED
        if self.use_etl:
            print("🚀 Getting optimized plans from ETL data warehouse...")
            try:
                # Use smaller limit for better performance - focus on quality over quantity
                etl_limit = 25  # Reduced from 150
                etl_plans = self.etl_service.get_comprehensive_market_data(
                    state, limit=etl_limit)

                if etl_plans:
                    print(
                        f"✅ ETL: Retrieved {len(etl_plans)} optimized plans from data warehouse")
                    all_plans.extend(etl_plans)
                else:
                    print("⚠️  ETL: No plans returned from warehouse")
            except Exception as e:
                print(f"⚠️  ETL service failed: {e}")

        # Priority 2: API Service (only if ETL gives very few plans)
        if self.use_api_fallback and len(all_plans) < 15:
            print("🔄 Supplementing with focused API data...")
            try:
                # Only get a small number of API plans to supplement
                api_plans = self.api.get_plans_for_retailer(
                    'agl', state, limit=15)
                if api_plans:
                    print(
                        f"✅ API: Retrieved {len(api_plans)} supplementary plans")
                    # Mark as API source and limit to avoid duplicates
                    for plan in api_plans[:10]:  # Further limit API plans
                        plan['data_source'] = 'api_supplement'
                    all_plans.extend(api_plans[:10])
            except Exception as e:
                print(f"⚠️  API supplement failed: {e}")

        # Priority 3: Competitive fallback (essential retailers only)
        essential_retailers = ['agl', 'origin',
                               'energyaustralia', 'alinta', 'red_energy']
        fallback_plans = self._get_essential_fallback_plans(
            state, current_retailer, essential_retailers)
        all_plans.extend(fallback_plans)

        # Remove duplicates based on retailer + plan similarity
        unique_plans = self._deduplicate_plans(all_plans)

        print(
            f"⚡ Total unique plans from all sources: {len(unique_plans)} (optimized)")
        return unique_plans

    def _get_essential_fallback_plans(self, state: str, current_retailer: str, essential_retailers: List[str]) -> List[Dict[str, Any]]:
        """Get fallback plans for essential retailers only"""

        fallback_plans = []

        for retailer_key in essential_retailers:
            # Skip current retailer
            if current_retailer.lower().replace(' ', '_') == retailer_key:
                continue

            if retailer_key in self.competitive_retailer_rates:
                rates = self.competitive_retailer_rates[retailer_key]
                retailer_name = retailer_key.replace('_', ' ').title()

                plan = {
                    'plan_id': f'{retailer_key}_essential_{state.lower()}',
                    'retailer': retailer_name,
                    'plan_name': rates['plan_name'],
                    'usage_rate': rates['usage_rate'],
                    'supply_charge': rates['supply_charge'],
                    'solar_fit_rate': rates['solar_fit_rate'],
                    'has_solar_fit': True,
                    'plan_type': 'market',
                    'fuel_type': 'electricity',
                    'customer_type': 'residential',
                    'data_source': 'essential_fallback',
                    'features': ['Competitive market rates', 'No lock-in contract', 'Solar feed-in available'],
                    'has_time_of_use': False,
                    'has_demand_charges': False,
                    'is_current_retailer': False
                }

                fallback_plans.append(plan)

        print(f"✅ Generated {len(fallback_plans)} essential fallback plans")
        return fallback_plans

    def _deduplicate_plans(self, plans: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate plans based on retailer and similar rates"""

        seen_combinations = set()
        unique_plans = []

        for plan in plans:
            retailer = plan.get('retailer', '').lower()
            usage_rate = plan.get('usage_rate', 0)

            # Create a key that identifies similar plans
            rate_bucket = round(usage_rate * 1000) // 5 * \
                5  # Group rates within 0.005 range
            combination_key = f"{retailer}_{rate_bucket}"

            if combination_key not in seen_combinations:
                seen_combinations.add(combination_key)
                unique_plans.append(plan)

        print(
            f"🧹 Deduplicated: {len(plans)} → {len(unique_plans)} unique plans")
        return unique_plans

    def _calculate_enhanced_plan_costs(self, plans: List[Dict[str, Any]], annual_usage: int,
                                       annual_solar_export: int, current_annual_cost: float) -> List[Dict[str, Any]]:
        """Enhanced cost calculation with data source consideration"""

        plan_costs = []

        for plan in plans:
            try:
                # Extract plan details with data source awareness
                usage_rate = plan.get('usage_rate', 0.28)
                supply_charge_daily = plan.get('supply_charge', 1.10)
                solar_fit_rate = plan.get('solar_fit_rate', 0.06)
                data_source = plan.get('data_source', 'fallback')

                # Validate rates based on data source
                if not self._validate_plan_rates(usage_rate, supply_charge_daily, data_source):
                    # Apply fallback rates for invalid data
                    retailer_key = plan.get(
                        'retailer', 'agl').lower().replace(' ', '_')
                    fallback = self.competitive_retailer_rates.get(
                        retailer_key, self.competitive_retailer_rates['agl'])
                    usage_rate = fallback['usage_rate']
                    supply_charge_daily = fallback['supply_charge']
                    solar_fit_rate = fallback['solar_fit_rate']
                    plan['data_source'] = f"{data_source}_corrected"

                # Calculate costs
                annual_usage_cost = annual_usage * usage_rate
                annual_supply_cost = supply_charge_daily * 365
                annual_solar_credit = annual_solar_export * \
                    solar_fit_rate if annual_solar_export > 0 else 0
                estimated_annual_cost = annual_usage_cost + \
                    annual_supply_cost - annual_solar_credit

                # Add to plan data
                plan_cost = plan.copy()
                plan_cost.update({
                    'estimated_annual_cost': estimated_annual_cost,
                    'annual_usage_cost': annual_usage_cost,
                    'annual_supply_cost': annual_supply_cost,
                    'annual_solar_credit': annual_solar_credit,
                    'usage_rate': usage_rate,
                    'supply_charge': supply_charge_daily,
                    'solar_fit_rate': solar_fit_rate,
                    'cost_breakdown': {
                        'usage_cost': annual_usage_cost,
                        'supply_cost': annual_supply_cost,
                        'solar_credit': annual_solar_credit,
                        'net_cost': estimated_annual_cost
                    }
                })

                plan_costs.append(plan_cost)

                # Debug logging for first few plans
                if len(plan_costs) <= 3:
                    print(
                        f"💰 {plan.get('retailer')} {plan.get('plan_name')} [{data_source}]:")
                    print(
                        f"   Usage: {annual_usage:,} kWh × ${usage_rate:.3f} = ${annual_usage_cost:.2f}")
                    print(
                        f"   Supply: 365 days × ${supply_charge_daily:.2f} = ${annual_supply_cost:.2f}")
                    if annual_solar_credit > 0:
                        print(
                            f"   Solar: {annual_solar_export:,} kWh × ${solar_fit_rate:.3f} = -${annual_solar_credit:.2f}")
                    print(f"   Total: ${estimated_annual_cost:.2f}")

            except Exception as e:
                print(
                    f"⚠️  Cost calculation failed for {plan.get('retailer', 'Unknown')}: {e}")
                # Add plan with estimated cost to avoid losing it
                plan_cost = plan.copy()
                plan_cost['estimated_annual_cost'] = current_annual_cost * 1.1
                plan_costs.append(plan_cost)

        return plan_costs

    def _validate_plan_rates(self, usage_rate: float, supply_charge: float, data_source: str) -> bool:
        """Validate plan rates based on data source"""

        # ETL data should be more trusted
        if 'etl' in data_source.lower():
            # More lenient validation for ETL data
            return (0.10 <= usage_rate <= 0.80 and 0.50 <= supply_charge <= 3.00)

        # API and fallback data - stricter validation
        return (0.15 <= usage_rate <= 0.60 and 0.70 <= supply_charge <= 2.50)

    def _calculate_current_rate(self, bill_data: Dict[str, Any]) -> float:
        """Calculate current cost per kWh with multiple fallback strategies"""

        # Strategy 1: Use provided cost_per_kwh
        current_cost_per_kwh = bill_data.get('cost_per_kwh', 0)
        if 0.10 <= current_cost_per_kwh <= 0.80:  # Reasonable range
            return current_cost_per_kwh

        # Strategy 2: Calculate from usage charge and usage
        usage_charge = bill_data.get('usage_charge', 0)
        usage_kwh = bill_data.get('usage_kwh', 0)
        if usage_charge and usage_kwh:
            calculated_rate = usage_charge / usage_kwh
            if 0.10 <= calculated_rate <= 0.80:
                print(
                    f"🔧 Calculated current rate from usage: ${calculated_rate:.3f}/kWh")
                return calculated_rate

        # Strategy 3: Calculate from total bill and usage (less accurate)
        total_amount = bill_data.get('total_amount', 0)
        if total_amount and usage_kwh:
            estimated_rate = total_amount / usage_kwh
            if 0.15 <= estimated_rate <= 1.00:  # Includes supply charge
                adjusted_rate = estimated_rate * 0.85  # Rough adjustment for supply charge
                print(
                    f"🔧 Estimated current rate from total bill: ${adjusted_rate:.3f}/kWh")
                return adjusted_rate

        # Strategy 4: Use state average as fallback
        state = bill_data.get('state', 'NSW')
        state_average = self.market_insights['average_rates_by_state'].get(
            state, 0.285)
        print(
            f"🔧 Using state average rate for {state}: ${state_average:.3f}/kWh")
        return state_average
    
    def _calculate_enhanced_savings(self, current_annual_cost: float, top_plans: List[Dict], 
                                  better_plans: List[Dict], has_solar: bool, state: str) -> Dict[str, Any]:
        """Enhanced savings analysis"""
        
        if not top_plans or current_annual_cost <= 0:
            return {'error': 'Insufficient data for savings calculation'}
        
        # Calculate max savings from genuinely better plans
        max_savings = 0
        best_data_source = 'fallback'
        if better_plans:
            best_alternative_cost = better_plans[0].get('estimated_annual_cost', current_annual_cost)
            max_savings = current_annual_cost - best_alternative_cost
            best_data_source = better_plans[0].get('data_source', 'fallback')
        
        # Enhanced savings tiers
        savings_tiers = []
        plans_to_analyze = better_plans[:5] if better_plans else []
        
        for i, plan in enumerate(plans_to_analyze, 1):
            savings = current_annual_cost - plan.get('estimated_annual_cost', 0)
            savings_tiers.append({
                'rank': i,
                'retailer': plan.get('retailer', 'Unknown'),
                'plan_name': plan.get('plan_name', 'Unknown Plan'),
                'plan_type': plan.get('plan_type', 'market'),
                'annual_savings': round(savings, 2),
                'monthly_savings': round(savings / 12, 2),
                'percentage_savings': round((savings / current_annual_cost) * 100, 1) if current_annual_cost > 0 else 0,
                'data_source': plan.get('data_source', 'fallback'),
                'confidence': self._get_data_confidence(plan.get('data_source', 'fallback'))
            })
        
        # Enhanced potential assessment
        if max_savings > 500:
            savings_potential = 'high'
            savings_message = f'Excellent savings available - you could save ${max_savings:.0f} annually!'
        elif max_savings > 200:
            savings_potential = 'medium'
            savings_message = f'Good savings available - potential ${max_savings:.0f} annual savings'
        elif max_savings > 50:
            savings_potential = 'low'
            savings_message = f'Some savings available - up to ${max_savings:.0f} annually'
        else:
            savings_potential = 'none'
            savings_message = 'Your current plan is already competitive with available market options'
        
        return {
            'max_annual_savings': round(max_savings, 2),
            'max_monthly_savings': round(max_savings / 12, 2),
            'savings_potential': savings_potential,
            'savings_message': savings_message,
            'savings_tiers': savings_tiers,
            'better_plans_available': len(better_plans),
            'best_plan_data_source': best_data_source,
            'current_plan_ranking': self._get_current_plan_ranking(current_annual_cost, top_plans),
            'solar_consideration': self._get_solar_savings_note(has_solar, top_plans),
            'confidence_level': self._get_overall_confidence(better_plans)
        }
    
    def _generate_market_insights(self, state: str, current_retailer: str, 
                                bill_data: Dict[str, Any], all_plans: List[Dict], 
                                better_plans: List[Dict], current_rate: float) -> Dict[str, Any]:
        """Enhanced market insights with multi-source data"""
        
        state_average = self.market_insights['average_rates_by_state'].get(state, 0.285)
        
        # Analyze all plans by data source
        etl_plans = [p for p in all_plans if 'etl' in p.get('data_source', '').lower()]
        api_plans = [p for p in all_plans if 'api' in p.get('data_source', '').lower()]
        fallback_plans = [p for p in all_plans if 'fallback' in p.get('data_source', '').lower()]
        
        all_rates = [plan.get('usage_rate', 0) for plan in all_plans if plan.get('usage_rate')]
        retailers_analyzed = set(plan.get('retailer', '') for plan in all_plans)
        
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
        
        # Enhanced market trends
        trends = []
        
        if len(etl_plans) > 0:
            trends.append(f"🏭 ETL Warehouse: {len(etl_plans)} plans from comprehensive energy database")
        
        if len(api_plans) > 0:
            trends.append(f"📡 Live API: {len(api_plans)} plans from real-time market feeds")
        
        trends.append(f"📊 Analyzed {len(retailers_analyzed)} retailers: {', '.join(sorted(retailers_analyzed))}")
        
        if bill_data.get('has_solar'):
            solar_plans = [p for p in all_plans if p.get('has_solar_fit')]
            if solar_plans:
                avg_solar_rate = sum(p.get('solar_fit_rate', 0) for p in solar_plans) / len(solar_plans)
                trends.append(f"☀️ Average solar feed-in tariff: ${avg_solar_rate:.3f}/kWh across retailers")
        
        trends.append(f"💰 Market range: ${cheapest_rate:.3f} - ${most_expensive_rate:.3f}/kWh")
        
        if len(better_plans) > 0:
            trends.append(f"🎯 {len(better_plans)} better plans found across multiple sources")
        else:
            trends.append("🏆 Your current plan is competitive with market alternatives")
        
        return {
            'current_rate_position': rate_position,
            'state_average_rate': state_average,
            'live_market_average': round(average_market_rate, 3),
            'market_rate_range': {
                'cheapest': round(cheapest_rate, 3),
                'most_expensive': round(most_expensive_rate, 3),
                'spread': round(most_expensive_rate - cheapest_rate, 3)
            },
            'retailer_count': len(retailers_analyzed),
            'plans_analyzed': len(all_plans),
            'better_plans_found': len(better_plans),
            'data_source_breakdown': {
                'etl_plans': len(etl_plans),
                'api_plans': len(api_plans),
                'fallback_plans': len(fallback_plans)
            },
            'market_trends': trends,
            'data_freshness': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'switching_recommendation': self._get_enhanced_switching_recommendation(
                current_rate, average_market_rate, current_retailer, better_plans, all_plans
            )
        }
    
    def _get_data_sources_used(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary of data sources used"""
        
        source_counts = {}
        for plan in plans:
            source = plan.get('data_source', 'unknown')
            source_counts[source] = source_counts.get(source, 0) + 1
        
        return {
            'sources': source_counts,
            'primary_source': 'ETL Data Warehouse' if self.use_etl else 'API + Fallback',
            'total_sources': len(source_counts),
            'data_quality': 'high' if any('etl' in s for s in source_counts.keys()) else 'medium'
        }
    
    def _get_data_confidence(self, data_source: str) -> str:
        """Get confidence level based on data source"""
        if 'etl' in data_source.lower():
            return 'high'
        elif 'api' in data_source.lower():
            return 'medium'
        else:
            return 'estimated'
    
    def _get_overall_confidence(self, better_plans: List[Dict]) -> str:
        """Get overall confidence level"""
        if not better_plans:
            return 'medium'
        
        etl_plans = sum(1 for p in better_plans if 'etl' in p.get('data_source', '').lower())
        
        if etl_plans >= 2:
            return 'high'
        elif etl_plans >= 1:
            return 'good'
        else:
            return 'medium'
    
    def _calculate_confidence_score(self, plan: Optional[Dict[str, Any]]) -> float:
        """Calculate confidence score for plan recommendation"""
        if not plan:
            return 0.5
        
        data_source = plan.get('data_source', 'fallback')
        if 'etl' in data_source.lower():
            return 0.95  # High confidence with ETL data
        elif 'api' in data_source.lower():
            return 0.85  # Good confidence with API data
        elif 'essential_fallback' in data_source:
            return 0.75  # Good confidence with competitive estimates
        else:
            return 0.65  # Medium confidence with basic fallback
    
    def _get_current_plan_ranking(self, current_cost: float, all_plans: List[Dict]) -> str:
        """Determine where current plan ranks among available options"""
        if not all_plans:
            return "Unable to determine ranking"
        
        costs = [p.get('estimated_annual_cost', 0) for p in all_plans] + [current_cost]
        costs.sort()
        
        current_rank = costs.index(current_cost) + 1
        total_plans = len(costs)
        
        percentile = (current_rank / total_plans) * 100
        
        if percentile <= 25:
            return f"Excellent - top 25% of available plans (rank {current_rank} of {total_plans})"
        elif percentile <= 50:
            return f"Good - top 50% of available plans (rank {current_rank} of {total_plans})"
        elif percentile <= 75:
            return f"Average - top 75% of available plans (rank {current_rank} of {total_plans})"
        else:
            return f"Below average - bottom 25% of available plans (rank {current_rank} of {total_plans})"
    
    def _get_why_best_explanation(self, best_plan: Optional[Dict], current_cost: float, better_plans: List[Dict]) -> str:
        """Generate explanation for why a plan is recommended"""
        if not best_plan:
            return "No better plans found - your current plan is competitive"
        
        savings = current_cost - best_plan.get('estimated_annual_cost', 0)
        retailer = best_plan.get('retailer', 'Unknown')
        plan_name = best_plan.get('plan_name', 'Unknown Plan')
        data_source = best_plan.get('data_source', 'fallback')
        
        source_note = ""
        if 'etl' in data_source.lower():
            source_note = " (ETL warehouse data)"
        elif 'api' in data_source.lower():
            source_note = " (Live market data)"
        else:
            source_note = " (Market estimate)"
        
        if savings > 300:
            return f"Significant savings with {retailer} {plan_name} - saves ${savings:.0f} annually{source_note}"
        elif savings > 100:
            return f"Good value with {retailer} {plan_name} - saves ${savings:.0f} annually{source_note}"
        elif savings > 0:
            return f"Modest savings with {retailer} {plan_name} - saves ${savings:.0f} annually{source_note}"
        else:
            return f"Competitive option from {retailer} - similar costs to current plan{source_note}"
    
    def _get_enhanced_switching_recommendation(self, current_rate: float, market_average: float,
                                             current_retailer: str, better_plans: List[Dict], all_plans: List[Dict]) -> str:
        """Enhanced switching recommendation"""
        
        if len(better_plans) >= 3:
            return "🎯 STRONG RECOMMENDATION: Multiple retailers offer better plans - switching highly recommended"
        elif len(better_plans) >= 1:
            best_source = better_plans[0].get('data_source', 'fallback')
            confidence = "high confidence" if 'etl' in best_source.lower() else "good confidence"
            return f"💡 RECOMMENDED: Better options available from other retailers - worth switching ({confidence})"
        elif current_rate > market_average * 1.15:
            return "⚠️  REVIEW NEEDED: Your rate is above market average - explore alternatives"
        else:
            return "✅ COMPETITIVE: Your current plan is competitive with market options"
    
    def _get_solar_savings_note(self, has_solar: bool, plans: List[Dict]) -> Optional[str]:
        """Generate solar-specific savings note"""
        if not has_solar:
            return None
        
        solar_plans = [p for p in plans if p.get('has_solar_fit')]
        if not solar_plans:
            return "Limited solar feed-in options available"
        
        best_solar_rate = max(p.get('solar_fit_rate', 0) for p in solar_plans)
        avg_solar_rate = sum(p.get('solar_fit_rate', 0) for p in solar_plans) / len(solar_plans)
        
        return f"Best solar feed-in tariff: ${best_solar_rate:.3f}/kWh (avg: ${avg_solar_rate:.3f}/kWh)"
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response when research fails"""
        return {
            'error': True,
            'message': f'Market research failed: {error_message}',
            'research_timestamp': datetime.now().isoformat(),
            'recommended_plans': [],
            'best_plan': None,
            'etl_status': 'connected' if self.use_etl else 'unavailable',
            'api_status': 'available' if self.use_api_fallback else 'unavailable',
            'suggestions': [
                'Please check your location and usage data',
                'Verify ETL service connectivity',
                'Try again with different parameters'
            ]
        }
    
    def get_plan_comparison_summary(self, research_result: Dict[str, Any]) -> str:
        """Enhanced summary with data source information"""
        
        if research_result.get('error'):
            return f"Research Error: {research_result.get('message')}"
        
        best_plan = research_result.get('best_plan', {})
        savings_analysis = research_result.get('savings_analysis', {})
        data_source = research_result.get('data_source', 'unknown')
        better_plans_found = research_result.get('better_plans_found', 0)
        
        summary_parts = []
        
        # Data source indicator
        if 'etl' in data_source:
            summary_parts.append("🏭 Analysis using ETL data warehouse + market intelligence:")
        elif 'api' in data_source:
            summary_parts.append("📡 Analysis using live market APIs:")
        else:
            summary_parts.append("📊 Analysis using competitive market estimates:")
        
        # Savings summary
        max_savings = savings_analysis.get('max_annual_savings', 0)
        
        if max_savings > 100:
            summary_parts.append(f"💰 Best savings: ${max_savings:.0f}/year with {best_plan.get('retailer', 'alternative retailer')}.")
        elif better_plans_found > 0:
            summary_parts.append(f"💡 Found {better_plans_found} competitive alternatives with modest savings.")
        else:
            summary_parts.append("✅ Your current plan is competitive with market options.")
        
        # Market position and confidence
        market_insights = research_result.get('market_insights', {})
        rate_position = market_insights.get('current_rate_position', 'unknown')
        if rate_position != 'unknown':
            confidence = savings_analysis.get('confidence_level', 'medium')
            summary_parts.append(f"Your rate is {rate_position} compared to market average ({confidence} confidence).")
        
        return " ".join(summary_parts)
    
    def test_all_services(self) -> Dict[str, Any]:
        """Test all available services"""
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'etl_service': {},
            'api_service': {},
            'overall_status': 'unknown'
        }
        
        # Test ETL service
        if self.use_etl:
            test_results['etl_service'] = self.etl_service.test_connection()
        else:
            test_results['etl_service'] = {'connected': False, 'error': 'ETL service unavailable'}
        
        # Test API service
        if self.use_api_fallback:
            test_results['api_service'] = self.api.test_api_access()
        else:
            test_results['api_service'] = {'success': False, 'error': 'API service unavailable'}
        
        # Overall status
        etl_ok = test_results['etl_service'].get('connected', False)
        api_ok = test_results['api_service'].get('cdr_register_access', False)
        
        if etl_ok and api_ok:
            test_results['overall_status'] = 'excellent'
        elif etl_ok:
            test_results['overall_status'] = 'good'
        elif api_ok:
            test_results['overall_status'] = 'limited'
        else:
            test_results['overall_status'] = 'fallback_only'
        
        return test_results


# Utility functions for easy testing and integration
def research_plans_for_bill(bill_data: Dict[str, Any], project_id: str = "wattsmybill-dev") -> Dict[str, Any]:
    """
    Convenience function to research plans for a bill using ETL + API hybrid approach
    
    Args:
        bill_data: Parsed bill data from BillAnalyzerAgent
        project_id: BigQuery project ID (default: wattsmybill-dev)
        
    Returns:
        Complete market research results with multi-source data
    """
    researcher = MarketResearcherAgent(project_id=project_id)
    return researcher.research_better_plans(bill_data)


def test_etl_integration(project_id: str = "wattsmybill-dev") -> Dict[str, Any]:
    """
    Test ETL integration and data availability
    
    Args:
        project_id: BigQuery project ID
        
    Returns:
        Test results for all services
    """
    print("🧪 Testing ETL + API Integration")
    print("=" * 50)
    
    researcher = MarketResearcherAgent(project_id=project_id)
    test_results = researcher.test_all_services()
    
    # Print test results
    print(f"\n📊 Test Results:")
    print(f"   Overall Status: {test_results['overall_status'].upper()}")
    
    etl_status = test_results.get('etl_service', {})
    if etl_status.get('connected'):
        print(f"   ETL Service: ✅ Connected")
        print(f"   Available Plans: {etl_status.get('total_plans_available', 'Unknown')}")
        retailers = etl_status.get('sample_retailers', [])
        if retailers:
            print(f"   Sample Retailers: {', '.join(retailers[:5])}")
    else:
        print(f"   ETL Service: ❌ {etl_status.get('error', 'Unavailable')}")
    
    api_status = test_results.get('api_service', {})
    if api_status.get('cdr_register_access'):
        print(f"   API Service: ✅ Available")
        retailer_access = api_status.get('retailer_api_access', {})
        for retailer, status in retailer_access.items():
            if status.get('success'):
                print(f"   {retailer.upper()}: {status.get('valid_plans', 0)} valid plans")
    else:
        print(f"   API Service: ❌ {api_status.get('error', 'Unavailable')}")
    
    return test_results


def demo_market_research(project_id: str = "wattsmybill-dev"):
    """
    Demo the enhanced market research with sample bill data
    """
    print("🎯 Demo: Enhanced Market Research")
    print("=" * 50)
    
    # Sample bill data
    sample_bill = {
        'state': 'NSW',
        'retailer': 'AGL',
        'usage_kwh': 750,
        'billing_days': 92,
        'total_amount': 285.50,
        'usage_charge': 220.15,
        'supply_charge': 45.20,
        'cost_per_kwh': 0.294,
        'has_solar': True,
        'solar_export_kwh': 120
    }
    
    print("📋 Sample Bill Analysis:")
    for key, value in sample_bill.items():
        print(f"   {key}: {value}")
    
    print("\n🔍 Running Market Research...")
    
    # Run research
    researcher = MarketResearcherAgent(project_id=project_id)
    results = researcher.research_better_plans(sample_bill)
    
    if results.get('error'):
        print(f"❌ Research failed: {results.get('message')}")
        return results
    
    # Display results
    print(f"\n📊 Research Results:")
    print(f"   Data Source: {results.get('data_source', 'unknown')}")
    print(f"   Plans Analyzed: {results.get('plans_analyzed', 0)}")
    print(f"   Better Plans Found: {results.get('better_plans_found', 0)}")
    
    best_plan = results.get('best_plan', {})
    if best_plan.get('annual_savings', 0) > 0:
        print(f"\n💰 Best Plan:")
        print(f"   Retailer: {best_plan.get('retailer')}")
        print(f"   Plan: {best_plan.get('plan_name')}")
        print(f"   Annual Cost: ${best_plan.get('estimated_annual_cost', 0):.2f}")
        print(f"   Annual Savings: ${best_plan.get('annual_savings', 0):.2f}")
        print(f"   Monthly Savings: ${best_plan.get('monthly_savings', 0):.2f}")
        print(f"   Confidence: {best_plan.get('confidence_score', 0):.2f}")
    else:
        print(f"\n✅ Current Plan Status:")
        print(f"   Your current plan is competitive with available market options")
    
    # Summary
    summary = researcher.get_plan_comparison_summary(results)
    print(f"\n📋 Summary:")
    print(f"   {summary}")
    
    return results


# Backwards compatibility class alias
class EnhancedMarketResearcherAgent(MarketResearcherAgent):
    """
    Backwards compatibility alias for the enhanced agent
    """
    pass


if __name__ == "__main__":
    # Run comprehensive tests
    print("🚀 Enhanced Market Researcher Agent - ETL Integration")
    print("=" * 60)
    
    # Test ETL integration
    test_results = test_etl_integration()
    
    print("\n" + "=" * 60)
    
    # Demo market research
    demo_results = demo_market_research()
    
    print("\n✅ Integration testing completed!")
    print("💡 Use research_plans_for_bill(bill_data) for easy integration")
