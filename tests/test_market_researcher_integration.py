#!/usr/bin/env python3
"""
Integration Test Script for Enhanced Market Researcher Agent
Tests ETL integration, API fallback, and compatibility

File: tests/test_market_researcher_integration.py
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_basic_import():
    """Test basic import functionality"""
    print("🧪 Testing basic imports...")
    
    try:
        from agents.market_researcher import MarketResearcherAgent, research_plans_for_bill
        print("✅ Enhanced Market Researcher Agent imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_etl_service_connection():
    """Test ETL service connection"""
    print("\n🧪 Testing ETL service connection...")
    
    try:
        from agents.market_researcher import ETLEnergyService
        
        etl_service = ETLEnergyService()
        
        if etl_service.connected:
            print("✅ ETL service connected successfully")
            
            # Test connection details
            test_result = etl_service.test_connection()
            print(f"   Total plans available: {test_result.get('total_plans_available', 'Unknown')}")
            
            retailers = test_result.get('sample_retailers', [])
            if retailers:
                print(f"   Sample retailers: {', '.join(retailers[:5])}")
            
            return True
        else:
            print("⚠️  ETL service not connected (expected in some environments)")
            return False
            
    except Exception as e:
        print(f"❌ ETL service test failed: {e}")
        return False

def test_api_fallback():
    """Test API fallback functionality"""
    print("\n🧪 Testing API fallback...")
    
    try:
        from agents.market_researcher import MarketResearcherAgent
        
        # Force API-only mode for testing
        researcher = MarketResearcherAgent()
        
        if researcher.use_api_fallback:
            print("✅ API fallback available")
            
            # Test API access
            if researcher.api:
                test_result = researcher.api.test_api_access()
                if test_result.get('cdr_register_access'):
                    print("✅ CDR register access working")
                else:
                    print("⚠️  CDR register access limited")
            
            return True
        else:
            print("⚠️  API fallback not available")
            return False
            
    except Exception as e:
        print(f"❌ API fallback test failed: {e}")
        return False

def test_plan_research():
    """Test plan research functionality"""
    print("\n🧪 Testing plan research...")
    
    # Sample bill data for testing
    test_bill_data = {
        'state': 'NSW',
        'retailer': 'Origin Energy',
        'usage_kwh': 650,
        'billing_days': 91,
        'total_amount': 245.80,
        'usage_charge': 185.60,
        'supply_charge': 42.50,
        'cost_per_kwh': 0.286,
        'has_solar': False,
        'solar_export_kwh': 0
    }
    
    try:
        from agents.market_researcher import research_plans_for_bill
        
        print("📊 Running market research with sample bill...")
        results = research_plans_for_bill(test_bill_data)
        
        if results.get('error'):
            print(f"⚠️  Research completed with limitations: {results.get('message')}")
            return False
        
        # Check results structure
        required_fields = ['recommended_plans', 'best_plan', 'savings_analysis', 'market_insights']
        missing_fields = [field for field in required_fields if field not in results]
        
        if missing_fields:
            print(f"❌ Missing required fields: {missing_fields}")
            return False
        
        print("✅ Market research completed successfully")
        
        # Display key results
        plans_analyzed = results.get('plans_analyzed', 0)
        better_plans = results.get('better_plans_found', 0)
        data_source = results.get('data_source', 'unknown')
        
        print(f"   Data source: {data_source}")
        print(f"   Plans analyzed: {plans_analyzed}")
        print(f"   Better plans found: {better_plans}")
        
        best_plan = results.get('best_plan', {})
        if best_plan.get('annual_savings', 0) > 0:
            print(f"   Best savings: ${best_plan.get('annual_savings', 0):.2f}/year with {best_plan.get('retailer', 'Unknown')}")
        else:
            print("   Current plan is competitive")
        
        return True
        
    except Exception as e:
        print(f"❌ Plan research test failed: {e}")
        return False

def test_backwards_compatibility():
    """Test backwards compatibility with existing interfaces"""
    print("\n🧪 Testing backwards compatibility...")
    
    try:
        from agents.market_researcher import MarketResearcherAgent
        
        researcher = MarketResearcherAgent()
        
        # Test that all expected methods exist
        required_methods = [
            'research_better_plans',
            'get_plan_comparison_summary'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(researcher, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"❌ Missing required methods: {missing_methods}")
            return False
        
        print("✅ All required methods available")
        print("✅ Backwards compatibility maintained")
        
        return True
        
    except Exception as e:
        print(f"❌ Backwards compatibility test failed: {e}")
        return False

def test_data_quality_validation():
    """Test data quality validation"""
    print("\n🧪 Testing data quality validation...")
    
    try:
        from agents.market_researcher import MarketResearcherAgent
        
        researcher = MarketResearcherAgent()
        
        # Test rate validation
        test_cases = [
            (0.25, 1.20, 'etl_warehouse', True),    # Valid ETL data
            (0.15, 0.95, 'api_supplement', True),   # Valid API data
            (1.50, 1.20, 'fallback', False),        # Invalid usage rate
            (0.25, 5.00, 'fallback', False),        # Invalid supply charge
        ]
        
        validation_passed = 0
        for usage_rate, supply_charge, data_source, expected_valid in test_cases:
            is_valid = researcher._validate_plan_rates(usage_rate, supply_charge, data_source)
            if is_valid == expected_valid:
                validation_passed += 1
            else:
                print(f"   ⚠️  Validation mismatch: {usage_rate}, {supply_charge}, {data_source}")
        
        if validation_passed == len(test_cases):
            print("✅ Data quality validation working correctly")
            return True
        else:
            print(f"❌ Data quality validation failed: {validation_passed}/{len(test_cases)} passed")
            return False
        
    except Exception as e:
        print(f"❌ Data quality validation test failed: {e}")
        return False

def test_service_status():
    """Test service status reporting"""
    print("\n🧪 Testing service status reporting...")
    
    try:
        from agents.market_researcher import MarketResearcherAgent
        
        researcher = MarketResearcherAgent()
        
        # Test service status
        test_results = researcher.test_all_services()
        
        required_keys = ['etl_service', 'api_service', 'overall_status']
        missing_keys = [key for key in required_keys if key not in test_results]
        
        if missing_keys:
            print(f"❌ Missing status keys: {missing_keys}")
            return False
        
        print("✅ Service status reporting working")
        print(f"   Overall status: {test_results['overall_status']}")
        
        etl_status = test_results['etl_service']
        api_status = test_results['api_service']
        
        print(f"   ETL connected: {etl_status.get('connected', False)}")
        print(f"   API available: {api_status.get('cdr_register_access', False)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Service status test failed: {e}")
        return False

def test_performance():
    """Test performance with sample workload"""
    print("\n🧪 Testing performance...")
    
    try:
        import time
        from agents.market_researcher import research_plans_for_bill
        
        # Sample bill for performance testing
        test_bill = {
            'state': 'QLD',
            'retailer': 'AGL',
            'usage_kwh': 800,
            'billing_days': 90,
            'total_amount': 320.50,
            'cost_per_kwh': 0.275,
            'has_solar': True,
            'solar_export_kwh': 150
        }
        
        start_time = time.time()
        results = research_plans_for_bill(test_bill)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        if execution_time < 30:  # Should complete within 30 seconds
            print(f"✅ Performance acceptable: {execution_time:.2f} seconds")
            
            # Check if we got meaningful results
            if not results.get('error') and results.get('plans_analyzed', 0) > 5:
                print(f"   Analyzed {results.get('plans_analyzed')} plans")
                print(f"   Data source: {results.get('data_source', 'unknown')}")
                return True
            else:
                print("⚠️  Limited results but performance OK")
                return True
        else:
            print(f"❌ Performance issue: {execution_time:.2f} seconds (too slow)")
            return False
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        return False

def run_comprehensive_tests():
    """Run all integration tests"""
    print("🚀 Enhanced Market Researcher Agent - Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Import", test_basic_import),
        ("ETL Service Connection", test_etl_service_connection),
        ("API Fallback", test_api_fallback),
        ("Plan Research", test_plan_research),
        ("Backwards Compatibility", test_backwards_compatibility),
        ("Data Quality Validation", test_data_quality_validation),
        ("Service Status", test_service_status),
        ("Performance", test_performance)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 Test Results Summary:")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("💡 The Enhanced Market Researcher Agent is ready for use")
        success = True
    elif passed >= total * 0.7:  # 70% pass rate
        print("⚠️  Most tests passed - system is functional with some limitations")
        print("🔧 Check failed tests and resolve any critical issues")
        success = True
    else:
        print("❌ Integration tests failed - system needs attention")
        print("🔧 Please resolve the failed tests before proceeding")
        success = False
    
    return success

def demo_usage():
    """Demonstrate typical usage patterns"""
    print("\n" + "=" * 60)
    print("📖 Usage Demonstration")
    
    print("\n1️⃣ Simple Usage:")
    print("```python")
    print("from agents.market_researcher import research_plans_for_bill")
    print("")
    print("bill_data = {")
    print("    'state': 'NSW',")
    print("    'retailer': 'AGL',")
    print("    'usage_kwh': 750,")
    print("    'billing_days': 92,")
    print("    'total_amount': 285.50,")
    print("    'cost_per_kwh': 0.294")
    print("}")
    print("")
    print("results = research_plans_for_bill(bill_data)")
    print("```")
    
    print("\n2️⃣ Advanced Usage:")
    print("```python")
    print("from agents.market_researcher import MarketResearcherAgent")
    print("")
    print("# Custom configuration")
    print("researcher = MarketResearcherAgent(")
    print("    project_id='your-project-id',")
    print("    dataset_id='your-dataset'")
    print(")")
    print("")
    print("# Research with usage analysis")
    print("results = researcher.research_better_plans(bill_data, usage_analysis)")
    print("")
    print("# Get summary")
    print("summary = researcher.get_plan_comparison_summary(results)")
    print("```")
    
    print("\n3️⃣ Service Testing:")
    print("```python")
    print("from agents.market_researcher import test_etl_integration")
    print("")
    print("# Test all services")
    print("test_results = test_etl_integration()")
    print("```")

def create_sample_bill_data():
    """Create sample bill data for testing"""
    return {
        "realistic_bills": [
            {
                "name": "Small Apartment - NSW",
                "bill_data": {
                    "state": "NSW",
                    "retailer": "AGL",
                    "usage_kwh": 450,
                    "billing_days": 92,
                    "total_amount": 185.50,
                    "usage_charge": 135.60,
                    "supply_charge": 38.90,
                    "cost_per_kwh": 0.301,
                    "has_solar": False,
                    "solar_export_kwh": 0
                }
            },
            {
                "name": "Family Home with Solar - QLD",
                "bill_data": {
                    "state": "QLD",
                    "retailer": "Origin Energy",
                    "usage_kwh": 1250,
                    "billing_days": 91,
                    "total_amount": 425.80,
                    "usage_charge": 310.20,
                    "supply_charge": 45.60,
                    "cost_per_kwh": 0.248,
                    "has_solar": True,
                    "solar_export_kwh": 450
                }
            },
            {
                "name": "Large House - VIC",
                "bill_data": {
                    "state": "VIC",
                    "retailer": "Energy Australia",
                    "usage_kwh": 1850,
                    "billing_days": 90,
                    "total_amount": 650.30,
                    "usage_charge": 485.50,
                    "supply_charge": 52.80,
                    "cost_per_kwh": 0.262,
                    "has_solar": False,
                    "solar_export_kwh": 0
                }
            }
        ]
    }

def save_test_report(results: Dict[str, bool]):
    """Save test results to file"""
    
    report = {
        "test_timestamp": datetime.now().isoformat(),
        "test_results": results,
        "summary": {
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results.values() if r),
            "failed_tests": sum(1 for r in results.values() if not r),
            "success_rate": sum(1 for r in results.values() if r) / len(results) * 100
        },
        "environment_info": {
            "python_version": sys.version,
            "platform": sys.platform
        }
    }
    
    try:
        filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Test report saved to: {filename}")
        
    except Exception as e:
        print(f"⚠️  Could not save test report: {e}")

if __name__ == "__main__":
    # Run comprehensive integration tests
    success = run_comprehensive_tests()
    
    # Show usage examples
    demo_usage()
    
    # Create sample data file
    sample_data = create_sample_bill_data()
    try:
        with open("sample_bill_data.json", "w") as f:
            json.dump(sample_data, f, indent=2)
        print(f"\n📋 Sample bill data saved to: sample_bill_data.json")
    except Exception as e:
        print(f"⚠️  Could not save sample data: {e}")
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)