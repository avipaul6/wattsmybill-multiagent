#!/usr/bin/env python3
"""
Test the Bill Analyzer Agent
File: test_bill_analyzer.py (note: correct filename)
"""
import sys
from pathlib import Path
import json
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_bill_analyzer_agent():
    """Test the Bill Analyzer Agent with real PDF files"""
    print("🤖 Testing Bill Analyzer Agent\n")
    
    try:
        # Import with correct path handling
        from agents.bill_analyzer import BillAnalyzerAgent
        
        analyzer = BillAnalyzerAgent()
        sample_bills_dir = "demo/sample_bills"
        
        if not os.path.exists(sample_bills_dir):
            print("❌ No demo/sample_bills directory found")
            return False
        
        pdf_files = [f for f in os.listdir(sample_bills_dir) if f.endswith('.pdf')]
        
        if not pdf_files:
            print("❌ No PDF files found for testing")
            return False
        
        success_count = 0
        
        for pdf_file in pdf_files:
            print(f"📊 Analyzing: {pdf_file}")
            print("=" * 50)
            
            file_path = os.path.join(sample_bills_dir, pdf_file)
            
            try:
                # Read the PDF file
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Analyze the bill
                analysis = analyzer.analyze_bill(file_content, 'pdf')
                
                if analysis.get('error'):
                    print(f"❌ Analysis failed: {analysis.get('message')}")
                    continue
                
                # Display key analysis results
                print("📋 ANALYSIS RESULTS:")
                
                # Usage analysis
                usage_profile = analysis.get('usage_profile', {})
                print(f"   ⚡ Usage Category: {usage_profile.get('usage_category', 'Unknown')}")
                print(f"   📊 Daily Average: {usage_profile.get('daily_average', 0):.1f} kWh/day")
                print(f"   📈 Usage Percentile: {usage_profile.get('usage_percentile', 0)}th")
                
                # Cost analysis
                cost_breakdown = analysis.get('cost_breakdown', {})
                print(f"   💰 Cost Rating: {cost_breakdown.get('cost_rating', 'Unknown')}")
                print(f"   💵 Cost per kWh: ${cost_breakdown.get('cost_per_kwh', 0):.3f}")
                
                # Solar analysis
                solar_analysis = analysis.get('solar_analysis', {})
                if solar_analysis.get('has_solar'):
                    print(f"   ☀️ Solar System: Yes")
                    print(f"   🔄 Export Ratio: {solar_analysis.get('export_ratio_percent', 0)}%")
                    print(f"   💸 Annual Solar Savings: ${solar_analysis.get('annual_savings_projection', 0):.2f}")
                else:
                    print(f"   ☀️ Solar System: No")
                
                # Efficiency score
                efficiency_score = analysis.get('efficiency_score', 0)
                print(f"   🎯 Efficiency Score: {efficiency_score:.0f}/100")
                
                # Recommendations
                recommendations = analysis.get('recommendations', [])
                print(f"   💡 Recommendations ({len(recommendations)}):")
                for i, rec in enumerate(recommendations[:3], 1):  # Show top 3
                    print(f"      {i}. {rec}")
                
                # Summary
                summary = analyzer.get_analysis_summary(analysis)
                print(f"\n   📝 Summary: {summary}")
                
                print(f"\n   ✅ Successfully analyzed {pdf_file}!")
                success_count += 1
                
            except Exception as e:
                print(f"   ❌ Error analyzing {pdf_file}: {e}")
                import traceback
                traceback.print_exc()
            
            print("\n" + "="*70 + "\n")
        
        print(f"📈 Analysis Summary: {success_count}/{len(pdf_files)} bills successfully analyzed")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Bill analyzer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_analysis_components():
    """Test individual analysis components"""
    print("🧪 Testing Analysis Components\n")
    
    try:
        # Import with correct path handling
        from agents.bill_analyzer import BillAnalyzerAgent
        
        analyzer = BillAnalyzerAgent()
        
        # Mock bill data for testing
        mock_bill_data = {
            'usage_kwh': 1200,
            'billing_days': 90,
            'daily_average_kwh': 13.3,
            'state': 'QLD',
            'total_amount': 350.0,
            'cost_per_kwh': 0.292,
            'supply_charge': 120.0,
            'usage_charge': 230.0,
            'has_solar': True,
            'solar_export_kwh': 450,
            'solar_credit_amount': 45.0,
            'feed_in_tariff': 0.10,
            'tariff_type': 'single_rate'
        }
        
        print("📊 Testing Usage Analysis:")
        usage_analysis = analyzer._analyze_usage_patterns(mock_bill_data)
        print(f"   Category: {usage_analysis.get('category')}")
        print(f"   Comparison: {usage_analysis.get('comparison')}")
        
        print("\n💰 Testing Cost Analysis:")
        cost_analysis = analyzer._analyze_costs(mock_bill_data)
        print(f"   Rating: {cost_analysis.get('rating')}")
        print(f"   Comparison: {cost_analysis.get('comparison')}")
        
        print("\n☀️ Testing Solar Analysis:")
        solar_analysis = analyzer._analyze_solar_system(mock_bill_data)
        print(f"   Performance: {solar_analysis.get('performance_rating')}")
        print(f"   Export Ratio: {solar_analysis.get('export_ratio_percent')}%")
        
        print("\n💡 Testing Recommendations:")
        recommendations = analyzer._generate_recommendations(mock_bill_data, usage_analysis, cost_analysis, solar_analysis)
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
        
        print("\n🎯 Testing Efficiency Score:")
        efficiency_score = analyzer._calculate_efficiency_score(usage_analysis, cost_analysis, solar_analysis)
        print(f"   Score: {efficiency_score:.0f}/100")
        
        return True
        
    except Exception as e:
        print(f"❌ Component testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all Bill Analyzer Agent tests"""
    print("🚀 WattsMyBill - Bill Analyzer Agent Test Suite")
    print("="*60)
    
    # Test components first
    component_success = test_analysis_components()
    
    # Test with real files
    file_success = test_bill_analyzer_agent()
    
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    if component_success and file_success:
        print("✅ ALL TESTS PASSED!")
        print("🎉 Bill Analyzer Agent is working correctly!")
        print("\n🔗 Next Steps:")
        print("1. ✅ Bill Parser working")
        print("2. ✅ Bill Analyzer Agent working")
        print("3. 🔄 Next: Market Research Agent")
        print("4. 🔄 Then: Agent orchestration")
    else:
        print("❌ Some tests failed")
        if not component_success:
            print("🔧 Fix component analysis methods")
        if not file_success:
            print("🔧 Check file processing and integration")

if __name__ == "__main__":
    main()