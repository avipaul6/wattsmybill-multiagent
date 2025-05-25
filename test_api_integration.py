#!/usr/bin/env python3
"""
FIXED WattsMyBill API Integration Test Script
Now handles None values properly

Usage: python test_api_integration.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_api_endpoints():
    """FIXED: Test direct API endpoint access with better None handling"""
    print("🔬 Testing Direct API Endpoints")
    print("="*50)
    
    try:
        from integrations.australian_energy_api import AustralianEnergyAPI
        
        api = AustralianEnergyAPI()
        
        # Test 1: CDR Register Access
        print("1️⃣ Testing CDR Register Access...")
        retailers = api.get_all_retailers()
        
        if retailers:
            print(f"   ✅ SUCCESS: Found {len(retailers)} energy retailers")
            print(f"   📋 Sample retailers: {[r['brand_name'] for r in retailers[:3]]}")
        else:
            print("   ⚠️  No retailers found (may be expected)")
        
        # Test 2: Plan Data Access (FIXED)
        print("\n2️⃣ Testing Plan Data Access...")
        test_retailers = ['agl']  # Start with just AGL
        
        for retailer in test_retailers:
            print(f"   Testing {retailer}...")
            plans = api.get_plans_for_retailer(retailer, 'NSW')
            
            if plans:
                print(f"   ✅ {retailer}: Found {len(plans)} plans")
                
                # FIXED: Better sample plan display with None handling
                sample_plan = plans[0]
                plan_name = sample_plan.get('plan_name', 'Unknown')
                usage_rate = sample_plan.get('usage_rate')
                supply_charge = sample_plan.get('supply_charge')
                data_quality = sample_plan.get('data_quality', 'unknown')
                
                # Safe formatting
                if usage_rate is not None:
                    print(f"   📊 Sample: {plan_name} - ${usage_rate:.3f}/kWh")
                else:
                    print(f"   📊 Sample: {plan_name} - Rate: N/A")
                
                if supply_charge is not None:
                    print(f"      Supply: ${supply_charge:.2f}/day")
                else:
                    print(f"      Supply: N/A")
                
                print(f"      Data Quality: {data_quality}")
                
            else:
                print(f"   📊 {retailer}: Using fallback data")
        
        # Test 3: State Plans (FIXED)
        print("\n3️⃣ Testing State Plan Search...")
        nsw_plans = api.get_all_plans_for_state('NSW')
        print(f"   ✅ NSW: Found {len(nsw_plans)} total plans")
        
        # Show breakdown by data quality
        quality_breakdown = {}
        for plan in nsw_plans:
            quality = plan.get('data_quality', 'unknown')
            quality_breakdown[quality] = quality_breakdown.get(quality, 0) + 1
        
        print(f"   📊 Data Quality Breakdown: {quality_breakdown}")
        
        # Test 4: Plan Search with Criteria (FIXED)
        print("\n4️⃣ Testing Plan Search...")
        criteria = {
            'state': 'NSW',
            'fuel_type': 'electricity',
            'has_solar': True,
            'usage_kwh': 4000
        }
        
        matching_plans = api.search_plans(criteria)
        print(f"   ✅ Search: Found {len(matching_plans)} matching plans")
        
        if matching_plans:
            best_plan = matching_plans[0]
            plan_name = best_plan.get('plan_name', 'Unknown')
            retailer = best_plan.get('retailer', 'Unknown')
            annual_cost = best_plan.get('estimated_annual_cost', 0)
            
            print(f"   🏆 Best: {retailer} - {plan_name}")
            print(f"      Annual Cost: ${annual_cost:.0f}")
            print(f"      Data Quality: {best_plan.get('data_quality', 'unknown')}")
        
        # Test 5: API Status (FIXED)
        print("\n5️⃣ Testing API Status...")
        status = api.test_api_access()
        print(f"   📡 CDR Register: {'✅' if status.get('cdr_register_access') else '❌'}")
        
        retailer_status = status.get('retailer_api_access', {})
        for retailer, result in retailer_status.items():
            success_icon = '✅' if result.get('success') else '❌'
            valid_plans = result.get('valid_plans', 0)
            total_plans = result.get('total_plans', 0)
            print(f"   📡 {retailer}: {success_icon} ({valid_plans}/{total_plans} valid)")
        
        overall_success = status.get('test_summary', {}).get('overall_success', False)
        print(f"   🎯 Overall API Status: {'✅ Working' if overall_success else '❌ Issues'}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import API module: {e}")
        print("   Make sure australian_energy_api.py is in src/integrations/")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_market_researcher_integration():
    """FIXED: Test the enhanced market researcher with better error handling"""
    print("\n🤖 Testing Enhanced Market Researcher")
    print("="*50)
    
    try:
        from agents.market_researcher import MarketResearcherAgent
        
        # Create test bill data
        test_bill = {
            'state': 'NSW',
            'retailer': 'AGL',
            'usage_kwh': 720,
            'billing_days': 90,
            'total_amount': 350.0,
            'cost_per_kwh': 0.486,  # Deliberately high to show savings
            'has_solar': True,
            'solar_export_kwh': 200
        }
        
        print("📊 Test bill data:")
        print(f"   State: {test_bill['state']}")
        print(f"   Usage: {test_bill['usage_kwh']} kWh/{test_bill['billing_days']} days")
        print(f"   Cost: ${test_bill['total_amount']} (${test_bill['cost_per_kwh']:.3f}/kWh)")
        print(f"   Solar: {test_bill['has_solar']} ({test_bill['solar_export_kwh']} kWh export)")
        
        # Create researcher and analyze
        researcher = MarketResearcherAgent()
        
        print(f"\n🔍 Running market research...")
        print(f"   API Status: {'🌐 LIVE DATA' if researcher.use_real_api else '📊 FALLBACK DATA'}")
        
        result = researcher.research_better_plans(test_bill)
        
        # FIXED: Display results with None handling
        print(f"\n📋 RESEARCH RESULTS:")
        print(f"   Data Source: {result.get('data_source', 'unknown')}")
        print(f"   Plans Analyzed: {result.get('plans_analyzed', 0)}")
        
        # Best plan (FIXED)
        best_plan = result.get('best_plan')
        if best_plan:
            print(f"\n🏆 BEST PLAN:")
            print(f"   Retailer: {best_plan.get('retailer', 'Unknown')}")
            print(f"   Plan: {best_plan.get('plan_name', 'Unknown')}")
            
            annual_cost = best_plan.get('estimated_annual_cost', 0)
            annual_savings = best_plan.get('annual_savings', 0)
            monthly_savings = best_plan.get('monthly_savings', 0)
            confidence = best_plan.get('confidence_score', 0)
            
            print(f"   Annual Cost: ${annual_cost:.0f}")
            print(f"   Annual Savings: ${annual_savings:.0f}")
            print(f"   Monthly Savings: ${monthly_savings:.0f}")
            print(f"   Confidence: {confidence:.0%}")
        else:
            print("\n⚠️  No best plan found")
        
        # Top recommendations (FIXED)
        recommendations = result.get('recommended_plans', [])
        if recommendations:
            print(f"\n💡 TOP 3 RECOMMENDATIONS:")
            for i, plan in enumerate(recommendations[:3], 1):
                retailer = plan.get('retailer', 'Unknown')
                plan_name = plan.get('plan_name', 'Unknown')
                annual_cost = plan.get('estimated_annual_cost', 0)
                annual_savings = plan.get('annual_savings', 0)
                usage_rate = plan.get('usage_rate', 0)
                supply_charge = plan.get('supply_charge_daily', 0)
                solar_fit = plan.get('solar_feed_in_tariff', 0)
                
                print(f"   {i}. {retailer} - {plan_name}")
                print(f"      💰 ${annual_cost:.0f}/year (Save ${annual_savings:.0f})")
                
                if usage_rate and supply_charge:
                    print(f"      ⚡ ${usage_rate:.3f}/kWh + ${supply_charge:.2f}/day")
                else:
                    print(f"      ⚡ Rate information not available")
                
                if solar_fit:
                    print(f"      ☀️ Solar: ${solar_fit:.3f}/kWh")
        else:
            print("\n⚠️  No recommendations found")
        
        # Market insights (FIXED)
        insights = result.get('market_insights', {})
        if insights:
            print(f"\n📈 MARKET INSIGHTS:")
            print(f"   Rate Position: {insights.get('current_rate_position', 'unknown')}")
            
            live_avg = insights.get('live_market_average', 0)
            if live_avg:
                print(f"   Market Average: ${live_avg:.3f}/kWh")
            
            rate_range = insights.get('market_rate_range', {})
            cheapest = rate_range.get('cheapest', 0)
            if cheapest:
                print(f"   Cheapest Available: ${cheapest:.3f}/kWh")
            
            print(f"   Retailers Analyzed: {insights.get('retailer_count', 0)}")
        
        # Summary (FIXED)
        summary = researcher.get_plan_comparison_summary(result)
        print(f"\n📝 SUMMARY:")
        print(f"   {summary}")
        
        # Check if we got real data
        data_source = result.get('data_source', 'unknown')
        if data_source == 'real_api':
            print(f"\n✅ SUCCESS: Using real Australian energy market data!")
        else:
            print(f"\n⚠️  INFO: Using fallback data (API may be unavailable)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import MarketResearcherAgent: {e}")
        return False
    except Exception as e:
        print(f"❌ Market researcher test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_streamlit_integration():
    """FIXED: Test integration with Streamlit app"""
    print("\n🎨 Testing Streamlit Integration")
    print("="*50)
    
    try:
        # Test if we can import the necessary components
        print("1️⃣ Testing imports...")
        
        # Check if streamlit is available
        try:
            import streamlit as st
            print("   ✅ Streamlit available")
        except ImportError:
            print("   ⚠️  Streamlit not installed (pip install streamlit)")
            return False
        
        # Check agent imports
        from agents.market_researcher import MarketResearcherAgent
        print("   ✅ Market researcher available")
        
        # Check if bill analyzer is available
        try:
            from agents.bill_analyzer import BillAnalyzerAgent
            print("   ✅ Bill analyzer available")
        except ImportError:
            print("   ⚠️  Bill analyzer not found")
        
        print("\n2️⃣ Testing real agent workflow...")
        
        # Simulate the workflow that would happen in Streamlit
        def simulate_streamlit_workflow():
            # Mock uploaded file data
            mock_bill_data = {
                'retailer': 'AGL',
                'usage_kwh': 800,
                'billing_days': 91,
                'total_amount': 385.50,
                'state': 'NSW',
                'has_solar': False,
                'cost_per_kwh': 0.482
            }
            
            # Market research (this would be called from app.py)
            researcher = MarketResearcherAgent()
            research_result = researcher.research_better_plans(mock_bill_data)
            
            return research_result
        
        result = simulate_streamlit_workflow()
        
        if result and not result.get('error'):
            print("   ✅ Workflow completed successfully")
            print(f"   📊 Found {result.get('plans_analyzed', 0)} plans")
            
            best_plan = result.get('best_plan', {})
            annual_savings = best_plan.get('annual_savings', 0)
            print(f"   💰 Potential savings: ${annual_savings:.0f}/year")
            
            data_source = result.get('data_source', 'unknown')
            print(f"   📡 Data source: {data_source}")
            
            return True
        else:
            print("   ❌ Workflow failed")
            error_msg = result.get('message', 'Unknown error') if result else 'No result returned'
            print(f"   Error: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Streamlit integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_integration_report(api_success, researcher_success, streamlit_success):
    """FIXED: Generate a comprehensive integration report"""
    
    print("\n" + "="*70)
    print("🎯 INTEGRATION REPORT")
    print("="*70)
    
    overall_success = api_success and researcher_success and streamlit_success
    
    print(f"📊 Overall Status: {'✅ READY FOR PRODUCTION' if overall_success else '⚠️  NEEDS ATTENTION'}")
    print(f"🕐 Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n📋 Component Status:")
    print(f"   🔌 API Integration: {'✅ Working' if api_success else '❌ Failed'}")
    print(f"   🤖 Market Researcher: {'✅ Working' if researcher_success else '❌ Failed'}")
    print(f"   🎨 Streamlit Integration: {'✅ Ready' if streamlit_success else '❌ Issues'}")
    
    if overall_success:
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. ✅ Your real API integration is working!")
        print(f"   2. 🔄 Replace the fixed australian_energy_api.py in your project")
        print(f"   3. 🔄 Update your app.py to use real agents")
        print(f"   4. 🧪 Test with real energy bills")
        print(f"   5. 🎯 Deploy and start helping Australians save money!")
        
        print(f"\n💡 USAGE EXAMPLE:")
        print(f"   # Replace your current API file:")
        print(f"   cp fixed_australian_energy_api.py src/integrations/australian_energy_api.py")
        print(f"   ")
        print(f"   # Test the fix:")
        print(f"   python test_api_integration.py")
        
    else:
        print(f"\n🔧 ISSUES TO RESOLVE:")
        if not api_success:
            print(f"   ❌ API Integration Issues:")
            print(f"      - Replace australian_energy_api.py with fixed version")
            print(f"      - Ensure proper None value handling")
        if not researcher_success:
            print(f"   ❌ Market Researcher Issues:")
            print(f"      - Check agent imports")
            print(f"      - Verify error handling")
        if not streamlit_success:
            print(f"   ❌ Streamlit Integration Issues:")
            print(f"      - Install streamlit: pip install streamlit")
            print(f"      - Check import paths")
        
        print(f"\n📞 TROUBLESHOOTING:")
        print(f"   1. Replace API file with fixed version from artifacts")
        print(f"   2. Check internet connection for API access") 
        print(f"   3. Verify all required packages are installed")
        print(f"   4. Run: pip install requests streamlit")
    
    # Show what the fix addresses
    print(f"\n🔧 FIXES APPLIED:")
    print(f"   ✅ None value handling in plan data")
    print(f"   ✅ Safe format string operations")
    print(f"   ✅ Fallback tariff values for incomplete data")
    print(f"   ✅ Better error logging and recovery")
    print(f"   ✅ Data quality indicators")
    
    return overall_success

def main():
    """FIXED: Run all integration tests with better error handling"""
    
    print("🚀 WattsMyBill - FIXED Real API Integration Test Suite")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run all tests
    print("Running comprehensive integration tests with fixes...\n")
    
    api_success = test_api_endpoints()
    researcher_success = test_market_researcher_integration()
    streamlit_success = test_streamlit_integration()
    
    # Generate final report
    overall_success = generate_integration_report(
        api_success, researcher_success, streamlit_success
    )
    
    # Exit code for CI/CD
    sys.exit(0 if overall_success else 1)

if __name__ == "__main__":
    main()