#!/usr/bin/env python3
"""
Diagnostic test to understand why usage extraction is failing
File: diagnose_usage.py
"""
import sys
from pathlib import Path
import re
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def diagnose_pdf_text_extraction():
    """Diagnose what text is actually being extracted from PDFs"""
    print("🔍 DIAGNOSTIC: Analyzing PDF Text Extraction\n")
    
    try:
        from utils.bill_parser import AustralianBillParser
        
        parser = AustralianBillParser()
        sample_bills_dir = "demo/sample_bills"
        
        if not os.path.exists(sample_bills_dir):
            print("❌ No demo/sample_bills directory found")
            return
        
        pdf_files = [f for f in os.listdir(sample_bills_dir) if f.endswith('.pdf')]
        
        for pdf_file in pdf_files:
            print(f"📄 ANALYZING: {pdf_file}")
            print("=" * 50)
            
            file_path = os.path.join(sample_bills_dir, pdf_file)
            
            try:
                # Read and extract text
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Extract raw text
                raw_text = parser._extract_pdf_text(file_content)
                
                if not raw_text:
                    print("❌ No text extracted from PDF")
                    continue
                
                print(f"📊 Extracted text length: {len(raw_text)} characters")
                print(f"📝 First 500 characters:")
                print("-" * 30)
                print(raw_text[:500])
                print("-" * 30)
                
                # Look for usage patterns in the raw text
                print(f"\n🔍 USAGE PATTERN ANALYSIS:")
                
                usage_patterns = [
                    r'usage[\s\w]*(\d+(?:,\d{3})*\.?\d*)',
                    r'(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                    r'any time[\s\w]*(\d+(?:,\d{3})*\.?\d*)',
                    r'general[\s\w]*(\d+(?:,\d{3})*\.?\d*)',
                    r'peak[\s\w]*(\d+(?:,\d{3})*\.?\d*)',
                    r'off[\-\s]*peak[\s\w]*(\d+(?:,\d{3})*\.?\d*)',
                    r'total[\s\w]*(\d+(?:,\d{3})*\.?\d*)',
                    r'electricity[\s\w]*(\d+(?:,\d{3})*\.?\d*)',
                ]
                
                found_numbers = []
                for pattern in usage_patterns:
                    matches = re.finditer(pattern, raw_text, re.IGNORECASE)
                    for match in matches:
                        try:
                            context_start = max(0, match.start() - 30)
                            context_end = min(len(raw_text), match.end() + 30)
                            context = raw_text[context_start:context_end].strip()
                            
                            number = match.group(1).replace(',', '')
                            if number.replace('.', '').isdigit():
                                num_val = float(number)
                                if 50 <= num_val <= 50000:  # Reasonable kWh range
                                    found_numbers.append((num_val, context))
                                    print(f"   ✅ Found: {num_val} in context: '{context}'")
                        except (ValueError, IndexError):
                            continue
                
                if not found_numbers:
                    print("   ❌ No reasonable usage numbers found")
                    
                    # Look for ANY numbers that might be usage
                    print("\n🔍 SEARCHING FOR ANY NUMBERS:")
                    number_pattern = r'(\d+(?:,\d{3})*\.?\d*)'
                    matches = re.finditer(number_pattern, raw_text)
                    
                    for i, match in enumerate(matches):
                        if i >= 10:  # Limit output
                            break
                        try:
                            context_start = max(0, match.start() - 20)
                            context_end = min(len(raw_text), match.end() + 20)
                            context = raw_text[context_start:context_end].strip()
                            print(f"   Number: {match.group(1)} in '{context}'")
                        except:
                            continue
                
                # Test current parser method
                print(f"\n🧪 CURRENT PARSER RESULT:")
                current_usage = parser._extract_usage(raw_text)
                print(f"   Current method extracts: {current_usage} kWh")
                
                print("\n" + "="*70 + "\n")
                
            except Exception as e:
                print(f"❌ Error processing {pdf_file}: {e}")
                import traceback
                traceback.print_exc()
                print("\n" + "="*70 + "\n")
    
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

def suggest_pattern_fixes():
    """Suggest specific pattern fixes based on common issues"""
    print("💡 PATTERN FIX SUGGESTIONS")
    print("=" * 50)
    
    suggestions = [
        {
            "issue": "PDF text extraction problems",
            "fix": "PDF might have images/OCR issues. Try converting PDF to text first.",
            "code": "# Install pdfplumber: pip install pdfplumber\nimport pdfplumber\nwith pdfplumber.open(pdf_path) as pdf:\n    text = '\\n'.join([page.extract_text() for page in pdf.pages])"
        },
        {
            "issue": "Usage numbers scattered across lines",
            "fix": "Combine lines before pattern matching",
            "code": "# Remove line breaks in usage sections\ntext = re.sub(r'usage\\s+\\n+', 'usage ', text, flags=re.IGNORECASE)"
        },
        {
            "issue": "Numbers separated by spaces or formatting",
            "fix": "More flexible number patterns",
            "code": "# Pattern for numbers with various separators\nr'(\\d+[\\s,]*\\d*\\.?\\d*)\\s*kwh'"
        }
    ]
    
    for suggestion in suggestions:
        print(f"🔧 {suggestion['issue']}")
        print(f"   💡 {suggestion['fix']}")
        print(f"   📝 Code: {suggestion['code']}")
        print()

if __name__ == "__main__":
    diagnose_pdf_text_extraction()
    suggest_pattern_fixes()