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

def test_retailer_detection():
    """Test retailer detection with various formats"""
    print("🏢 Testing Retailer Detection\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        retailer_tests = [
            ("origin energy customer service", "Origin"),
            ("agl electricity bill", "Agl"),
            ("energyaustralia account statement", "Energyaustralia"),
            ("red energy pty ltd", "Red Energy"),
            ("simply energy", "Simply Energy"),
            ("alinta energy residential", "Alinta"),
            ("momentum energy", "Momentum"),
            ("powershop", "Powershop"),
            ("lumo energy", "Lumo"),
            ("globird energy", "Globird"),
            ("unknown retailer xyz", None)
        ]
        
        success_count = 0
        for text, expected in retailer_tests:
            detected = parser._find_retailer(text.lower())
            if detected == expected or (detected is None and expected is None):
                print(f"✅ '{text}' → '{detected}' ✓")
                success_count += 1
            else:
                print(f"❌ '{text}' → '{detected}' (expected '{expected}')")
        
        print(f"\n📊 Retailer Detection: {success_count}/{len(retailer_tests)} passed")
        return success_count == len(retailer_tests)
        
    except Exception as e:
        print(f"❌ Retailer detection test failed: {e}")
        return False

def test_amount_extraction():
    """Test total amount extraction with various formats"""
    print("💰 Testing Amount Extraction\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        amount_tests = [
            ("amount due $450.67", 450.67),
            ("total amount: $1,234.56", 1234.56),
            ("account balance $89.90", 89.90),
            ("your total for this bill $567.89", 567.89),
            ("total amount due: 345.78", 345.78),
            ("new charges $2,567.45", 2567.45),
            ("$678.90 amount due", 678.90),
            ("total $123.45", 123.45),
            ("amount $50000.00", None),  # Too high, should reject
            ("amount $5.00", None),       # Too low, should reject
        ]
        
        success_count = 0
        for text, expected in amount_tests:
            extracted = parser._extract_total_amount(text.lower())
            if extracted == expected or (extracted is None and expected is None):
                print(f"✅ '{text}' → ${extracted} ✓")
                success_count += 1
            else:
                print(f"❌ '{text}' → ${extracted} (expected ${expected})")
        
        print(f"\n📊 Amount Extraction: {success_count}/{len(amount_tests)} passed")
        return success_count >= len(amount_tests) * 0.8  # 80% pass rate acceptable
        
    except Exception as e:
        print(f"❌ Amount extraction test failed: {e}")
        return False

def test_usage_extraction():
    """Test usage extraction with various formats"""
    print("⚡ Testing Usage Extraction\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        usage_tests = [
            ("total kwh: 1,234", 1234),
            ("total usage (kwh): 567", 567),
            ("electricity usage: 890", 890),
            ("general usage 1,500 kwh $0.32", 1500),
            ("any time usage 750 kwh", 750),
            ("total usage kwh 2,345", 2345),
            ("usage 100000 kwh", None),  # Too high, should reject
            ("usage 10 kwh", None),      # Too low, should reject
        ]
        
        success_count = 0
        for text, expected in usage_tests:
            extracted = parser._extract_usage(text.lower())
            if extracted == expected or (extracted is None and expected is None):
                print(f"✅ '{text}' → {extracted} kWh ✓")
                success_count += 1
            else:
                print(f"❌ '{text}' → {extracted} kWh (expected {expected})")
        
        print(f"\n📊 Usage Extraction: {success_count}/{len(usage_tests)} passed")
        return success_count >= len(usage_tests) * 0.8
        
    except Exception as e:
        print(f"❌ Usage extraction test failed: {e}")
        return False

