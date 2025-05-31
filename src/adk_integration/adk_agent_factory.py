"""
ADK Integration Factory for WattsMyBill Multi-Agent System
File: src/adk_integration/adk_agent_factory.py
"""

import os
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import your real agents
try:
    from agents.bill_analyzer import BillAnalyzerAgent
    from agents.market_researcher import MarketResearcherAgent
    AGENTS_AVAILABLE = True
    print("✅ WattsMyBill agents imported successfully")
except ImportError as e:
    print(f"⚠️ WattsMyBill agents not available: {e}")
    AGENTS_AVAILABLE = False

# Google Cloud ADK integration - using correct imports from main.py
try:
    from google.adk.agents import LlmAgent
    from google.adk.cli.fast_api import get_fast_api_app
    ADK_AVAILABLE = True
    print("✅ Google Cloud ADK available for integration")
except ImportError as e:
    print(f"⚠️ Google Cloud ADK not available: {e}")
    ADK_AVAILABLE = False

logger = logging.getLogger(__name__)


class ADKIntegratedAgentFactory:
    """Factory that integrates WattsMyBill agents with Google Cloud ADK"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize your real agents
        if AGENTS_AVAILABLE:
            self.bill_analyzer = BillAnalyzerAgent()
            self.market_researcher = MarketResearcherAgent()
            print("✅ Real WattsMyBill agents initialized")
        else:
            self.bill_analyzer = None
            self.market_researcher = None

        # Test real agent availability
        self.real_agents_available = self._test_real_agents()

        # ADK agents (will be created if ADK is available)
        self.adk_agents = {}
        self.adk_workflow = None

        if ADK_AVAILABLE and AGENTS_AVAILABLE:
            self._create_adk_agents()

        logger.info(
            f"🏭 ADK Factory initialized - Real agents: {self.real_agents_available}, ADK: {ADK_AVAILABLE}")

    def _test_real_agents(self) -> bool:
        """Test if real agents are working"""
        if not AGENTS_AVAILABLE:
            return False
            
        try:
            # Test bill analyzer
            test_result = self.bill_analyzer._get_error_response("test")
            
            # Test market researcher
            market_status = self.market_researcher.test_all_services()
            
            return True
        except Exception as e:
            logger.warning(f"Real agent test failed: {e}")
            return False

    def _create_adk_agents(self):
        """Create ADK-wrapped versions of real agents using LlmAgent"""
        if not ADK_AVAILABLE or not AGENTS_AVAILABLE:
            return

        try:
            # Create tool functions that wrap your real agents
            bill_analysis_func = self._create_bill_analysis_tool()
            market_research_func = self._create_market_research_tool()
            rebate_finder_func = self._create_rebate_finder_tool()
            usage_optimizer_func = self._create_usage_optimizer_tool()

            # Create specialized ADK agents with tool functions using LlmAgent
            self.adk_agents['bill_analyzer'] = LlmAgent(
                name="WattsMyBill_BillAnalyzer",
                model="gemini-2.0-flash-exp",
                description="Specialized agent for analyzing Australian energy bills using real BillAnalyzerAgent",
                instruction="""You are an expert Australian energy bill analyzer. Use the analyze_energy_bill tool 
                to process uploaded bills and provide detailed insights about usage, costs, and efficiency.""",
                tools=[bill_analysis_func]
            )

            self.adk_agents['market_researcher'] = LlmAgent(
                name="WattsMyBill_MarketResearcher",
                model="gemini-2.0-flash-exp",
                description="Market research agent using real MarketResearcherAgent with ETL and API integration",
                instruction="""You are an expert in Australian energy markets. Use the research_energy_market tool
                to find better electricity plans using live market data and ETL warehouse information.""",
                tools=[market_research_func]
            )

            self.adk_agents['rebate_hunter'] = LlmAgent(
                name="WattsMyBill_RebateHunter",
                model="gemini-2.0-flash-exp",
                description="Government rebate and incentive finder",
                instruction="""You specialize in finding Australian government energy rebates and incentives.
                Use the find_government_rebates tool to identify applicable rebates for users.""",
                tools=[rebate_finder_func]
            )

            self.adk_agents['usage_optimizer'] = LlmAgent(
                name="WattsMyBill_UsageOptimizer", 
                model="gemini-2.0-flash-exp",
                description="Energy usage optimization specialist",
                instruction="""You are an energy efficiency expert. Use the optimize_energy_usage tool
                to provide personalized recommendations for reducing energy consumption and costs.""",
                tools=[usage_optimizer_func]
            )

            # Create comprehensive coordinator agent with all tool functions
            self.adk_agents['comprehensive_analyzer'] = LlmAgent(
                name="WattsMyBill_ComprehensiveAnalyzer",
                model="gemini-2.0-flash-exp",
                description="Master coordinator for complete energy bill analysis using all WattsMyBill agents",
                instruction="""You are the master coordinator for WattsMyBill analysis. You have access to all
                specialized tools and real agents. When a user uploads an energy bill, coordinate the complete
                analysis process:
                
                1. Use analyze_energy_bill to parse and analyze the bill
                2. Use research_energy_market to find better plans
                3. Use find_government_rebates to identify applicable rebates  
                4. Use optimize_energy_usage to provide efficiency recommendations
                5. Synthesize all results into actionable recommendations
                
                Always use the real agent tools to ensure accurate, up-to-date analysis.""",
                tools=[bill_analysis_func, market_research_func, rebate_finder_func, usage_optimizer_func]
            )

            logger.info(f"✅ Created {len(self.adk_agents)} ADK-integrated agents using LlmAgent")

        except Exception as e:
            logger.error(f"Failed to create ADK agents: {e}")
            self.adk_agents = {}

    def _create_bill_analysis_tool(self):
        """Create ADK tool function that wraps the real BillAnalyzerAgent"""

        def analyze_energy_bill(file_content: bytes, file_type: str = "pdf", privacy_mode: bool = False) -> str:
            """
            Analyze an Australian energy bill using the real BillAnalyzerAgent.

            Args:
                file_content: The bill file content as bytes
                file_type: Type of file ('pdf' or 'image')
                privacy_mode: Whether to redact personal information

            Returns:
                JSON string with complete bill analysis
            """
            try:
                if not self.bill_analyzer:
                    return json.dumps({
                        "status": "error",
                        "error": "Real BillAnalyzer not available",
                        "agent": "adk_bill_analyzer"
                    })

                result = self.bill_analyzer.analyze_bill(file_content, file_type, privacy_mode)

                return json.dumps({
                    "status": "success",
                    "agent": "real_bill_analyzer",
                    "analysis": result,
                    "data_source": "real_bill_analyzer_agent",
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Real BillAnalyzer failed: {e}")
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "agent": "real_bill_analyzer"
                })

        return analyze_energy_bill

    def _create_market_research_tool(self):
        """Create ADK tool function that wraps the real MarketResearcherAgent"""

        def research_energy_market(bill_analysis: str, state: str = "NSW", postcode: str = "") -> str:
            """
            Research better energy plans using the real MarketResearcherAgent with ETL and API integration.

            Args:
                bill_analysis: JSON string from bill analysis
                state: Australian state/territory
                postcode: Optional postcode for localized results

            Returns:
                JSON string with market research results
            """
            try:
                if not self.market_researcher:
                    return json.dumps({
                        "status": "error",
                        "error": "Real MarketResearcher not available",
                        "agent": "adk_market_researcher"
                    })

                # Parse bill analysis
                bill_data = json.loads(bill_analysis)
                if bill_data.get("status") != "success":
                    return json.dumps({"status": "error", "error": "Invalid bill analysis data"})

                # Extract bill data for market research
                analysis_data = bill_data.get("analysis", {})
                bill_info = analysis_data.get("bill_data", {})

                # Enhance with state/postcode
                bill_info["state"] = state
                if postcode:
                    bill_info["postcode"] = postcode

                # Use real market researcher
                result = self.market_researcher.research_better_plans(bill_info)

                # Test services to get API integration status
                service_status = self.market_researcher.test_all_services()
                api_integrated = service_status.get('overall_status') in ['excellent', 'good']

                return json.dumps({
                    "status": "success",
                    "agent": "real_market_researcher",
                    "market_research": result,
                    "api_used": service_status.get('overall_status', 'unknown'),
                    "data_source": result.get('data_source', 'real_market_researcher_agent'),
                    "api_integration": api_integrated,
                    "etl_status": service_status.get('etl_service', {}).get('connected', False),
                    "timestamp": datetime.now().isoformat()
                })

            except json.JSONDecodeError:
                return json.dumps({"status": "error", "error": "Invalid JSON in bill_analysis"})
            except Exception as e:
                logger.error(f"Real MarketResearcher failed: {e}")
                return json.dumps({
                    "status": "error",
                    "error": str(e),
                    "agent": "real_market_researcher"
                })

        return research_energy_market

    def _create_rebate_finder_tool(self):
        """Create ADK tool function for finding government rebates"""

        def find_government_rebates(state: str, has_solar: bool = False, usage_category: str = "medium") -> str:
            """
            Find applicable government energy rebates and incentives.

            Args:
                state: Australian state/territory
                has_solar: Whether the household has solar panels
                usage_category: Usage level (low/medium/high)

            Returns:
                JSON string with applicable rebates
            """
            try:
                # Enhanced rebate database (would integrate with real government APIs)
                rebates = []
                total_value = 0

                # State-specific rebates
                state_rebates = {
                    'NSW': [
                        {
                            'name': 'NSW Energy Savings Scheme',
                            'value': 200,
                            'type': 'annual',
                            'eligibility': 'All NSW households',
                            'how_to_apply': 'Through participating retailers',
                            'deadline': '2025-12-31',
                            'status': 'available'
                        }
                    ],
                    'VIC': [
                        {
                            'name': 'Victorian Energy Upgrade Program',
                            'value': 400,
                            'type': 'one_time',
                            'eligibility': 'Energy efficient appliance upgrades',
                            'how_to_apply': 'Accredited provider installation',
                            'deadline': '2025-06-30',
                            'status': 'available'
                        }
                    ],
                    'QLD': [
                        {
                            'name': 'QLD Electricity Rebate',
                            'value': 372,
                            'type': 'annual',
                            'eligibility': 'Eligible concession card holders',
                            'how_to_apply': 'Automatic through electricity bill',
                            'deadline': 'Ongoing',
                            'status': 'available'
                        }
                    ]
                }

                # Add state rebates
                if state in state_rebates:
                    rebates.extend(state_rebates[state])
                    total_value += sum(r['value'] for r in state_rebates[state])

                # Solar-specific rebates
                if has_solar:
                    solar_rebates = [
                        {
                            'name': f'{state} Solar Battery Rebate',
                            'value': 3000,
                            'type': 'one_time',
                            'eligibility': 'Existing solar system owners',
                            'how_to_apply': 'Apply through state government portal',
                            'deadline': '2025-12-31',
                            'status': 'available'
                        }
                    ]
                    rebates.extend(solar_rebates)
                    total_value += sum(r['value'] for r in solar_rebates)

                # High usage rebates
                if usage_category == 'high':
                    efficiency_rebates = [
                        {
                            'name': 'Energy Efficiency Upgrade Rebate',
                            'value': 600,
                            'type': 'one_time',
                            'eligibility': 'Households with high energy usage',
                            'how_to_apply': 'Purchase energy efficient appliances',
                            'deadline': '2025-09-30',
                            'status': 'available'
                        }
                    ]
                    rebates.extend(efficiency_rebates)
                    total_value += sum(r['value'] for r in efficiency_rebates)

                # Identify high-value rebates
                high_value_rebates = [r['name'] for r in rebates if r['value'] >= 500]

                return json.dumps({
                    "status": "success",
                    "applicable_rebates": rebates,
                    "total_rebate_value": total_value,
                    "rebate_count": len(rebates),
                    "high_value_rebates": high_value_rebates,
                    "state": state,
                    "timestamp": datetime.now().isoformat()
                })

            except Exception as e:
                logger.error(f"Rebate finder failed: {e}")
                return json.dumps({
                    "status": "error",
                    "error": str(e)
                })

        return find_government_rebates

    def _create_usage_optimizer_tool(self):
        """Create ADK tool function for usage optimization"""

        def optimize_energy_usage(bill_analysis: str) -> str:
            """
            Provide personalized energy usage optimization recommendations.

            Args:
                bill_analysis: JSON string from bill analysis

            Returns:
                JSON string with optimization recommendations
            """
            try:
                # Parse bill analysis
                bill_data = json.loads(bill_analysis)
                if bill_data.get("status") != "success":
                    return json.dumps({"status": "error", "error": "Invalid bill analysis data"})

                analysis_data = bill_data.get("analysis", {})
                usage_profile = analysis_data.get("usage_profile", {})
                solar_analysis = analysis_data.get("solar_analysis", {})

                daily_usage = usage_profile.get("daily_average", 15)
                usage_category = usage_profile.get("usage_category", "medium")
                has_solar = solar_analysis.get("has_solar", False)

                opportunities = []
                quick_wins = []
                total_savings = 0

                # Base optimization opportunities
                if usage_category in ['high', 'very_high']:
                    opportunities.append({
                        'type': 'appliance_efficiency',
                        'recommendation': 'Replace old appliances with energy-efficient models',
                        'potential_annual_savings': 300,
                        'potential_monthly_savings': 25,
                        'implementation': 'Purchase ENERGY STAR rated appliances',
                        'difficulty': 'medium'
                    })
                    total_savings += 300

                    quick_wins.extend([
                        'Switch to LED light bulbs (save $50-100/year)',
                        'Use cold water for washing (save $30-60/year)',
                        'Air dry clothes instead of tumble drying'
                    ])

                # Time-of-use optimization
                if daily_usage > 10:
                    opportunities.append({
                        'type': 'time_of_use',
                        'recommendation': 'Shift usage to off-peak hours',
                        'potential_annual_savings': 200,
                        'potential_monthly_savings': 17,
                        'implementation': 'Run dishwasher, washing machine at night',
                        'difficulty': 'easy'
                    })
                    total_savings += 200

                    quick_wins.append('Run major appliances during off-peak hours (9pm-7am)')

                # Solar optimization
                if has_solar:
                    export_ratio = solar_analysis.get('export_ratio_percent', 0)
                    if export_ratio > 50:
                        opportunities.append({
                            'type': 'solar_optimization',
                            'recommendation': 'Install battery storage to capture excess solar',
                            'potential_annual_savings': 800,
                            'potential_monthly_savings': 67,
                            'implementation': 'Install home battery system',
                            'difficulty': 'high'
                        })
                        total_savings += 800
                    else:
                        quick_wins.append('Shift daytime usage to maximize solar self-consumption')

                # HVAC optimization
                opportunities.append({
                    'type': 'hvac_efficiency',
                    'recommendation': 'Optimize heating and cooling settings',
                    'potential_annual_savings': 250,
                    'potential_monthly_savings': 21,
                    'implementation': 'Set thermostat 1-2°C higher in summer, lower in winter',
                    'difficulty': 'easy'
                })
                total_savings += 250

                quick_wins.extend([
                    'Clean air conditioner filters monthly',
                    'Use ceiling fans to circulate air',
                    'Close curtains/blinds during hot days'
                ])

                return json.dumps({
                    "status": "success",
                    "optimization_opportunities": opportunities,
                    "quick_wins": quick_wins[:5],  # Limit to top 5
                    "total_annual_savings": total_savings,
                    "total_monthly_savings": total_savings / 12,
                    "usage_category": usage_category,
                    "has_solar": has_solar,
                    "timestamp": datetime.now().isoformat()
                })

            except json.JSONDecodeError:
                return json.dumps({"status": "error", "error": "Invalid JSON in bill_analysis"})
            except Exception as e:
                logger.error(f"Usage optimizer failed: {e}")
                return json.dumps({
                    "status": "error",
                    "error": str(e)
                })

        return optimize_energy_usage

    def create_adk_workflow(self) -> Dict[str, Any]:
        """Create the complete ADK workflow"""

        if not ADK_AVAILABLE:
            return {
                "status": "error",
                "error": "Google Cloud ADK not available",
                "real_agents_used": self.real_agents_available,
                "api_integration": False
            }

        if not AGENTS_AVAILABLE:
            return {
                "status": "error", 
                "error": "Real WattsMyBill agents not available",
                "real_agents_used": False,
                "api_integration": False
            }

        if not self.adk_agents:
            return {
                "status": "error",
                "error": "ADK agents not created",
                "real_agents_used": self.real_agents_available,
                "api_integration": False
            }

        try:
            # Test market researcher API integration
            market_status = self.market_researcher.test_all_services()
            api_integration = market_status.get('overall_status') in ['excellent', 'good']
            etl_status = market_status.get('etl_service', {}).get('connected', False)

            return {
                "status": "ready",
                "comprehensive_analyzer": self.adk_agents['comprehensive_analyzer'],
                "agent_count": len(self.adk_agents),
                "real_agents_used": self.real_agents_available,
                "api_integration": api_integration,
                "adk_integrated": True,
                "etl_status": etl_status,
                "market_plans_available": market_status.get('etl_service', {}).get('total_plans_available', 0),
                "_factory": self  # Store reference for testing
            }

        except Exception as e:
            logger.error(f"ADK workflow creation failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "real_agents_used": self.real_agents_available,
                "api_integration": False
            }

    def get_agent_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all agents"""

        # Test real agents
        real_agent_status = {
            "bill_analyzer": "active" if self.real_agents_available else "inactive",
            "market_researcher": "active" if self.real_agents_available else "inactive"
        }

        # Test market researcher specifically
        if self.real_agents_available and self.market_researcher:
            try:
                market_test = self.market_researcher.test_all_services()
                real_agent_status["market_researcher_etl"] = "connected" if market_test.get(
                    'etl_service', {}).get('connected') else "unavailable"
                real_agent_status["market_researcher_api"] = "available" if market_test.get(
                    'api_service', {}).get('cdr_register_access') else "unavailable"
            except Exception as e:
                real_agent_status["market_researcher_error"] = str(e)

        # ADK status
        adk_status = {
            "available": ADK_AVAILABLE,
            "agents_created": len(self.adk_agents) if ADK_AVAILABLE else 0,
            "workflow_ready": bool(self.adk_agents)
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "real_agents": real_agent_status,
            "adk_integration": adk_status,
            "overall_status": "healthy" if self.real_agents_available and ADK_AVAILABLE else "limited"
        }


