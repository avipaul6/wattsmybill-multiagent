#!/usr/bin/env python3
"""
Comprehensive Plan Finder for WattsMyBill Market Research Agent
Uses the new comprehensive tariff extraction system to find optimal plans
Usage: python find_optimal_plans.py --kwh 8000 --postcode 4207 --format json
"""

import argparse
import json
from google.cloud import bigquery
import pandas as pd
import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
PROJECT_ID = os.environ.get('GOOGLE_CLOUD_PROJECT') or os.environ.get('GCP_PROJECT_ID') or 'wattsmybill-dev'
DATASET_ID = 'energy_plans'

class ComprehensivePlanFinder:
    """Find optimal energy plans using comprehensive tariff data"""
    
    def __init__(self):
        self.client = bigquery.Client(project=PROJECT_ID)
        
    def check_data_availability(self) -> Dict[str, int]:
        """Check availability of comprehensive data"""
        tables_to_check = [
            'plans_simple',
            'plan_contract_details', 
            'tariff_rates_comprehensive',
            'plan_discounts',
            'plan_fees',
            'solar_feed_in_tariffs',
            'plan_geography'
        ]
        
        availability = {}
        for table in tables_to_check:
            try:
                query = f"SELECT COUNT(*) as count FROM `{PROJECT_ID}.{DATASET_ID}.{table}`"
                result = self.client.query(query).to_dataframe()
                availability[table] = int(result['count'].iloc[0])
            except:
                availability[table] = 0
                
        return availability
    
    def calculate_comprehensive_cost(self, plan_id: str, annual_kwh: float, 
                                   usage_pattern: Dict = None) -> Dict[str, float]:
        """Calculate accurate cost using comprehensive tariff data"""
        
        # Get all rate components for this plan
        rates_query = f"""
        SELECT 
            rate_type,
            time_of_use_type,
            unit_price,
            unit,
            volume_min,
            volume_max,
            start_time,
            end_time,
            period
        FROM `{PROJECT_ID}.{DATASET_ID}.tariff_rates_comprehensive`
        WHERE plan_id = '{plan_id}'
        ORDER BY rate_type, time_of_use_type
        """
        
        rates_df = self.client.query(rates_query).to_dataframe()
        
        if rates_df.empty:
            # Fallback to simple estimation
            return {
                "daily_supply_annual": 365 * 1.20,
                "usage_annual": annual_kwh * 0.28,
                "total_annual": (365 * 1.20) + (annual_kwh * 0.28),
                "calculation_type": "ESTIMATED"
            }
        
        costs = {
            "daily_supply_annual": 0,
            "usage_annual": 0,
            "demand_annual": 0,
            "calculation_type": "COMPREHENSIVE"
        }
        
        # Calculate daily supply charges
        daily_supply = rates_df[rates_df['rate_type'] == 'DAILY_SUPPLY']
        if not daily_supply.empty:
            costs["daily_supply_annual"] = daily_supply['unit_price'].sum() * 365
        
        # Calculate usage charges
        usage_rates = rates_df[rates_df['rate_type'] == 'USAGE']
        
        if not usage_rates.empty:
            if len(usage_rates) == 1:
                # Single rate
                costs["usage_annual"] = usage_rates.iloc[0]['unit_price'] * annual_kwh
            else:
                # Time-of-use or stepped rates - simplified calculation
                # For Market Research Agent, we'll use average rate
                avg_rate = usage_rates['unit_price'].mean()
                costs["usage_annual"] = avg_rate * annual_kwh
        
        # Calculate demand charges (if any)
        demand_rates = rates_df[rates_df['rate_type'] == 'DEMAND']
        if not demand_rates.empty and usage_pattern:
            # Simplified demand calculation - assume 50% of peak usage as demand
            peak_demand_kw = usage_pattern.get('peak_demand_kw', annual_kwh / 8760 * 2)
            costs["demand_annual"] = demand_rates['unit_price'].sum() * peak_demand_kw * 12
        
        costs["total_annual"] = costs["daily_supply_annual"] + costs["usage_annual"] + costs["demand_annual"]
        
        return costs
    
    def get_plan_benefits(self, plan_id: str) -> Dict[str, Any]:
        """Get discounts, incentives, and solar benefits for a plan"""
        benefits = {
            "discounts": [],
            "incentives": [], 
            "solar_fit_rate": None,
            "fees": [],
            "green_power": False
        }
        
        # Get discounts
        discounts_query = f"""
        SELECT display_name, description, discount_type, category, rate, amount
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_discounts`
        WHERE plan_id = '{plan_id}'
        """
        
        try:
            discounts_df = self.client.query(discounts_query).to_dataframe()
            benefits["discounts"] = discounts_df.to_dict('records')
        except:
            pass
        
        # Get incentives
        incentives_query = f"""
        SELECT display_name, description, category
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_incentives`
        WHERE plan_id = '{plan_id}'
        """
        
        try:
            incentives_df = self.client.query(incentives_query).to_dataframe()
            benefits["incentives"] = incentives_df.to_dict('records')
        except:
            pass
        
        # Get solar feed-in tariff
        solar_query = f"""
        SELECT AVG(unit_price) as avg_fit_rate
        FROM `{PROJECT_ID}.{DATASET_ID}.solar_feed_in_tariffs`
        WHERE plan_id = '{plan_id}'
        """
        
        try:
            solar_df = self.client.query(solar_query).to_dataframe()
            if not solar_df.empty and solar_df.iloc[0]['avg_fit_rate']:
                benefits["solar_fit_rate"] = float(solar_df.iloc[0]['avg_fit_rate'])
        except:
            pass
        
        # Get fees
        fees_query = f"""
        SELECT fee_type, amount, rate, description
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_fees`
        WHERE plan_id = '{plan_id}'
        """
        
        try:
            fees_df = self.client.query(fees_query).to_dataframe()
            benefits["fees"] = fees_df.to_dict('records')
        except:
            pass
        
        # Check green power
        try:
            green_query = f"""
            SELECT COUNT(*) as green_count
            FROM `{PROJECT_ID}.{DATASET_ID}.green_power_charges`
            WHERE plan_id = '{plan_id}'
            """
            green_df = self.client.query(green_query).to_dataframe()
            benefits["green_power"] = int(green_df.iloc[0]['green_count']) > 0
        except:
            pass
        
        return benefits
    
    def check_postcode_availability(self, plan_id: str, postcode: str) -> bool:
        """Check if plan is available in postcode"""
        query = f"""
        SELECT 
            COUNTIF(included = true) as included_count,
            COUNTIF(included = false) as excluded_count
        FROM `{PROJECT_ID}.{DATASET_ID}.plan_geography`
        WHERE plan_id = '{plan_id}' AND postcode = '{postcode}'
        """
        
        try:
            result = self.client.query(query).to_dataframe()
            if not result.empty:
                row = result.iloc[0]
                return row['included_count'] > 0 and row['excluded_count'] == 0
        except:
            pass
        
        return True  # Default to available if no geo data
    
    def find_optimal_plans(self, annual_kwh: float, postcode: str = None, 
                          fuel_type: str = "ELECTRICITY", customer_type: str = "RESIDENTIAL",
                          include_solar: bool = False, max_results: int = 25) -> List[Dict[str, Any]]:
        """Find optimal plans using comprehensive data"""
        
        # Base query for plans with comprehensive data
        base_query = f"""
        WITH comprehensive_plans AS (
            SELECT DISTINCT
                p.plan_id,
                p.plan_name,
                p.brand,
                p.retailer,
                p.plan_type,
                p.fuel_type,
                p.customer_type,
                p.application_url,
                c.pricing_model,
                c.is_fixed,
                c.term_type,
                c.cooling_off_days
            FROM `{PROJECT_ID}.{DATASET_ID}.plans_simple` p
            INNER JOIN `{PROJECT_ID}.{DATASET_ID}.plan_contract_details` c ON p.plan_id = c.plan_id
            WHERE 
                p.fuel_type = '{fuel_type}'
                AND p.customer_type = '{customer_type}'
                AND (p.effective_to IS NULL OR p.effective_to > CURRENT_TIMESTAMP())
                AND p.plan_name IS NOT NULL
                AND p.brand IS NOT NULL
        )
        SELECT * FROM comprehensive_plans
        ORDER BY retailer, plan_name
        LIMIT {max_results * 2}  -- Get more to filter by postcode
        """
        
        plans_df = self.client.query(base_query).to_dataframe()
        
        if plans_df.empty:
            return []
        
        optimal_plans = []
        
        for _, plan_row in plans_df.iterrows():
            plan_id = plan_row['plan_id']
            
            # Check postcode availability
            if postcode and not self.check_postcode_availability(plan_id, postcode):
                continue
            
            # Calculate comprehensive costs
            costs = self.calculate_comprehensive_cost(plan_id, annual_kwh)
            
            # Get benefits and features
            benefits = self.get_plan_benefits(plan_id)
            
            # Skip if looking for solar and no solar FIT
            if include_solar and not benefits["solar_fit_rate"]:
                continue
            
            # Compile comprehensive plan data
            plan_data = {
                "plan_id": plan_id,
                "plan_name": plan_row['plan_name'],
                "brand": plan_row['brand'],
                "retailer": plan_row['retailer'],
                "plan_type": plan_row['plan_type'],
                "pricing_model": plan_row['pricing_model'],
                "is_fixed": plan_row['is_fixed'],
                "term_type": plan_row['term_type'],
                "cooling_off_days": plan_row['cooling_off_days'],
                "application_url": plan_row['application_url'],
                
                # Cost breakdown
                "costs": {
                    "total_annual": round(costs["total_annual"], 2),
                    "total_monthly": round(costs["total_annual"] / 12, 2),
                    "daily_supply_annual": round(costs["daily_supply_annual"], 2),
                    "usage_annual": round(costs["usage_annual"], 2),
                    "demand_annual": round(costs.get("demand_annual", 0), 2),
                    "calculation_type": costs["calculation_type"]
                },
                
                # Benefits and features
                "benefits": benefits,
                
                # Market research metadata
                "metadata": {
                    "annual_kwh": annual_kwh,
                    "postcode": postcode,
                    "analysis_date": datetime.utcnow().isoformat(),
                    "data_source": "comprehensive_extraction"
                }
            }
            
            optimal_plans.append(plan_data)
        
        # Sort by total annual cost
        optimal_plans.sort(key=lambda x: x["costs"]["total_annual"])
        
        return optimal_plans[:max_results]
    
    def get_market_analysis_summary(self, plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate market analysis summary for the Market Research Agent"""
        if not plans:
            return {"error": "No plans found"}
        
        costs = [plan["costs"]["total_annual"] for plan in plans]
        
        # Calculate market statistics
        analysis = {
            "market_summary": {
                "total_plans_analyzed": len(plans),
                "price_range": {
                    "min": min(costs),
                    "max": max(costs),
                    "median": sorted(costs)[len(costs)//2],
                    "average": sum(costs) / len(costs)
                },
                "potential_savings": max(costs) - min(costs),
                "savings_percentage": ((max(costs) - min(costs)) / max(costs)) * 100
            },
            
            "retailer_breakdown": {},
            "plan_type_breakdown": {},
            "pricing_model_breakdown": {},
            
            "top_plans": plans[:5],  # Top 5 cheapest
            
            "features_analysis": {
                "plans_with_solar": len([p for p in plans if p["benefits"]["solar_fit_rate"]]),
                "plans_with_discounts": len([p for p in plans if p["benefits"]["discounts"]]),
                "plans_with_incentives": len([p for p in plans if p["benefits"]["incentives"]]),
                "fixed_vs_variable": {
                    "fixed": len([p for p in plans if p["is_fixed"]]),
                    "variable": len([p for p in plans if not p["is_fixed"]])
                }
            },
            
            "data_quality": {
                "comprehensive_calculations": len([p for p in plans if p["costs"]["calculation_type"] == "COMPREHENSIVE"]),
                "estimated_calculations": len([p for p in plans if p["costs"]["calculation_type"] == "ESTIMATED"])
            }
        }
        
        # Retailer breakdown
        for plan in plans:
            retailer = plan["retailer"]
            if retailer not in analysis["retailer_breakdown"]:
                analysis["retailer_breakdown"][retailer] = {
                    "plan_count": 0,
                    "avg_cost": 0,
                    "min_cost": float('inf'),
                    "max_cost": 0
                }
            
            retailer_data = analysis["retailer_breakdown"][retailer]
            retailer_data["plan_count"] += 1
            cost = plan["costs"]["total_annual"]
            retailer_data["min_cost"] = min(retailer_data["min_cost"], cost)
            retailer_data["max_cost"] = max(retailer_data["max_cost"], cost)
        
        # Calculate average costs for retailers
        for retailer in analysis["retailer_breakdown"]:
            retailer_plans = [p for p in plans if p["retailer"] == retailer]
            retailer_costs = [p["costs"]["total_annual"] for p in retailer_plans]
            analysis["retailer_breakdown"][retailer]["avg_cost"] = sum(retailer_costs) / len(retailer_costs)
        
        return analysis

def main():
    parser = argparse.ArgumentParser(description="Find optimal energy plans for Market Research Agent")
    parser.add_argument("--kwh", type=float, default=6000, help="Annual kWh usage")
    parser.add_argument("--postcode", type=str, help="Postcode for availability check")
    parser.add_argument("--fuel", type=str, default="ELECTRICITY", choices=["ELECTRICITY", "GAS", "DUAL"])
    parser.add_argument("--customer", type=str, default="RESIDENTIAL", choices=["RESIDENTIAL", "BUSINESS"])
    parser.add_argument("--solar", action="store_true", help="Include only plans with solar feed-in tariffs")
    parser.add_argument("--max-results", type=int, default=25, help="Maximum number of plans to return")
    parser.add_argument("--format", type=str, default="text", choices=["text", "json"], help="Output format")
    parser.add_argument("--analysis-only", action="store_true", help="Return only market analysis summary")
    
    args = parser.parse_args()
    
    finder = ComprehensivePlanFinder()
    
    # Check data availability
    availability = finder.check_data_availability()
    
    if args.format == "text":
        print(f"🔍 Finding optimal plans for {args.kwh} kWh/year")
        if args.postcode:
            print(f"📍 Postcode: {args.postcode}")
        print(f"📋 Fuel: {args.fuel}, Customer: {args.customer}")
        print(f"📊 Data availability:")
        for table, count in availability.items():
            print(f"   {table}: {count:,} records")
    
    # Find optimal plans
    try:
        optimal_plans = finder.find_optimal_plans(
            annual_kwh=args.kwh,
            postcode=args.postcode,
            fuel_type=args.fuel,
            customer_type=args.customer,
            include_solar=args.solar,
            max_results=args.max_results
        )
        
        if args.analysis_only:
            # Return only market analysis for Market Research Agent
            analysis = finder.get_market_analysis_summary(optimal_plans)
            if args.format == "json":
                print(json.dumps(analysis, indent=2, default=str))
            else:
                print(f"\n📊 Market Analysis Summary:")
                print(f"   Plans analyzed: {analysis['market_summary']['total_plans_analyzed']}")
                print(f"   Price range: ${analysis['market_summary']['price_range']['min']:.2f} - ${analysis['market_summary']['price_range']['max']:.2f}")
                print(f"   Potential savings: ${analysis['market_summary']['potential_savings']:.2f} ({analysis['market_summary']['savings_percentage']:.1f}%)")
        
        elif args.format == "json":
            # Return full data for Market Research Agent
            output = {
                "optimal_plans": optimal_plans,
                "market_analysis": finder.get_market_analysis_summary(optimal_plans),
                "search_parameters": {
                    "annual_kwh": args.kwh,
                    "postcode": args.postcode,
                    "fuel_type": args.fuel,
                    "customer_type": args.customer,
                    "include_solar": args.solar
                }
            }
            print(json.dumps(output, indent=2, default=str))
        
        else:
            # Human-readable output
            print(f"\n🏆 Top {len(optimal_plans)} optimal plans:")
            
            for i, plan in enumerate(optimal_plans[:10], 1):
                calc_emoji = "🎯" if plan["costs"]["calculation_type"] == "COMPREHENSIVE" else "📊"
                solar_emoji = "☀️" if plan["benefits"]["solar_fit_rate"] else ""
                discount_emoji = "💰" if plan["benefits"]["discounts"] else ""
                
                print(f"\n  {i}. {calc_emoji}{solar_emoji}{discount_emoji} {plan['brand']}: {plan['plan_name']}")
                print(f"     💵 ${plan['costs']['total_annual']:.2f}/year (${plan['costs']['total_monthly']:.2f}/month)")
                print(f"     🏷️  {plan['plan_type']} | {plan['pricing_model']} | {plan['retailer']}")
                print(f"     📈 Supply: ${plan['costs']['daily_supply_annual']:.2f}/yr | Usage: ${plan['costs']['usage_annual']:.2f}/yr")
                
                if plan["benefits"]["solar_fit_rate"]:
                    print(f"     ☀️  Solar FIT: {plan['benefits']['solar_fit_rate']:.2f}¢/kWh")
                
                if plan["benefits"]["discounts"]:
                    discounts = ", ".join([d["category"] for d in plan["benefits"]["discounts"][:2]])
                    print(f"     💰 Discounts: {discounts}")
                
                if plan["application_url"]:
                    print(f"     🔗 {plan['application_url']}")
    
    except Exception as e:
        if args.format == "json":
            print(json.dumps({"error": str(e)}, indent=2))
        else:
            print(f"❌ Error finding plans: {e}")

if __name__ == "__main__":
    main()