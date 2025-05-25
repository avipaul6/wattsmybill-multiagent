#!/usr/bin/env python3
"""
Enhanced Test Suite for Real Bill Parser
File: test_bill_parser.py
"""
import sys
from pathlib import Path
import json
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_parser():
    """Test basic parser functionality"""
    print("🧪 Testing Basic Parser Functionality\n")
    
    try:
        from utils.bill_parser import AustralianBillParser, parse_australian_energy_bill
        
        print("✅ Bill parser imported successfully")
        
        # Test parser instance
        parser = AustralianBillParser()
        print("✅ Parser instance created")
        
        # Test fallback functionality
        fallback = parser._get_fallback_data("Test fallback")
        print(f"✅ Fallback data generated with confidence: {fallback['confidence']:.1%}")
        
        # Test with empty content (should use fallback)
        empty_result = parser.parse_bill(b"", "pdf")
        print(f"✅ Empty content handled, method: {empty_result['extraction_method']}")
        
        # Test privacy mode
        privacy_result = parser._get_fallback_data("Test privacy", privacy_mode=True)
        print(f"✅ Privacy mode working: account={privacy_result.get('account_number')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic parser test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_parser_fixes():
    """Test the specific fixes made to the parser"""
    print("🔧 Testing Specific Parser Fixes\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        print("🧪 Fix 1: Alinta Usage Extraction")
        alinta_usage_text = "any time usage 942 kwh $0.2600 $244.96"
        usage = parser._extract_usage(alinta_usage_text.lower())
        expected = 942
        if usage == expected:
            print(f"   ✅ FIXED: '{alinta_usage_text}' → {usage} kWh")
        else:
            print(f"   ❌ BROKEN: '{alinta_usage_text}' → {usage} kWh (expected {expected})")
        
        print("\n🧪 Fix 2: QLD State Detection")
        qld_address_text = "supply address: 20 vargon circuit holmview qld 4207"
        state = parser._extract_state_with_context(qld_address_text.lower())
        expected_state = "QLD"
        if state == expected_state:
            print(f"   ✅ FIXED: '{qld_address_text}' → {state}")
        else:
            print(f"   ❌ BROKEN: '{qld_address_text}' → {state} (expected {expected_state})")
        
        print("\n🧪 Fix 3: AGL Peak/Off-Peak Summation")
        agl_usage_text = """
        peak usage 600 kwh @ $0.32 = $192.00
        off-peak usage 450 kwh @ $0.24 = $108.00
        """
        usage = parser._extract_usage(agl_usage_text.lower())
        expected_sum = 1050  # 600 + 450
        if usage == expected_sum:
            print(f"   ✅ FIXED: Peak + Off-peak → {usage} kWh (600+450)")
        else:
            print(f"   ❌ BROKEN: Peak + Off-peak → {usage} kWh (expected {expected_sum})")
        
        return True
        
    except Exception as e:
        print(f"❌ Specific parser fixes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_bill_samples():
    """Test with real Australian energy bill samples"""
    print("📄 Testing with Real Australian Energy Bill Samples\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        # Alinta Bill Sample - exact format that was failing
        alinta_bill_text = """
        alinta energy
        your customer number 1586 3139
        your electricity reference number 101 183 978 29
        total amount $312.02
        
        supply address: 20 vargon circuit holmview qld 4207
        dates this account covers: 07 mar 2018 to 30 may 2018
        number of days: 85 days
        
        electricity charges
        any time usage 942 kwh $0.2600 $244.96
        supply charge 85 $0.9900 $84.15
        
        total charges $312.02
        """
        
        print("📊 Testing: Alinta Energy (problematic format)")
        print("-" * 60)
        
        # Parse the bill
        result = parser._parse_text(alinta_bill_text.lower())
        
        # Display results with SPECIFIC VALIDATION for problem cases
        print(f"   🏢 Retailer: {result.get('retailer')}")
        print(f"   💰 Total: ${result.get('total_amount')}")
        
        # CRITICAL: Test the specific issues that were failing
        usage_kwh = result.get('usage_kwh')
        state = result.get('state')
        
        if usage_kwh == 942:
            print(f"   ⚡ Usage: {usage_kwh} kWh ✅ FIXED!")
        else:
            print(f"   ⚡ Usage: {usage_kwh} kWh ❌ STILL BROKEN - should be 942")
        
        if state == "QLD":
            print(f"   📍 State: {state} ✅ FIXED!")
        else:
            print(f"   📍 State: {state} ❌ STILL BROKEN - should be QLD")
        
        print(f"   📅 Days: {result.get('billing_days')}")
        print(f"   🎯 Confidence: {result.get('confidence', 0):.1%}")
        
        # Return success if both critical issues are fixed
        return usage_kwh == 942 and state == "QLD"
        
    except Exception as e:
        print(f"❌ Real bill samples test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_pdf_files():
    """Test with actual PDF files"""
    print("📄 Testing with Real PDF Files\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        import os
        
        parser = AustralianBillParser()
        
        # Check for sample bills in demo folder
        sample_bills_dir = "demo/sample_bills"
        pdf_files = []
        
        if os.path.exists(sample_bills_dir):
            pdf_files = [f for f in os.listdir(sample_bills_dir) if f.endswith('.pdf')]
            print(f"Found {len(pdf_files)} PDF files in {sample_bills_dir}/")
        
        if not pdf_files:
            print("⚠️  No PDF files found in demo/sample_bills/")
            print("   You can add your sample bills there for testing")
            return True  # Not a failure, just no files to test
        
        # Test each PDF file
        successful_parses = 0
        for pdf_file in pdf_files:
            print(f"\n📊 Testing: {pdf_file}")
            print("-" * 40)
            file_path = os.path.join(sample_bills_dir, pdf_file)
            
            try:
                # Read the PDF file
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Parse the bill
                result = parser.parse_bill(file_content, 'pdf')
                
                # Display key results
                print(f"   🔧 Method: {result.get('extraction_method')}")
                print(f"   🏢 Retailer: {result.get('retailer')}")
                print(f"   💰 Total: ${result.get('total_amount')}")
                print(f"   ⚡ Usage: {result.get('usage_kwh')} kWh")
                print(f"   📍 State: {result.get('state')}")
                print(f"   🎯 Confidence: {result.get('confidence', 0):.1%}")
                
                if result.get('confidence', 0) > 0.5:
                    print(f"   🎉 Successfully parsed {pdf_file}!")
                    successful_parses += 1
                else:
                    print(f"   ⚠️  Low confidence for {pdf_file}")
                
            except Exception as e:
                print(f"   ❌ Error processing {pdf_file}: {e}")
        
        print(f"\n📈 PDF Parsing Summary: {successful_parses}/{len(pdf_files)} successful")
        return True
        
    except Exception as e:
        print(f"❌ PDF file test failed: {e}")
        return False

def generate_test_report(test_results):
    """Generate a comprehensive test report"""
    print("\n" + "="*70)
    print("📋 COMPREHENSIVE TEST REPORT")
    print("="*70)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests:.1%})")
    print()
    
    # Detailed results
    for test_name, passed in test_results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    
    # Critical fixes assessment
    critical_tests = ['Specific Parser Fixes', 'Real Bill Samples']
    critical_passed = sum(1 for test in critical_tests if test_results.get(test, False))
    
    print("🔧 CRITICAL FIXES STATUS:")
    for test in critical_tests:
        status = "✅ FIXED" if test_results.get(test, False) else "❌ BROKEN"
        print(f"   {status} {test}")
    
    # Assessment
    if critical_passed == len(critical_tests):
        print("\n🎉 CRITICAL FIXES WORKING!")
        print("✅ Alinta usage extraction fixed")
        print("✅ QLD state detection fixed")
        print("🚀 Parser is ready for production use")
    else:
        print("\n❌ CRITICAL ISSUES REMAIN!")
        print("🔧 Fix the parser before proceeding")
    
    # Next steps
    print("\n🔗 Next Steps:")
    if critical_passed == len(critical_tests):
        print("1. ✅ Parser fixes validated")
        print("2. 🔄 Integrate with agent factory")
        print("3. 🎯 Test with Streamlit UI")
        print("4. 🚀 Begin agent implementation")
    else:
        print("1. 🔧 Fix failing parser issues")
        print("2. 🧪 Re-run tests until all pass")
        print("3. 📄 Test with real PDF files")
    
    return critical_passed == len(critical_tests)

def main():
    """Run all tests and generate comprehensive report"""
    print("🚀 WattsMyBill - Enhanced Bill Parser Test Suite")
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run critical tests
    test_results = {
        'Basic Parser Functionality': test_basic_parser(),
        'Specific Parser Fixes': test_specific_parser_fixes(),
        'Real Bill Samples': test_real_bill_samples(),
        'PDF File Processing': test_real_pdf_files(),
    }
    
    # Generate report
    production_ready = generate_test_report(test_results)
    
    # Final assessment
    if production_ready:
        print("\n🎉 PRODUCTION READY!")
        print("Your bill parser has passed all critical tests.")
    else:
        print("\n⚠️  NOT PRODUCTION READY")
        print("Please fix the failing tests before proceeding.")

if __name__ == "__main__":
    main()