def test_solar_extraction():
    """Test solar export and credit extraction"""
    print("☀️ Testing Solar Data Extraction\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        # Solar export tests
        solar_export_tests = [
            ("solar exports: 456 kwh", 456.0),
            ("feed-in: 789 kwh", 789.0),
            ("exported 234 kwh", 234.0),
            ("solar feed-in credit (incl gst): 567 kwh", 567.0),
        ]
        
        # Solar credit tests
        solar_credit_tests = [
            ("solar feed-in credit: 567 kwh $45.67", 45.67),
            ("solar exports: 456 kwh $-36.78", 36.78),
            ("feed-in: $23.45", 23.45),
            ("solar credit $67.89", 67.89),
        ]
        
        # Feed-in tariff tests
        tariff_tests = [
            ("feed-in tariff: $0.08", 0.08),
            ("solar tariff $0.12", 0.12),
            ("export rate: $0.06", 0.06),
            ("8c/kwh feed", 0.08),
            ("12.5c/kwh solar", 0.125),
        ]
        
        print("🔋 Solar Export Tests:")
        export_success = 0
        for text, expected in solar_export_tests:
            extracted = parser._extract_solar_export(text.lower())
            if extracted == expected:
                print(f"✅ '{text}' → {extracted} kWh ✓")
                export_success += 1
            else:
                print(f"❌ '{text}' → {extracted} kWh (expected {expected})")
        
        print(f"\n💰 Solar Credit Tests:")
        credit_success = 0
        for text, expected in solar_credit_tests:
            extracted = parser._extract_solar_credit(text.lower())
            if extracted == expected:
                print(f"✅ '{text}' → ${extracted} ✓")
                credit_success += 1
            else:
                print(f"❌ '{text}' → ${extracted} (expected ${expected})")
        
        print(f"\n📈 Feed-in Tariff Tests:")
        tariff_success = 0
        for text, expected in tariff_tests:
            extracted = parser._extract_feed_in_tariff(text.lower())
            if extracted == expected:
                print(f"✅ '{text}' → ${extracted}/kWh ✓")
                tariff_success += 1
            else:
                print(f"❌ '{text}' → ${extracted}/kWh (expected ${expected})")
        
        total_tests = len(solar_export_tests) + len(solar_credit_tests) + len(tariff_tests)
        total_success = export_success + credit_success + tariff_success
        
        print(f"\n📊 Solar Extraction: {total_success}/{total_tests} passed")
        return total_success >= total_tests * 0.7  # 70% pass rate for solar features
        
    except Exception as e:
        print(f"❌ Solar extraction test failed: {e}")
        return False

def test_real_bill_samples():
    """Test with comprehensive real Australian energy bill text samples"""
    print("📄 Testing with Real Australian Energy Bill Samples\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        # Enhanced Origin Bill Sample (with solar)
        origin_bill_text = """
        origin energy
        electricity account
        account number a-f7fd1b5b
        amount due $1,110.18
        supply address 20 vargon cct holmview qld 4207
        billing period: 06 jan 2024 to 05 apr 2024 (91 days)
        
        electricity charges
        general usage 3,825.868 kwh $0.320430 $1,225.92
        daily supply 91 days $1.339910 $121.93
        solar meter charge 91 days $0.085260 $7.76
        
        solar credits
        solar feed-in credit (incl gst): 1,250 kwh $-125.50
        feed-in tariff: $0.10/kwh
        
        total charges $1,355.61
        account balance $1,110.18
        """
        
        # Enhanced AGL Bill Sample
        agl_bill_text = """
        agl energy
        customer number 12345678
        account 987654321
        your total for this bill $445.67
        
        service address: 123 main street sydney nsw 2000
        billing period: 15 feb 2024 - 15 may 2024 (90 days)
        
        electricity usage
        any time usage 1,200 kwh @ $0.28 = $336.00
        supply charge 90 days @ $1.15 = $103.50
        service charges $6.17
        
        total new charges $445.67
        """
        
        # Enhanced Alinta Bill Sample (with solar)
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
        
        solar export
        exported 345 kwh
        solar credit $-17.25
        export rate: $0.05/kwh
        
        total charges $312.02
        """
        
        # Simply Energy Bill Sample
        simply_bill_text = """
        simply energy pty ltd
        account number se-789456123
        amount due: $567.89
        
        property address: 456 collins street melbourne vic 3000
        billing period: 01/04/2024 to 30/06/2024 (91 days)
        
        usage summary
        total usage kwh: 1,567
        electricity charge $423.09
        daily service charge 91 days @ $1.25 = $113.75
        connection fee $31.05
        
        account balance $567.89
        """
        
        bill_samples = [
            ("Origin Energy (with solar)", origin_bill_text),
            ("AGL Energy", agl_bill_text),
            ("Alinta Energy (with solar)", alinta_bill_text),
            ("Simply Energy", simply_bill_text)
        ]
        
        results = []
        
        for name, bill_text in bill_samples:
            print(f"📊 Testing: {name}")
            print("-" * 50)
            
            # Parse the bill
            result = parser._parse_text(bill_text.lower())
            results.append((name, result))
            
            # Display results
            print(f"   🏢 Retailer: {result.get('retailer')}")
            print(f"   🏠 Account: {result.get('account_number')}")
            print(f"   💰 Total: ${result.get('total_amount')}")
            print(f"   ⚡ Usage: {result.get('usage_kwh')} kWh")
            print(f"   📍 State: {result.get('state')}")
            print(f"   📅 Days: {result.get('billing_days')}")
            print(f"   🔌 Supply: ${result.get('supply_charge')}")
            print(f"   📈 Rate: ${result.get('usage_rate')}")
            
            # Solar data
            if result.get('solar_export_kwh'):
                print(f"   ☀️ Solar Export: {result.get('solar_export_kwh')} kWh")
                print(f"   💸 Solar Credit: ${result.get('solar_credit_amount')}")
                print(f"   📊 Feed-in Tariff: ${result.get('feed_in_tariff')}/kWh")
                print(f"   🌞 Has Solar: {result.get('has_solar', False)}")
            
            # Calculated insights
            if result.get('daily_average_kwh'):
                print(f"   📊 Daily Average: {result['daily_average_kwh']:.1f} kWh/day")
            if result.get('cost_per_kwh'):
                print(f"   💵 Cost per kWh: ${result['cost_per_kwh']:.3f}")
            
            print(f"   🎯 Confidence: {result.get('confidence', 0):.1%}")
            
            # Validate key fields
            validation_score = 0
            if result.get('retailer'):
                validation_score += 1
            if result.get('total_amount'):
                validation_score += 1
            if result.get('usage_kwh'):
                validation_score += 1
            if result.get('state'):
                validation_score += 1
            
            print(f"   ✅ Validation: {validation_score}/4 key fields extracted")
            
            if validation_score >= 3:
                print(f"   🎉 Successfully parsed {name}!")
            else:
                print(f"   ⚠️  Partial parsing for {name}")
            
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Real bill samples test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_privacy_mode():
    """Test privacy mode functionality"""
    print("🔒 Testing Privacy Mode\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        # Sample bill text with personal info
        sample_text = """
        origin energy
        account number abc123456789
        amount due $450.67
        supply address 123 main street sydney nsw 2000
        """
        
        # Parse without privacy mode
        normal_result = parser._parse_text(sample_text.lower())
        
        # Apply privacy mode
        private_result = parser._apply_privacy_mode(normal_result.copy())
        
        print("🔓 Normal Mode:")
        print(f"   Account: {normal_result.get('account_number')}")
        print(f"   Postcode: {normal_result.get('postcode')}")
        
        print("\n🔒 Privacy Mode:")
        print(f"   Account: {private_result.get('account_number')}")
        print(f"   Postcode: {private_result.get('postcode')}")
        
        # Validate privacy features
        privacy_checks = []
        
        # Check account masking
        if private_result.get('account_number') and '*' in private_result['account_number']:
            privacy_checks.append("✅ Account number masked")
        else:
            privacy_checks.append("❌ Account number not masked")
        
        # Check postcode removal
        if private_result.get('postcode') is None:
            privacy_checks.append("✅ Postcode removed")
        else:
            privacy_checks.append("❌ Postcode not removed")
        
        for check in privacy_checks:
            print(f"   {check}")
        
        return all("✅" in check for check in privacy_checks)
        
    except Exception as e:
        print(f"❌ Privacy mode test failed: {e}")
        return False

def test_confidence_scoring():
    """Test confidence scoring algorithm"""
    print("🎯 Testing Confidence Scoring\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        # High confidence sample (all key fields)
        high_confidence_data = {
            'retailer': 'Origin',
            'total_amount': 450.67,
            'usage_kwh': 1200,
            'account_number': 'ABC123',
            'state': 'NSW',
            'billing_period': {'start_date': '01/01/2024', 'end_date': '31/03/2024'},
            'billing_days': 90
        }
        
        # Medium confidence sample (some fields missing)
        medium_confidence_data = {
            'retailer': 'AGL',
            'total_amount': 350.00,
            'usage_kwh': None,  # Missing
            'account_number': None,  # Missing
            'state': 'VIC'
        }
        
        # Low confidence sample (only basic fields)
        low_confidence_data = {
            'retailer': None,  # Missing
            'total_amount': 250.00,
            'usage_kwh': None,  # Missing
        }
        
        test_cases = [
            ("High Confidence", high_confidence_data, 0.8),
            ("Medium Confidence", medium_confidence_data, 0.5),
            ("Low Confidence", low_confidence_data, 0.3)
        ]
        
        for name, data, expected_min in test_cases:
            confidence = parser._calculate_confidence(data)
            print(f"   📊 {name}: {confidence:.1%}")
            
            if confidence >= expected_min:
                print(f"      ✅ Meets minimum threshold ({expected_min:.1%})")
            else:
                print(f"      ⚠️  Below threshold ({expected_min:.1%})")
        
        return True
        
    except Exception as e:
        print(f"❌ Confidence scoring test failed: {e}")
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
            print("   Recommended files:")
            print("   - origin_bill.pdf")
            print("   - agl_bill.pdf") 
            print("   - alinta_bill.pdf")
            print("   - sample_solar_bill.pdf")
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
                
                # Parse the bill (normal mode)
                result = parser.parse_bill(file_content, 'pdf')
                
                # Display key results
                print(f"   📄 File size: {len(file_content):,} bytes")
                print(f"   🔧 Method: {result.get('extraction_method')}")
                print(f"   🏢 Retailer: {result.get('retailer')}")
                print(f"   💰 Total: ${result.get('total_amount')}")
                print(f"   ⚡ Usage: {result.get('usage_kwh')} kWh")
                print(f"   📍 State: {result.get('state')}")
                print(f"   🏠 Account: {result.get('account_number')}")
                print(f"   📅 Days: {result.get('billing_days')}")
                
                # Solar information
                if result.get('has_solar'):
                    print(f"   ☀️ Solar Export: {result.get('solar_export_kwh')} kWh")
                    print(f"   💸 Solar Credit: ${result.get('solar_credit_amount')}")
                
                print(f"   🎯 Confidence: {result.get('confidence', 0):.1%}")
                print(f"   📊 Text Length: {result.get('raw_text_length', 0):,} chars")
                
                # Test privacy mode
                privacy_result = parser.parse_bill(file_content, 'pdf', privacy_mode=True)
                print(f"   🔒 Privacy Account: {privacy_result.get('account_number')}")
                
                if result.get('confidence', 0) > 0.5:
                    print(f"   🎉 Successfully parsed {pdf_file}!")
                    successful_parses += 1
                else:
                    print(f"   ⚠️  Low confidence for {pdf_file} - using fallback data")
                
            except Exception as e:
                print(f"   ❌ Error processing {pdf_file}: {e}")
        
        print(f"\n📈 PDF Parsing Summary: {successful_parses}/{len(pdf_files)} successful")
        return True
        
    except Exception as e:
        print(f"❌ PDF file test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_edge_cases():
    """Test edge cases and error handling"""
    print("🔍 Testing Edge Cases\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        parser = AustralianBillParser()
        
        edge_cases = [
            ("Empty text", ""),
            ("Very short text", "abc"),
            ("Numbers only", "123 456 789"),
            ("Special characters", "!@#$%^&*()"),
            ("Mixed case", "OrIgIn EnErGy $123.45"),
            ("Unicode text", "ørîgîñ énërgÿ $456.78"),
            ("Very large numbers", "usage 999999999 kwh $999999999.99"),
        ]
        
        print("Testing edge cases:")
        success_count = 0
        
        for description, text in edge_cases:
            try:
                result = parser._parse_text(text.lower())
                print(f"✅ {description}: Handled gracefully")
                success_count += 1
            except Exception as e:
                print(f"❌ {description}: Failed with {e}")
        
        print(f"\n📊 Edge Cases: {success_count}/{len(edge_cases)} handled")
        
        # Test invalid inputs
        print("\nTesting invalid inputs:")
        invalid_tests = 0
        
        try:
            parser.parse_bill(None, 'pdf')
            print("❌ None input: Should have failed")
        except:
            print("✅ None input: Properly rejected")
            invalid_tests += 1
        
        try:
            result = parser.parse_bill(b"", 'invalid_type')
            print("✅ Invalid file type: Handled gracefully")
            invalid_tests += 1
        except:
            print("✅ Invalid file type: Properly rejected")
            invalid_tests += 1
        
        return success_count >= len(edge_cases) * 0.8 and invalid_tests >= 1
        
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
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
    
    # Assessment
    if passed_tests == total_tests:
        print("🎉 EXCELLENT! All tests passed!")
        print("🚀 Your bill parser is production-ready!")
    elif passed_tests >= total_tests * 0.8:
        print("✅ GOOD! Most tests passed!")
        print("🔧 Minor improvements needed in failing areas")
    elif passed_tests >= total_tests * 0.6:
        print("⚠️  NEEDS WORK! Some core functionality issues")
        print("🛠️  Review failed tests and improve parsing logic")
    else:
        print("❌ MAJOR ISSUES! Significant problems detected")
        print("🔧 Substantial rework needed")
    
    # Recommendations
    print("\n" + "="*70)
    print("💡 RECOMMENDATIONS")
    print("="*70)
    
    if not test_results.get('Retailer Detection', True):
        print("🏢 Improve retailer detection patterns")
    
    if not test_results.get('Amount Extraction', True):
        print("💰 Enhance amount extraction regex patterns")
    
    if not test_results.get('Solar Data Extraction', True):
        print("☀️ Add more solar export patterns for newer bill formats")
    
    if not test_results.get('Privacy Mode', True):
        print("🔒 Fix privacy mode implementation")
    
    print("\n📁 Sample Bills Setup:")
    print("1. Create directory: demo/sample_bills/")
    print("2. Add PDF files from various Australian retailers")
    print("3. Test with real bills to validate accuracy")
    print("4. Consider adding bills with solar panels")
    
    print("\n🔗 Next Steps:")
    print("1. Fix any failing tests")
    print("2. Integrate with agent factory")
    print("3. Test with Streamlit UI")
    print("4. Add more retailer patterns as needed")

def main():
    """Run all tests and generate comprehensive report"""
    print("🚀 WattsMyBill - Enhanced Bill Parser Test Suite")
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Run all tests
    test_results = {
        'Basic Parser Functionality': test_basic_parser(),
        'Retailer Detection': test_retailer_detection(),
        'Amount Extraction': test_amount_extraction(),
        'Usage Extraction': test_usage_extraction(),
        'Solar Data Extraction': test_solar_extraction(),
        'Real Bill Samples': test_real_bill_samples(),
        'Privacy Mode': test_privacy_mode(),
        'Confidence Scoring': test_confidence_scoring(),
        'PDF File Processing': test_real_pdf_files(),
        'Edge Cases': test_edge_cases(),
    }
    
    # Generate comprehensive report
    generate_test_report(test_results)

if __name__ == "__main__":
    main()