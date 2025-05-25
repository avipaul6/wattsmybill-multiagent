"""
Enhanced Real Bill Parser - Improved accuracy, solar data, privacy options
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
    """Enhanced parser for Australian energy bills with solar and privacy features"""
    
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
        
        # Enhanced patterns with better accuracy
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
                # Pattern for bills with $ symbol before amount
                r'\$(\d+(?:,\d{3})*\.?\d*)[\s]*(?:amount due|total|balance)',
                r'total[\s:]*\$(\d+(?:,\d{3})*\.?\d*)'
            ],
            'usage_kwh': [
                r'general usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'any time usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'total usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'total kwh[\s:]*(\d+(?:,\d{3})*\.?\d*)',
                r'usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'electricity usage[\s:]*(\d+(?:,\d{3})*\.?\d*)',
                # Pattern for detailed usage sections
                r'total usage[\s\(]*kwh[\s\)]*[\s:]*(\d+(?:,\d{3})*\.?\d*)',
                r'(\d+(?:,\d{3})*\.?\d*)\s*kwh[\s]*\$[\d,\.]*[\s]*(?:usage|consumption|electricity)'
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
                r'\b(\d{4})\b(?=\s*(?:nsw|vic|qld|sa|wa|tas|nt|act))',
                r'(?:nsw|vic|qld|sa|wa|tas|nt|act)[\s,]+(\d{4})',
                r'\b(\d{4})\s+australia'
            ],
            'state': [
                r'\b(NSW|VIC|QLD|SA|WA|TAS|NT|ACT)\b',
                r'\b(New South Wales|Victoria|Queensland|South Australia|Western Australia|Tasmania|Northern Territory|Australian Capital Territory)\b'
            ],
            # Solar export patterns
            'solar_export_kwh': [
                r'solar exports?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'feed[\-\s]*in[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'exported?[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
                r'solar feed[\-\s]*in credit[\s\(]*(?:incl[\s\w,]*)?[\s\)]*[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh'
            ],
            'solar_credit_amount': [
                r'solar feed[\-\s]*in credit[\s\(]*(?:incl[\s\w,]*)?[\s\)]*[\s:]*\d+(?:,\d{3})*\.?\d*\s*kwh[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'solar exports?[\s:]*\d+(?:,\d{3})*\.?\d*\s*kwh[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)',
                r'feed[\-\s]*in[\s:]*\$[\-]?(\d+(?:,\d{3})*\.?\d*)',
                r'solar credit[\s:$\-]*(\d+(?:,\d{3})*\.?\d*)'
            ],
            'feed_in_tariff': [
                r'feed[\-\s]*in tariff[\s:$]*(\d+\.?\d*)',
                r'solar tariff[\s:$]*(\d+\.?\d*)',
                r'export rate[\s:$]*(\d+\.?\d*)',
                r'(\d+\.?\d*)c?/kwh[\s]*(?:feed|solar|export)'
            ]
        }
    
    def parse_bill(self, file_content: bytes, file_type: str, privacy_mode: bool = False) -> Dict[str, Any]:
        """
        Parse an energy bill and extract structured data
        
        Args:
            file_content: Raw file content as bytes
            file_type: 'pdf' or 'image'
            privacy_mode: If True, redact personal information
            
        Returns:
            Dictionary with extracted bill data
        """
        try:
            # Extract text based on file type
            if file_type.lower() == 'pdf':
                text = self._extract_pdf_text(file_content)
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
            'postcode': self._extract_pattern(text, 'postcode'),
            'state': self._extract_state(text),
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
        # First try exact matches in order of specificity
        retailer_scores = {}
        
        for retailer, patterns in self.retailers.items():
            score = 0
            for pattern in patterns:
                # Count occurrences and weight by pattern specificity
                count = text.count(pattern)
                if count > 0:
                    # Longer patterns get higher weight
                    weight = len(pattern.split())
                    score += count * weight
            
            if score > 0:
                retailer_scores[retailer] = score
        
        if retailer_scores:
            # Return the retailer with highest score
            best_retailer = max(retailer_scores, key=retailer_scores.get)
            return best_retailer.replace('_', ' ').title()
        
        return None
    
    def _extract_total_amount(self, text: str) -> Optional[float]:
        """Extract total amount with better accuracy"""
        # Try multiple strategies to find the total amount
        
        # Strategy 1: Look for common amount patterns
        for pattern in self.patterns['total_amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    # Validate amount is reasonable (between $10 and $10,000)
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
        """Extract usage in kWh with better accuracy"""
        # Try multiple strategies to find usage
        
        # Strategy 1: Look for total usage in summary sections
        usage_patterns = [
            r'total kwh[\s:]*(\d+(?:,\d{3})*\.?\d*)',
            r'total usage[\s\(]*kwh[\s\)]*[\s:]*(\d+(?:,\d{3})*\.?\d*)',
            r'electricity usage[\s:]*(\d+(?:,\d{3})*\.?\d*)',
            r'general usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh',
            r'any time usage[\s:]*(\d+(?:,\d{3})*\.?\d*)\s*kwh'
        ]
        
        for pattern in usage_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    usage = float(match.group(1).replace(',', ''))
                    # Validate usage is reasonable (between 50 and 50,000 kWh)
                    if 50 <= usage <= 50000:
                        return int(usage)
                except ValueError:
                    continue
        
        return None
    
    def _extract_billing_days(self, text: str) -> Optional[int]:
        """Extract billing days with better accuracy"""
        for pattern in self.patterns['billing_days']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    days = int(match.group(1))
                    # Validate days is reasonable (between 28 and 100)
                    if 28 <= days <= 100:
                        return days
                except ValueError:
                    continue
        return None
    
    def _extract_solar_export(self, text: str) -> Optional[float]:
        """Extract solar export amount in kWh"""
        for pattern in self.patterns['solar_export_kwh']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    export = float(match.group(1).replace(',', ''))
                    if 0 <= export <= 10000:  # Reasonable solar export range
                        return export
                except ValueError:
                    continue
        return None
    
    def _extract_solar_credit(self, text: str) -> Optional[float]:
        """Extract solar feed-in credit amount"""
        for pattern in self.patterns['solar_credit_amount']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    credit = float(match.group(1).replace(',', ''))
                    if 0 <= credit <= 1000:  # Reasonable credit range
                        return credit
                except ValueError:
                    continue
        return None
    
    def _extract_feed_in_tariff(self, text: str) -> Optional[float]:
        """Extract feed-in tariff rate"""
        for pattern in self.patterns['feed_in_tariff']:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    tariff = float(match.group(1))
                    # Convert cents to dollars if necessary
                    if tariff > 1:  # Likely in cents
                        tariff = tariff / 100
                    if 0.01 <= tariff <= 1.0:  # Reasonable tariff range
                        return tariff
                except ValueError:
                    continue
        return None
    
    def _has_solar_system(self, data: Dict[str, Any]) -> bool:
        """Determine if the household has solar panels"""
        return any([
            data.get('solar_export_kwh') is not None,
            data.get('solar_credit_amount') is not None,
            data.get('feed_in_tariff') is not None
        ])
    
    def _clean_account_number(self, account: str) -> Optional[str]:
        """Clean and validate account number"""
        if not account:
            return None
        
        # Remove common words that get picked up by regex
        clean_account = account.strip()
        
        # Skip if it's a common word or too short
        skip_words = ['supply', 'address', 'number', 'account', 'customer', 'electricity']
        if clean_account.lower() in skip_words or len(clean_account) < 3:
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
                    # If pattern has two groups, second is the amount
                    amount = float(match.group(2) if len(match.groups()) > 1 else match.group(1))
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
            # Mask account number (show last 4 digits only)
            account = data['account_number']
            if len(account) > 4:
                data['account_number'] = '*' * (len(account) - 4) + account[-4:]
        
        # Remove postcode in privacy mode
        data['postcode'] = None
        
        return data
    
    def _calculate_derived_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate additional values from extracted data including solar metrics"""
        derived = {}
        
        # Standard calculations
        if data.get('usage_kwh') and data.get('billing_days'):
            derived['daily_average_kwh'] = data['usage_kwh'] / data['billing_days']
        
        if data.get('total_amount') and data.get('usage_kwh'):
            derived['cost_per_kwh'] = data['total_amount'] / data['usage_kwh']
        
        if data.get('supply_charge') and data.get('billing_days'):
            derived['daily_supply_charge'] = data['supply_charge'] / data['billing_days']
        
        if data.get('usage_charge') and data.get('usage_kwh'):
            derived['usage_rate'] = data['usage_charge'] / data['usage_kwh']
        
        # Solar calculations
        if data.get('solar_export_kwh') and data.get('billing_days'):
            derived['daily_solar_export'] = data['solar_export_kwh'] / data['billing_days']
        
        if data.get('solar_credit_amount'):
            # Estimate annual solar savings
            derived['solar_savings_annual'] = data['solar_credit_amount'] * (365 / (data.get('billing_days') or 90))
        
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
    
    def _extract_state(self, text: str) -> Optional[str]:
        """Extract Australian state"""
        state_str = self._extract_pattern(text, 'state')
        if state_str:
            # Normalize state names
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
        found_fields = sum(1 for field in required_fields if data.get(field) is not None)
        
        base_confidence = found_fields / len(required_fields)
        
        # Bonus for additional fields
        optional_fields = ['account_number', 'state', 'billing_period', 'billing_days']
        found_optional = sum(1 for field in optional_fields if data.get(field) is not None)
        
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