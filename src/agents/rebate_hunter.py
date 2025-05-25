"""
Government Rebate Hunter Agent
File: src/agents/rebate_hunter.py
"""
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import sys
import os

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RebateHunterAgent:
    """
    Specialized agent for finding government energy rebates and incentives
    Focuses on Australian federal and state-specific rebates
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 2025 Australian Energy Rebates Database
        self.federal_rebates = {
            'energy_bill_relief': {
                'name': 'Energy Bill Relief Fund',
                'value': 300,
                'type': 'federal',
                'eligibility': 'All Australian households',
                'how_to_apply': 'Automatic credit applied to electricity bills',
                'deadline': 'Ongoing through 2025',
                'status': 'active',
                'description': 'Federal government relief for electricity bills'
            },
            'small_scale_renewable': {
                'name': 'Small-scale Renewable Energy Scheme (STCs)',
                'value': 200,  # Estimated average value
                'type': 'federal',
                'eligibility': 'Households with solar panels under 100kW',
                'how_to_apply': 'Through electricity retailer or solar installer',
                'deadline': 'Ongoing',
                'status': 'active',
                'description': 'Federal incentive for small-scale renewable energy systems',
                'requires_solar': True
            }
        }
        
        # State-specific rebates (2025 current programs)
        self.state_rebates = {
            'QLD': {
                'qld_electricity_rebate': {
                    'name': 'Queensland Electricity Rebate',
                    'value': 372,
                    'type': 'state',
                    'eligibility': 'QLD households',
                    'how_to_apply': 'Apply through Queensland Government website',
                    'deadline': 'Annual application - Check Qld.gov.au',
                    'status': 'active',
                    'description': 'Queensland government electricity rebate for households'
                },
                'qld_affordable_energy': {
                    'name': 'QLD Affordable Energy Plan',
                    'value': 200,
                    'type': 'state',
                    'eligibility': 'Eligible concession card holders in QLD',
                    'how_to_apply': 'Through electricity retailer',
                    'deadline': 'Ongoing',
                    'status': 'active',
                    'description': 'Additional support for eligible QLD households'
                },
                'qld_solar_bonus_legacy': {
                    'name': 'QLD Solar Bonus Scheme (Legacy)',
                    'value': 150,
                    'type': 'state',
                    'eligibility': 'Existing solar customers on legacy 44c scheme',
                    'how_to_apply': 'Check with current retailer',
                    'deadline': 'Legacy scheme - existing customers only',
                    'status': 'legacy',
                    'description': 'Legacy solar bonus for existing participants',
                    'requires_solar': True
                }
            },
            'NSW': {
                'nsw_energy_relief': {
                    'name': 'NSW Energy Bill Relief',
                    'value': 150,
                    'type': 'state',
                    'eligibility': 'NSW residents',
                    'how_to_apply': 'Apply through Service NSW',
                    'deadline': 'Check Service NSW website',
                    'status': 'active',
                    'description': 'NSW government energy bill relief'
                },
                'nsw_low_income': {
                    'name': 'NSW Low Income Household Rebate',
                    'value': 285,
                    'type': 'state',
                    'eligibility': 'Eligible concession card holders in NSW',
                    'how_to_apply': 'Through electricity retailer',
                    'deadline': 'Ongoing',
                    'status': 'active',
                    'description': 'Support for low income NSW households'
                },
                'nsw_family_energy': {
                    'name': 'NSW Family Energy Rebate',
                    'value': 180,
                    'type': 'state',
                    'eligibility': 'Families with eligible Family Tax Benefit',
                    'how_to_apply': 'Through Service NSW',
                    'deadline': 'Annual application',
                    'status': 'active',
                    'description': 'Support for NSW families'
                }
            },
            'VIC': {
                'vic_energy_compare': {
                    'name': 'Victorian Energy Compare Credit',
                    'value': 250,
                    'type': 'state',
                    'eligibility': 'VIC households who switch plans',
                    'how_to_apply': 'Through Victorian Energy Compare website',
                    'deadline': 'When switching plans',
                    'status': 'active',
                    'description': 'Credit for switching energy plans in Victoria'
                },
                'vic_power_saving': {
                    'name': 'Power Saving Bonus',
                    'value': 250,
                    'type': 'state',
                    'eligibility': 'VIC households',
                    'how_to_apply': 'Online application through Victorian Government',
                    'deadline': 'Limited time offer - check website',
                    'status': 'active',
                    'description': 'Victorian government power saving bonus'
                },
                'vic_winter_energy': {
                    'name': 'Winter Energy Payment',
                    'value': 200,
                    'type': 'state',
                    'eligibility': 'Eligible concession card holders in VIC',
                    'how_to_apply': 'Automatic payment for eligible customers',
                    'deadline': 'Winter period',
                    'status': 'seasonal',
                    'description': 'Winter energy support for eligible Victorians'
                }
            },
            'SA': {
                'sa_cost_of_living': {
                    'name': 'SA Cost of Living Concession',
                    'value': 190,
                    'type': 'state',
                    'eligibility': 'Eligible concession card holders in SA',
                    'how_to_apply': 'Through electricity retailer',
                    'deadline': 'Ongoing',
                    'status': 'active',
                    'description': 'South Australian cost of living support'
                }
            },
            'WA': {
                'wa_energy_assistance': {
                    'name': 'WA Energy Assistance Payment',
                    'value': 305,
                    'type': 'state',
                    'eligibility': 'Eligible concession card holders in WA',
                    'how_to_apply': 'Through electricity retailer or government',
                    'deadline': 'Annual application',
                    'status': 'active',
                    'description': 'Western Australian energy assistance'
                }
            },
            'TAS': {
                'tas_energy_supplement': {
                    'name': 'TAS Energy Supplement',
                    'value': 150,
                    'type': 'state',
                    'eligibility': 'Eligible Tasmanian households',
                    'how_to_apply': 'Through Service Tasmania',
                    'deadline': 'Ongoing',
                    'status': 'active',
                    'description': 'Tasmanian energy supplement for eligible households'
                }
            },
            'NT': {
                'nt_energy_concession': {
                    'name': 'NT Energy Concession',
                    'value': 180,
                    'type': 'state',
                    'eligibility': 'Eligible NT residents',
                    'how_to_apply': 'Through Territory government',
                    'deadline': 'Ongoing',
                    'status': 'active',
                    'description': 'Northern Territory energy concession'
                }
            },
            'ACT': {
                'act_utilities_concession': {
                    'name': 'ACT Utilities Concession',
                    'value': 220,
                    'type': 'state',
                    'eligibility': 'Eligible ACT concession card holders',
                    'how_to_apply': 'Through electricity retailer',
                    'deadline': 'Ongoing',
                    'status': 'active',
                    'description': 'ACT utilities concession for eligible households'
                }
            }
        }
        
        # Special category rebates
        self.special_rebates = {
            'low_income': {
                'name': 'Concession Card Holder Rebates',
                'value': 200,  # Variable by state
                'type': 'federal_state',
                'eligibility': 'Pension, healthcare, or low income card holders',
                'how_to_apply': 'Contact your electricity retailer',
                'deadline': 'Ongoing',
                'status': 'active',
                'description': 'Additional rebates for concession card holders'
            },
            'medical_equipment': {
                'name': 'Medical Equipment Energy Rebate',
                'value': 150,
                'type': 'state_specific',
                'eligibility': 'Households using life support equipment',
                'how_to_apply': 'Through electricity retailer with medical certificate',
                'deadline': 'Ongoing',
                'status': 'active',
                'description': 'Support for households with medical equipment'
            }
        }
        
    def find_applicable_rebates(self, state: str = 'QLD', has_solar: bool = False,
                              household_income: str = 'not_specified',
                              has_concession_card: bool = False,
                              has_medical_equipment: bool = False) -> Dict[str, Any]:
        """
        Main method to find applicable government rebates
        
        Args:
            state: Australian state code
            has_solar: Whether household has solar panels
            household_income: 'low', 'medium', 'high', or 'not_specified'
            has_concession_card: Whether household has concession card
            has_medical_equipment: Whether household uses medical equipment
            
        Returns:
            Dictionary with applicable rebates and total value
        """
        try:
            print(f"🎯 Searching for rebates in {state}...")
            
            applicable_rebates = []
            
            # Federal rebates (available to all)
            federal_rebates = self._get_federal_rebates(has_solar)
            applicable_rebates.extend(federal_rebates)
            
            # State-specific rebates
            state_rebates = self._get_state_rebates(state, has_solar)
            applicable_rebates.extend(state_rebates)
            
            # Special category rebates
            special_rebates = self._get_special_rebates(
                household_income, has_concession_card, has_medical_equipment, state
            )
            applicable_rebates.extend(special_rebates)
            
            # Calculate totals
            total_value = sum(rebate['value'] for rebate in applicable_rebates)
            high_value_rebates = [r['name'] for r in applicable_rebates if r['value'] >= 200]
            
            # Priority ranking
            priority_rebates = self._rank_rebates_by_priority(applicable_rebates)
            
            result = {
                'applicable_rebates': applicable_rebates,
                'total_rebate_value': total_value,
                'rebate_count': len(applicable_rebates),
                'high_value_rebates': high_value_rebates,
                'priority_rebates': priority_rebates,
                'state_analyzed': state,
                'search_criteria': {
                    'has_solar': has_solar,
                    'household_income': household_income,
                    'has_concession_card': has_concession_card,
                    'has_medical_equipment': has_medical_equipment
                },
                'estimated_application_time': self._estimate_application_time(applicable_rebates),
                'next_steps': self._generate_next_steps(priority_rebates),
                'confidence_level': 'high',
                'agent_version': '1.0_rebate_hunter',
                'search_timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ Found {len(applicable_rebates)} applicable rebates totaling ${total_value}")
            return result
            
        except Exception as e:
            self.logger.error(f"Rebate search failed: {e}")
            return self._get_error_response(str(e))
    
    def _get_federal_rebates(self, has_solar: bool) -> List[Dict[str, Any]]:
        """Get applicable federal rebates"""
        rebates = []
        
        # Energy Bill Relief (available to all)
        rebates.append(self.federal_rebates['energy_bill_relief'])
        
        # Solar-specific federal rebates
        if has_solar:
            rebates.append(self.federal_rebates['small_scale_renewable'])
        
        return rebates
    
    def _get_state_rebates(self, state: str, has_solar: bool) -> List[Dict[str, Any]]:
        """Get applicable state-specific rebates"""
        rebates = []
        
        state_programs = self.state_rebates.get(state, {})
        
        for rebate_key, rebate_info in state_programs.items():
            # Check if rebate requires solar
            if rebate_info.get('requires_solar', False) and not has_solar:
                continue
            
            # Include active and legacy rebates
            if rebate_info.get('status') in ['active', 'legacy', 'seasonal']:
                rebates.append(rebate_info)
        
        return rebates
    
    def _get_special_rebates(self, household_income: str, has_concession_card: bool,
                           has_medical_equipment: bool, state: str) -> List[Dict[str, Any]]:
        """Get special category rebates"""
        rebates = []
        
        # Low income / concession card rebates
        if household_income == 'low' or has_concession_card:
            rebates.append(self.special_rebates['low_income'])
        
        # Medical equipment rebate
        if has_medical_equipment:
            rebates.append(self.special_rebates['medical_equipment'])
        
        return rebates
    
    def _rank_rebates_by_priority(self, rebates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank rebates by priority (value, ease of application, likelihood)"""
        
        def calculate_priority_score(rebate):
            score = 0
            
            # Value weight (40%)
            value = rebate.get('value', 0)
            if value >= 300:
                score += 40
            elif value >= 200:
                score += 30
            elif value >= 100:
                score += 20
            else:
                score += 10
            
            # Ease of application (30%)
            how_to_apply = rebate.get('how_to_apply', '').lower()
            if 'automatic' in how_to_apply:
                score += 30
            elif 'retailer' in how_to_apply:
                score += 25
            elif 'online' in how_to_apply:
                score += 20
            else:
                score += 10
            
            # Status/reliability (30%)
            status = rebate.get('status', '')
            if status == 'active':
                score += 30
            elif status == 'seasonal':
                score += 20
            elif status == 'legacy':
                score += 15
            else:
                score += 5
            
            return score
        
        # Sort by priority score (highest first)
        ranked = sorted(rebates, key=calculate_priority_score, reverse=True)
        
        # Add priority ranks
        for i, rebate in enumerate(ranked, 1):
            rebate['priority_rank'] = i
            rebate['priority_score'] = calculate_priority_score(rebate)
        
        return ranked[:5]  # Top 5 priority rebates
    
    def _estimate_application_time(self, rebates: List[Dict[str, Any]]) -> str:
        """Estimate total time needed to apply for all rebates"""
        if not rebates:
            return "No applications needed"
        
        automatic_count = sum(1 for r in rebates if 'automatic' in r.get('how_to_apply', '').lower())
        online_count = sum(1 for r in rebates if 'online' in r.get('how_to_apply', '').lower())
        retailer_count = sum(1 for r in rebates if 'retailer' in r.get('how_to_apply', '').lower())
        other_count = len(rebates) - automatic_count - online_count - retailer_count
        
        if automatic_count == len(rebates):
            return "No applications needed - all automatic"
        elif len(rebates) <= 2:
            return "1-2 hours total application time"
        elif len(rebates) <= 4:
            return "2-4 hours total application time"
        else:
            return "4-6 hours total application time"
    
    def _generate_next_steps(self, priority_rebates: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable next steps for applying for rebates"""
        if not priority_rebates:
            return ["No rebates currently available"]
        
        next_steps = []
        
        # Group by application method
        automatic_rebates = [r for r in priority_rebates if 'automatic' in r.get('how_to_apply', '').lower()]
        retailer_rebates = [r for r in priority_rebates if 'retailer' in r.get('how_to_apply', '').lower()]
        online_rebates = [r for r in priority_rebates if 'online' in r.get('how_to_apply', '').lower()]
        
        if automatic_rebates:
            next_steps.append(f"✅ {len(automatic_rebates)} rebates are automatic - no action needed")
        
        if retailer_rebates:
            next_steps.append(f"📞 Contact your electricity retailer for {len(retailer_rebates)} rebates")
        
        if online_rebates:
            next_steps.append(f"💻 Apply online for {len(online_rebates)} rebates through government websites")
        
        # Add specific high-value recommendations
        for rebate in priority_rebates[:3]:
            if rebate['value'] >= 200:
                next_steps.append(f"🎯 Priority: Apply for {rebate['name']} (${rebate['value']}) - {rebate['how_to_apply']}")
        
        return next_steps
    
    def get_rebate_summary(self, search_result: Dict[str, Any]) -> str:
        """Generate human-readable summary of rebate search"""
        
        if search_result.get('error'):
            return f"Rebate Search Error: {search_result.get('message')}"
        
        total_value = search_result.get('total_rebate_value', 0)
        rebate_count = search_result.get('rebate_count', 0)
        state = search_result.get('state_analyzed', 'Unknown')
        
        if total_value == 0:
            return f"No applicable rebates found for {state}. Check eligibility criteria or try different search parameters."
        
        high_value_rebates = search_result.get('high_value_rebates', [])
        
        summary_parts = []
        summary_parts.append(f"Found {rebate_count} applicable rebates in {state} totaling ${total_value}.")
        
        if high_value_rebates:
            summary_parts.append(f"High-value rebates: {', '.join(high_value_rebates[:2])}.")
        
        application_time = search_result.get('estimated_application_time', '')
        if application_time:
            summary_parts.append(f"Estimated application time: {application_time}.")
        
        return " ".join(summary_parts)
    
    def _get_error_response(self, error_message: str) -> Dict[str, Any]:
        """Return error response when rebate search fails"""
        return {
            'error': True,
            'message': f'Rebate search failed: {error_message}',
            'search_timestamp': datetime.now().isoformat(),
            'applicable_rebates': [],
            'total_rebate_value': 0,
            'suggestions': [
                'Please check your state and household criteria',
                'Try again with different search parameters',
                'Contact your electricity retailer for current rebates'
            ]
        }


# Utility function for easy testing
def find_rebates_for_household(state: str = 'QLD', has_solar: bool = False,
                             household_income: str = 'not_specified') -> Dict[str, Any]:
    """
    Convenience function to find rebates for a household
    
    Args:
        state: Australian state code
        has_solar: Whether household has solar panels
        household_income: Income category
        
    Returns:
        Complete rebate search results
    """
    hunter = RebateHunterAgent()
    return hunter.find_applicable_rebates(state, has_solar, household_income)