"""
Enhanced Real Bill Parser - Fixed pattern recognition issues
File: src/utils/bill_parser.py
"""
import re
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import PyPDF2
import io
from PIL import Image
import pytesseract


class AustralianBillParser:
    """Enhanced parser for Australian energy bills with improved pattern recognition"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Enhanced Australian energy retailers patterns
        self.retailers = {
            'agl': ['agl', 'australian gas light', 'agl energy'],
            'origin': ['origin', 'origin energy'],
            'energyaustralia': ['energyaustralia', 'energy australia'],
            'red_energy': ['red energy', 'red'],
            'simply_energy': ['simply energy', 'simply'],
            'alinta': ['alinta', 'alinta energy'],
            'momentum': ['momentum', 'momentum energy'],
            'powershop': ['powershop'],
            'click_energy': ['click energy', 'click'],
            'lumo': ['lumo', 'lumo energy'],
            'nectr': ['nectr'],
            'sumo': ['sumo'],
            'tango': ['tango'],
            'ovo': ['ovo'],
            'globird': ['globird', 'glo bird']
        }

        # Enhanced patterns with better accuracy for problematic cases
        self.patterns = {
            'total_amount': [
                r'amount due[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'total amount[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'account balance[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'your total for this bill[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'total amount due[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'new charges[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'current charges[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'balance[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
                r'\$(\d+(?:,\d{3})*\.?\d*)[\s]*(?:amount due|total|balance)',
                r'total[\s:]*\$(\d+(?:,\d{3})*\.?\d*)'
            ],
            'usage_kwh': [
                r'any time usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'general usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'total usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'total kwh[\s:]*(\d+(?:,\d{3})*\.?\d*)',
                r'usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'electricity usage[\s:]*(\d+(?:,\d{3})*\.?\d*)',
                r'any time usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh[\s$\d\.]*',
                r'general usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh[\s$\d\.]*',
                r'total usage[\s\(]*kwh[\s\)]*[\s:]*(\d+(?:,\d{3})*\.?\d*)',
                r'(\d+(?:,\d{3})*\.?\d*)\s*kwh[\s]*\$[\d,\.]*[\s]*(?:usage|consumption|electricity)',
                r'electricity usage[\s:]*(\d+(?:,\d{3})*\.?\d*)',
                r'usage charges[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'consumption[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'energy usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'total electricity consumed[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'billing period usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh'
            ],
            'account_number': [
                r'account number[\s:]*([a-z0-9\-\s]+)',
                r'account[\s:]*([a-z0-9\-\s]+)',
                r'customer number[\s:]*([a-z0-9\-\s]+)',
                r'electricity reference number[\s:]*([a-z0-9\-\s]+)',
                r'your customer number[\s:]*([a-z0-9\-\s]+)',
                r'reference[\s:]*([a-z0-9\-\s]+)'
            ],
            'billing_days': [
                r'\((\d+)\s*days\)',
                r'number of days[\s:]*(\d+)',
                r'(\d+)\s*days',
                r'billing period[\s:]*\d+[\s/]\w+[\s/]\d+[\s\-to]*\d+[\s/]\w+[\s/]\d+[\s\(]*(\d+)[\s]*days'
            ],
            'postcode': [
                r'(?:holmview|brisbane|gold coast|cairns|townsville)\s+qld\s+(\d{4})',
                r'(?:sydney|newcastle|wollongong)\s+nsw\s+(\d{4})',
                r'(?:melbourne|geelong|ballarat)\s+vic\s+(\d{4})',
                r'\b(\d{4})\b(?=\s*(?:nsw|vic|qld|sa|wa|tas|nt|act))',
                r'(?:nsw|vic|qld|sa|wa|tas|nt|act)[\s,]+(\d{4})',
                r'\b(\d{4})\s+australia',
                r'(?:address|street|road|avenue|circuit|cct|st|rd|ave)[\s\w,]*\s+(\d{4})'
            ],
            'state': [
                r'\b(NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\b',
                r'\b(New South Wales|Victoria|Queensland|South Australia|Western Australia|Tasmania|Northern Territory|Australian Capital Territory)\b',
                r'(?:holmview|brisbane|gold coast|cairns|townsville)[\s\w,]*\s+(qld)',
                r'(?:sydney|newcastle|wollongong)[\s\w,]*\s+(nsw)',
                r'(?:melbourne|geelong|ballarat)[\s\w,]*\s+(vic)',
                r'(?:adelaide|mount gambier)[\s\w,]*\s+(sa)',
                r'(?:perth|fremantle|bunbury)[\s\w,]*\s+(wa)'
            ],
            'solar_export_kwh': [
                r'solar exports?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'feed[\-\s]*in[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'exported?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'solar feed[\-\s]*in credit[\s\(]*(?:incl[\s\w,]*)?[\s\)]*[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'exported electricity[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'pv exports?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'solar generation exported[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'feed in tariff[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh'
            ],
            'solar_credit_amount': [
                r'solar feed[\-\s]*in credit[\s\(]*(?:incl[\s\w,]*)?[\s\)]*[\s:]*\d+(?:,\d{3})*\.?\d*\s*kwh[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'solar exports?[\s:]*\d+(?:,\d{3})*\.?\d*\s*kwh[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'feed[\-\s]*in[\s:]*\$[\-]?(\d+(?:,\d{3})*\.?\d*)',
                r'solar credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'exported electricity credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'pv export credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'feed in credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'solar rebate[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)'
            ],
            'feed_in_tariff': [
                r'feed[\-\s]*in tariff[\s:$]*(\d+\.?\d*)',
                r'solar tariff[\s:$]*(\d+\.?\d*)',
                r'export rate[\s:$]*(\d+\.?\d*)',
                r'(\d+\.?\d*)c?/kwh[\s]*(?:feed|solar|export)',
                r'feed[\-\s]*in tariff[\s:$]*(\d+\.?\d*)/kwh',
                r'export tariff[\s:$]*(\d+\.?\d*)',
                r'solar feed[\-\s]*in rate[\s:]*(\d+\.?\d*)c',
                r'pv export rate[\s:$]*(\d+\.?\d*)',
                r'solar buyback rate[\s:]*(\d+\.?\d*)c/kwh'
            ]
        }

    def parse_bill(self, file_content: bytes, file_type: str, privacy_mode: bool = False) -> Dict[str, Any]:
        """Parse an energy bill and extract structured data"""
        try:
            # Extract text based on file type
            if file_type.lower() == 'pdf':
                text = self._extract_pdf_text(file_content)

                # If no usage found in first page, try extracting from all pages
                if text:
                    quick_usage_check = self._extract_usage(text)
                    if quick_usage_check is None:
                        print("DEBUG: No usage on first page, trying full PDF...")
                        text = self._extract_full_pdf_text(file_content)
            else:
                text = self._extract_image_text(file_content)

            if not text:
                return self._get_fallback_data("Could not extract text from file", privacy_mode)

            # Parse the extracted text
            parsed_data = self._parse_text(text)

            # Apply privacy mode if requested
            if privacy_mode:
                parsed_data = self._apply_privacy_mode(parsed_data)

            # Add metadata
            parsed_data.update({
                'extraction_method': 'real_parsing',
                'confidence': self._calculate_confidence(parsed_data),
                'raw_text_length': len(text),
                'parsing_timestamp': datetime.now().isoformat(),
                'privacy_mode': privacy_mode,
                'has_solar': self._has_solar_system(parsed_data)
            })

            return parsed_data

        except Exception as e:
            self.logger.error(f"Bill parsing failed: {e}")
            return self._get_fallback_data(f"Parsing error: {str(e)}", privacy_mode)

    def _extract_full_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from all pages of PDF"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            full_text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"

            return full_text.lower()

        except Exception as e:
            self.logger.error(f"Full PDF text extraction failed: {e}")
            return ""

    def _extract_pdf_text(self, pdf_content: bytes) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)

            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

            return text.lower()  # Normalize for pattern matching

        except Exception as e:
            self.logger.error(f"PDF text extraction failed: {e}")
            return ""

    def _extract_image_text(self, image_content: bytes) -> str:
        """Extract text from image using OCR"""
        try:
            image = Image.open(io.BytesIO(image_content))
            text = pytesseract.image_to_string(image)
            return text.lower()
        except Exception as e:
            self.logger.error(f"Image text extraction failed: {e}")
            return ""

    def _parse_text(self, text: str) -> Dict[str, Any]:
        """Parse extracted text to find bill information - enhanced accuracy"""

        parsed_data = {
            'retailer': self._find_retailer(text),
            'account_number': self._clean_account_number(self._extract_pattern(text, 'account_number')),
            'total_amount': self._extract_total_amount(text),
            'usage_kwh': self._extract_usage(text),
            'supply_charge': self._extract_supply_charge(text),
            'usage_charge': self._extract_usage_charge(text),
            'billing_period': self._extract_billing_period(text),
            'postcode': self._extract_postcode_with_context(text),
            'state': self._extract_state_with_context(text),
            'tariff_type': self._identify_tariff_type(text),
            'billing_days': self._extract_billing_days(text),
            # Solar-related data
            'solar_export_kwh': self._extract_solar_export(text),
            'solar_credit_amount': self._extract_solar_credit(text),
            'feed_in_tariff': self._extract_feed_in_tariff(text),
            'daily_solar_export': None,
            'solar_savings_annual': None
        }

        # Calculate derived values
        parsed_data.update(self._calculate_derived_values(parsed_data))

        return parsed_data

    def _find_retailer(self, text: str) -> Optional[str]:
        """Identify the energy retailer with better accuracy"""
        retailer_scores = {}

        for retailer, patterns in self.retailers.items():
            score = 0
            for pattern in patterns:
                count = text.count(pattern)
                if count > 0:
                    weight = len(pattern.split())
                    score += count * weight

            if score > 0:
                retailer_scores[retailer] = score

        if retailer_scores:
            best_retailer = max(retailer_scores, key=retailer_scores.get)
            return best_retailer.replace('_', ' ').title()

        return None

    def _extract_total_amount(self, text: str) -> Optional[float]:
        """Extract total amount with better accuracy"""
        for pattern in self.patterns['total_amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if 10 <= amount <= 10000:
                        return amount
                except ValueError:
                    continue

        # Strategy 2: Look for amounts in typical bill sections
        amount_patterns = [
            r'electricity account[\s\S]*?total amount[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
            r'here\'s your bill[\s\S]*?\$(\d+(?:,\d{3})*\.?\d*)',
            r'amount due[\s\S]*?\$(\d+(?:,\d{3})*\.?\d*)'
        ]

        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if 10 <= amount <= 10000:
                        return amount
                except ValueError:
                    continue

        return None

    def _extract_usage(self, text: str) -> Optional[int]:
        """FIXED: Extract usage in kWh with accurate pattern matching based on diagnostic"""

        print(f"DEBUG: Searching for usage in text length: {len(text)}")

        # Strategy 1: Specific patterns based on diagnostic results

        # Origin format - look for the exact pattern we saw
        origin_match = re.search(
            r'general usage[\s\n]*(\d+(?:,\d{3})*\.?\d*)\s*kwh', text, re.IGNORECASE)
        if origin_match:
            try:
                usage = float(origin_match.group(1).replace(',', ''))
                if 50 <= usage <= 50000:
                    print(f"DEBUG: Found Origin usage: {usage} kWh")
                    return int(usage)
            except ValueError:
                pass

        # AGL format - sum peak and off-peak based on diagnostic
        peak_total = 0

        # Look for peak usage
        peak_match = re.search(
            r'peak usage[^0-9]*(\d+)\s*kwh', text, re.IGNORECASE)
        if peak_match:
            try:
                peak_usage = int(peak_match.group(1))
                if 10 <= peak_usage <= 10000:
                    peak_total += peak_usage
                    print(f"DEBUG: Found peak usage: {peak_usage} kWh")
            except ValueError:
                pass

        # Look for off-peak usage
        offpeak_match = re.search(
            r'off[\s\-]*peak usage[^0-9]*(\d+)\s*kwh', text, re.IGNORECASE)
        if offpeak_match:
            try:
                offpeak_usage = int(offpeak_match.group(1))
                if 10 <= offpeak_usage <= 10000:
                    peak_total += offpeak_usage
                    print(f"DEBUG: Found off-peak usage: {offpeak_usage} kWh")
            except ValueError:
                pass

        if peak_total > 0:
            print(
                f"DEBUG: Total AGL usage (peak + off-peak): {peak_total} kWh")
            return peak_total

        # Alinta format - try multiple approaches
        alinta_patterns = [
            r'any time usage[\s\n]*(\d+)\s*kwh',
            r'any time[\s\S]*?(\d+)\s*kwh',
            # Look on other pages if needed
            r'usage[\s\S]*?(\d+)\s*kwh[\s\S]*?\$[\d,\.]+',
        ]

        for pattern in alinta_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    usage = int(match.group(1))
                    if 100 <= usage <= 10000:  # Reasonable range for Alinta
                        print(f"DEBUG: Found Alinta usage: {usage} kWh")
                        return usage
                except ValueError:
                    continue

        # Generic fallback patterns
        fallback_patterns = [
            r'total usage[\s\n]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'electricity usage[\s\n]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'total usage kwh[\s:]*(\d+(?:,\d{3})*\.?\d*)',
            r'usage[\s\n]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
        ]

        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    usage = float(match.group(1).replace(',', ''))
                    if 50 <= usage <= 50000:
                        print(f"DEBUG: Found generic usage: {usage} kWh")
                        return int(usage)
                except ValueError:
                    continue

        print("DEBUG: No usage patterns matched")
        return None

    def _extract_postcode_with_context(self, text: str) -> Optional[str]:
        """FIXED: Extract postcode with better context awareness"""
        context_patterns = [
            r'holmview\s+qld\s+(\d{4})',
            r'brisbane\s+qld\s+(\d{4})',
            r'melbourne\s+vic\s+(\d{4})',
            r'sydney\s+nsw\s+(\d{4})',
            r'adelaide\s+sa\s+(\d{4})',
            r'perth\s+wa\s+(\d{4})',
        ]

        for pattern in context_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        # Fallback to general patterns
        for pattern in self.patterns['postcode']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_state_with_context(self, text: str) -> Optional[str]:
        """FIXED: Extract state with better context awareness"""
        context_patterns = [
            (r'holmview[\s\w,]*qld', 'QLD'),
            (r'brisbane[\s\w,]*qld', 'QLD'),
            (r'gold coast[\s\w,]*qld', 'QLD'),
            (r'melbourne[\s\w,]*vic', 'VIC'),
            (r'sydney[\s\w,]*nsw', 'NSW'),
            (r'adelaide[\s\w,]*sa', 'SA'),
            (r'perth[\s\w,]*wa', 'WA'),
        ]

        for pattern, state in context_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return state

        # Fallback to general patterns
        state_str = self._extract_pattern(text, 'state')
        if state_str:
            state_mapping = {
                'new south wales': 'NSW',
                'victoria': 'VIC',
                'queensland': 'QLD',
                'south australia': 'SA',
                'western australia': 'WA',
                'tasmania': 'TAS',
                'northern territory': 'NT',
                'australian capital territory': 'ACT'
            }

            state_lower = state_str.lower()
            return state_mapping.get(state_lower, state_str.upper())

        return None

    def _extract_billing_days(self, text: str) -> Optional[int]:
        """Extract billing days with better accuracy"""
        for pattern in self.patterns['billing_days']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    days = int(match.group(1))
                    if 28 <= days <= 100:
                        return days
                except ValueError:
                    continue
        return None

    def _extract_solar_export(self, text: str) -> Optional[float]:
        """FIXED: Extract solar export amount in kWh with better patterns"""

        # Enhanced patterns based on your diagnostic data
        solar_export_patterns = [
            # Origin format: "solar feed-in credit (incl gst): 1,250 kwh"
            r'solar feed[\-\s]*in credit[\s\(]*(?:incl[\s\w,]*)?[\s\)]*[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',

            # Standard patterns
            r'solar exports?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'feed[\-\s]*in[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'exported?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'exported electricity[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'pv exports?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'solar generation exported[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',

            # More flexible patterns
            r'solar[\s\w]*credit[\s\S]*?(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'feed[\s\-]*in[\s\S]*?(\d+(?:,\d{3})*\.?\d*)\s*kwh',
        ]

        print(f"🐛 DEBUG: Searching for solar export in text...")

        for i, pattern in enumerate(solar_export_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    export = float(match.group(1).replace(',', ''))
                    if 0 <= export <= 10000:  # Reasonable solar export range
                        print(
                            f"🐛 Found solar export with pattern {i+1}: {export} kWh")
                        print(f"   Pattern: {pattern}")
                        print(f"   Match: '{match.group(0)}'")
                        return export
                except ValueError:
                    continue

        print(f"🐛 No solar export found")
        return None

    def _extract_solar_credit(self, text: str) -> Optional[float]:
        """FIXED: Extract solar feed-in credit amount with better patterns"""

        # Enhanced patterns for solar credits
        solar_credit_patterns = [
            # Origin format: "solar feed-in credit (incl gst): 1,250 kwh $-125.50"
            r'solar feed[\-\s]*in credit[\s\(]*(?:incl[\s\w,]*)?[\s\)]*[\s:]*\d+(?:,\d{3})*\.?\d*\s*kwh[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',

            # Standard patterns
            r'solar exports?[\s:]*\d+(?:,\d{3})*\.?\d*\s*kwh[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
            r'feed[\-\s]*in[\s:]*\$[\-]?(\d+(?:,\d{3})*\.?\d*)',
            r'solar credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
            r'exported electricity credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
            r'pv export credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
            r'feed in credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',

            # More flexible - look for credit amounts near solar keywords
            r'solar[\s\w]*credit[\s\S]*?\$[\-]?(\d+(?:,\d{3})*\.?\d*)',
            r'feed[\s\-]*in[\s\S]*?\$[\-]?(\d+(?:,\d{3})*\.?\d*)',

            # Look for negative amounts (credits)
            r'\$\-(\d+(?:,\d{3})*\.?\d*)[\s\S]*?(?:solar|feed|credit)',
            r'(?:solar|feed|credit)[\s\S]*?\$\-(\d+(?:,\d{3})*\.?\d*)',
        ]

        print(f"🐛 DEBUG: Searching for solar credit...")

        for i, pattern in enumerate(solar_credit_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    credit = float(match.group(1).replace(',', ''))
                    if 0 <= credit <= 1000:  # Reasonable credit range
                        print(
                            f"🐛 Found solar credit with pattern {i+1}: ${credit}")
                        print(f"   Pattern: {pattern}")
                        print(f"   Match: '{match.group(0)}'")
                        return credit
                except ValueError:
                    continue

        print(f"🐛 No solar credit found")
        return None

    def _extract_feed_in_tariff(self, text: str) -> Optional[float]:
        """FIXED: Extract feed-in tariff rate with better patterns"""

        # Enhanced patterns for feed-in tariffs
        feed_in_patterns = [
            # Origin format: "feed-in tariff: $0.10/kwh"
            r'feed[\-\s]*in tariff[\s:$]*(\d+\.?\d*)',
            r'feed[\-\s]*in tariff[\s:$]*(\d+\.?\d*)/kwh',

            # Standard patterns
            r'solar tariff[\s:$]*(\d+\.?\d*)',
            r'export rate[\s:$]*(\d+\.?\d*)',
            r'export tariff[\s:$]*(\d+\.?\d*)',
            r'solar feed[\-\s]*in rate[\s:]*(\d+\.?\d*)c',
            r'pv export rate[\s:$]*(\d+\.?\d*)',
            r'solar buyback rate[\s:]*(\d+\.?\d*)c/kwh',

            # Pattern for cents notation
            r'(\d+\.?\d*)c?/kwh[\s]*(?:feed|solar|export)',

            # More flexible patterns
            r'feed[\s\-]*in[\s\S]*?\$(\d+\.?\d*)',
            r'solar[\s\w]*tariff[\s\S]*?\$(\d+\.?\d*)',
        ]

        print(f"🐛 DEBUG: Searching for feed-in tariff...")

        for i, pattern in enumerate(feed_in_patterns):
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    tariff = float(match.group(1))
                    # Convert cents to dollars if necessary
                    if tariff > 1:  # Likely in cents
                        tariff = tariff / 100
                    if 0.01 <= tariff <= 1.0:  # Reasonable tariff range
                        print(
                            f"🐛 Found feed-in tariff with pattern {i+1}: ${tariff:.3f}/kWh")
                        print(f"   Pattern: {pattern}")
                        print(f"   Match: '{match.group(0)}'")
                        return tariff
                except ValueError:
                    continue

        print(f"🐛 No feed-in tariff found")
        return None

    def _has_solar_system(self, data: Dict[str, Any]) -> bool:
        """Determine if the household has solar panels"""
        return any([
            data.get('solar_export_kwh') is not None,
            data.get('solar_credit_amount') is not None,
            data.get('feed_in_tariff') is not None
        ])

    def _clean_account_number(self, account: str) -> Optional[str]:
        """FIXED: Clean and validate account number - better filtering"""
        if not account:
            return None

        clean_account = account.strip()

        skip_words = [
            'supply', 'address', 'number', 'account', 'customer', 'electricity',
            'supply address', 'amount due', 'your customer', 'reference number'
        ]

        if clean_account.lower() in skip_words or len(clean_account) < 3:
            return None

        if not re.search(r'[a-z0-9]', clean_account.lower()):
            return None

        return clean_account

    def _extract_supply_charge(self, text: str) -> Optional[float]:
        """Extract supply charge"""
        patterns = [
            r'supply charge[\s:]*(\d+)\s*days?[\s:$]*(\d+\.?\d*)',
            r'daily supply[\s:]*\d+\s*days?[\s:$]*(\d+\.?\d*)',
            r'service charge[\s:$]*(\d+\.?\d*)',
            r'connection[\s:$]*(\d+\.?\d*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(2) if len(
                        match.groups()) > 1 else match.group(1))
                    if 0 <= amount <= 1000:
                        return amount
                except (ValueError, IndexError):
                    continue
        return None

    def _extract_usage_charge(self, text: str) -> Optional[float]:
        """Extract usage charge"""
        patterns = [
            r'usage charge[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
            r'energy charge[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
            r'electricity charge[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
            r'general usage[\s:]*\d+(?:,\d{3})*\.?\d*\s*kwh[\s:$]*(\d+(?:,\d{3})*\.?\d*)',
            r'any time usage[\s:]*\d+(?:,\d{3})*\.?\d*[\s:$]*(\d+(?:,\d{3})*\.?\d*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if 0 <= amount <= 5000:
                        return amount
                except ValueError:
                    continue
        return None

    def _apply_privacy_mode(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply privacy mode to redact personal information"""
        if data.get('account_number'):
            account = data['account_number']
            if len(account) > 4:
                data['account_number'] = '*' * \
                    (len(account) - 4) + account[-4:]

        data['postcode'] = None
        return data

    def _calculate_derived_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional values from extracted data including solar metrics"""
        derived = {}

        if data.get('usage_kwh') and data.get('billing_days'):
            derived['daily_average_kwh'] = data['usage_kwh'] / \
                data['billing_days']

        if data.get('total_amount') and data.get('usage_kwh'):
            derived['cost_per_kwh'] = data['total_amount'] / data['usage_kwh']

        if data.get('supply_charge') and data.get('billing_days'):
            derived['daily_supply_charge'] = data['supply_charge'] / \
                data['billing_days']

        if data.get('usage_charge') and data.get('usage_kwh'):
            derived['usage_rate'] = data['usage_charge'] / data['usage_kwh']

        if data.get('solar_export_kwh') and data.get('billing_days'):
            derived['daily_solar_export'] = data['solar_export_kwh'] / \
                data['billing_days']

        if data.get('solar_credit_amount'):
            derived['solar_savings_annual'] = data['solar_credit_amount'] * \
                (365 / (data.get('billing_days') or 90))

        return derived

    def _extract_pattern(self, text: str, pattern_type: str) -> Optional[str]:
        """Extract data using regex patterns"""
        if pattern_type not in self.patterns:
            return None

        for pattern in self.patterns[pattern_type]:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_billing_period(self, text: str) -> Optional[Dict[str, str]]:
        """Extract billing period dates"""
        patterns = [
            r'billing period[\s:]*(\d{1,2}[\s/]\w{3}[\s/]\d{2,4})[\s\-to]*(\d{1,2}[\s/]\w{3}[\s/]\d{2,4})',
            r'(\d{1,2}[\s/]\w{3}[\s/]\d{2,4})\s*to\s*(\d{1,2}[\s/]\w{3}[\s/]\d{2,4})',
            r'period[\s:]*(\d{1,2}/\d{1,2}/\d{2,4})[\s\-to]*(\d{1,2}/\d{1,2}/\d{2,4})',
            r'(\d{1,2}/\d{1,2}/\d{2,4})[\s\-to]*(\d{1,2}/\d{1,2}/\d{2,4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return {
                    'start_date': match.group(1),
                    'end_date': match.group(2)
                }
        return None

    def _identify_tariff_type(self, text: str) -> str:
        """Identify tariff structure type"""
        if any(term in text for term in ['time of use', 'peak', 'off-peak', 'shoulder']):
            return 'time_of_use'
        elif 'demand' in text:
            return 'demand'
        else:
            return 'single_rate'

    def _calculate_confidence(self, data: Dict[str, Any]) -> float:
        """Calculate confidence score based on extracted data"""
        required_fields = ['retailer', 'total_amount', 'usage_kwh']
        found_fields = sum(
            1 for field in required_fields if data.get(field) is not None)

        base_confidence = found_fields / len(required_fields)

        optional_fields = ['account_number', 'state',
                           'billing_period', 'billing_days']
        found_optional = sum(
            1 for field in optional_fields if data.get(field) is not None)

        bonus = found_optional * 0.1

        return min(base_confidence + bonus, 1.0)

    def _get_fallback_data(self, error_message: str, privacy_mode: bool = False) -> Dict[str, Any]:
        """Return fallback data when parsing fails"""
        account_number = None if privacy_mode else "UNKNOWN"

        return {
            'retailer': 'Unknown Retailer',
            'account_number': account_number,
            'total_amount': 450.0,
            'usage_kwh': 720,
            'supply_charge': 89.0,
            'usage_charge': 340.0,
            'billing_period': None,
            'postcode': None if privacy_mode else "2000",
            'state': 'NSW',
            'tariff_type': 'single_rate',
            'billing_days': 90,
            'daily_supply_charge': 0.99,
            'usage_rate': 0.47,
            'cost_per_kwh': 0.625,
            'daily_average_kwh': 8.0,
            # Solar fields
            'solar_export_kwh': None,
            'solar_credit_amount': None,
            'feed_in_tariff': None,
            'daily_solar_export': None,
            'solar_savings_annual': None,
            'has_solar': False,
            # Metadata
            'extraction_method': 'fallback',
            'confidence': 0.3,
            'error': error_message,
            'parsing_timestamp': datetime.now().isoformat(),
            'privacy_mode': privacy_mode
        }


# Utility function for easy import
def parse_australian_energy_bill(file_content: bytes, file_type: str, privacy_mode: bool = False) -> Dict[str, Any]:
    """
    Convenience function to parse Australian energy bills

    Args:
        file_content: Raw file content as bytes
        file_type: 'pdf' or 'image'
        privacy_mode: If True, redact personal information

    Returns:
        Dictionary with extracted bill data
    """
    parser = AustralianBillParser()
    return parser.parse_bill(file_content, file_type, privacy_mode)