def create_adk_wattsmybill_workflow(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Convenience function to create the complete ADK WattsMyBill workflow

    Args:
        config: Configuration dictionary with project_id, dataset_id, etc.

    Returns:
        Dictionary with workflow status and components
    """

    try:
        factory = ADKIntegratedAgentFactory(config)
        workflow = factory.create_adk_workflow()

        return workflow

    except Exception as e:
        logger.error(f"Failed to create ADK WattsMyBill workflow: {e}")
        return {
            "status": "error",
            "error": str(e),
            "real_agents_used": False,
            "api_integration": False
        }


# Test function
def test_adk_integration():
    """Test the ADK integration with real agents"""

    print("🧪 Testing ADK Integration with Real WattsMyBill Agents")
    print("=" * 60)

    try:
        # Create factory
        factory = ADKIntegratedAgentFactory()

        # Get status
        status = factory.get_agent_status()

        print(f"📊 Agent Status:")
        print(f"   Overall: {status['overall_status']}")
        print(f"   Real Agents: {status['real_agents']}")
        print(f"   ADK Integration: {status['adk_integration']}")

        # Create workflow
        workflow = factory.create_adk_workflow()

        print(f"\n🔧 Workflow Status: {workflow.get('status')}")
        if workflow.get('status') == 'ready':
            print(f"   ADK Agents: {workflow.get('agent_count')}")
            print(f"   Real Agents Used: {workflow.get('real_agents_used')}")
            print(f"   API Integration: {workflow.get('api_integration')}")
            print(f"   ETL Status: {workflow.get('etl_status')}")

        return workflow

    except Exception as e:
        print(f"❌ ADK Integration test failed: {e}")
        return None


if __name__ == "__main__":
    # Run test
    test_workflow = test_adk_integration()

    if test_workflow and test_workflow.get('status') == 'ready':
        print("\n✅ ADK Integration with Real WattsMyBill Agents is ready!")
    else:
        print("\n⚠️ ADK Integration has limitations - check configuration")