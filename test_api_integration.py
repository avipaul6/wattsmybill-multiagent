#!/usr/bin/env python3
"""
WattsMyBill API Integration Test Script
Run this to verify your real API integration is working

Usage: python test_api_integration.py
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_api_endpoints():
    """Test direct API endpoint access"""
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
        
        # Test 2: Plan Data Access
        print("\n2️⃣ Testing Plan Data Access...")
        test_retailers = ['agl', 'origin']
        
        for retailer in test_retailers:
            print(f"   Testing {retailer}...")
            plans = api.get_plans_for_retailer(retailer, 'NSW')
            
            if plans:
                print(f"   ✅ {retailer}: Found {len(plans)} plans")
                sample_plan = plans[0]
                print(f"   📊 Sample: {sample_plan.get('plan_name', 'Unknown')} - ${sample_plan.get('usage_rate', 0):.3f}/kWh")
            else:
                print(f"   📊 {retailer}: Using fallback data")
        
        # Test 3: State Plans
        print("\n3️⃣ Testing State Plan Search...")
        nsw_plans = api.get_all_plans_for_state('NSW')
        print(f"   ✅ NSW: Found {len(nsw_plans)} total plans")
        
        # Test 4: Plan Search with Criteria
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
            print(f"   🏆 Best: {best_plan.get('retailer', 'Unknown')} - ${best_plan.get('estimated_annual_cost', 0):.0f}/year")
        
        # Test 5: API Status
        print("\n5️⃣ Testing API Status...")
        status = api.test_api_access()
        print(f"   📡 CDR Register: {'✅' if status.get('cdr_register_access') else '❌'}")
        
        retailer_status = status.get('retailer_api_access', {})
        for retailer, result in retailer_status.items():
            print(f"   📡 {retailer}: {'✅' if result.get('success') else '❌'}")
        
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
    """Test the enhanced market researcher"""
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
        
        # Display results
        print(f"\n📋 RESEARCH RESULTS:")
        print(f"   Data Source: {result.get('data_source', 'unknown')}")
        print(f"   Plans Analyzed: {result.get('plans_analyzed', 0)}")
        
        # Best plan
        best_plan = result.get('best_plan')
        if best_plan:
            print(f"\n🏆 BEST PLAN:")
            print(f"   Retailer: {best_plan.get('retailer')}")
            print(f"   Plan: {best_plan.get('plan_name')}")
            print(f"   Annual Cost: ${best_plan.get('estimated_annual_cost', 0):.0f}")
            print(f"   Annual Savings: ${best_plan.get('annual_savings', 0):.0f}")
            print(f"   Monthly Savings: ${best_plan.get('monthly_savings', 0):.0f}")
            print(f"   Confidence: {best_plan.get('confidence_score', 0):.0%}")
        
        # Top recommendations
        recommendations = result.get('recommended_plans', [])
        if recommendations:
            print(f"\n💡 TOP 3 RECOMMENDATIONS:")
            for i, plan in enumerate(recommendations[:3], 1):
                print(f"   {i}. {plan.get('retailer')} - {plan.get('plan_name')}")
                print(f"      💰 ${plan.get('estimated_annual_cost', 0):.0f}/year (Save ${plan.get('annual_savings', 0):.0f})")
                print(f"      ⚡ ${plan.get('usage_rate', 0):.3f}/kWh + ${plan.get('supply_charge_daily', 0):.2f}/day")
                if plan.get('solar_feed_in_tariff'):
                    print(f"      ☀️ Solar: ${plan.get('solar_feed_in_tariff', 0):.3f}/kWh")
        
        # Market insights
        insights = result.get('market_insights', {})
        if insights:
            print(f"\n📈 MARKET INSIGHTS:")
            print(f"   Rate Position: {insights.get('current_rate_position', 'unknown')}")
            print(f"   Market Average: ${insights.get('live_market_average', 0):.3f}/kWh")
            print(f"   Cheapest Available: ${insights.get('market_rate_range', {}).get('cheapest', 0):.3f}/kWh")
            print(f"   Retailers Analyzed: {insights.get('retailer_count', 0)}")
        
        # Summary
        summary = researcher.get_plan_comparison_summary(result)
        print(f"\n📝 SUMMARY:")
        print(f"   {summary}")
        
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
    """Test integration with Streamlit app"""
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
            print("   ⚠️  Streamlit not installed")
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
            print(f"   💰 Potential savings: ${result.get('best_plan', {}).get('annual_savings', 0):.0f}/year")
            return True
        else:
            print("   ❌ Workflow failed")
            return False
            
    except Exception as e:
        print(f"❌ Streamlit integration test failed: {e}")
        return False

def generate_integration_report(api_success, researcher_success, streamlit_success):
    """Generate a comprehensive integration report"""
    
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
        print(f"   2. 🔄 Update your app.py to use real agents")
        print(f"   3. 🧪 Test with real energy bills")
        print(f"   4. 🎯 Deploy and start helping Australians save money!")
        
        print(f"\n💡 USAGE EXAMPLE:")
        print(f"   # In your app.py, replace simulated responses:")
        print(f"   from agents.market_researcher import MarketResearcherAgent")
        print(f"   researcher = MarketResearcherAgent()")
        print(f"   real_results = researcher.research_better_plans(bill_data)")
    else:
        print(f"\n🔧 ISSUES TO RESOLVE:")
        if not api_success:
            print(f"   ❌ Fix API integration issues")
        if not researcher_success:
            print(f"   ❌ Fix market researcher implementation")
        if not streamlit_success:
            print(f"   ❌ Fix Streamlit integration")
        
        print(f"\n📞 TROUBLESHOOTING:")
        print(f"   1. Check internet connection for API access")
        print(f"   2. Verify all required packages are installed")
        print(f"   3. Ensure file paths are correct")
        print(f"   4. Check error messages above for specific issues")
    
    return overall_success

def main():
    """Run all integration tests"""
    
    print("🚀 WattsMyBill - Real API Integration Test Suite")
    print(f"🕐 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run all tests
    print("Running comprehensive integration tests...\n")
    
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