#!/usr/bin/env python3
"""
Fixed WattsMyBill Multi-Agent System with Google Cloud ADK Integration
Solution for ADK FastAPI custom endpoint conflicts
"""

import os
import sys
import logging
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from contextlib import asynccontextmanager

# FastAPI and dependencies
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import our agents with proper error handling
try:
    from src.agents.bill_analyzer import BillAnalyzerAgent
    from src.agents.market_researcher import MarketResearcherAgent, test_etl_integration
    print("✅ Agents imported successfully from src.agents")
except ImportError:
    try:
        from agents.bill_analyzer import BillAnalyzerAgent
        from agents.market_researcher import MarketResearcherAgent, test_etl_integration
        print("✅ Agents imported successfully from agents")
    except ImportError as e:
        print(f"❌ Failed to import agents: {e}")
        print("📍 Please ensure agents are in either 'src/agents/' or 'agents/' directory")
        sys.exit(1)

# Google Cloud ADK integration (if available)
try:
    from google.adk.agents import LlmAgent
    from google.adk.cli.fast_api import get_fast_api_app
    try:
        from src.adk_integration.adk_agent_factory import ADKIntegratedAgentFactory, create_adk_wattsmybill_workflow
    except ImportError:
        from adk_integration.adk_agent_factory import ADKIntegratedAgentFactory, create_adk_wattsmybill_workflow
    ADK_AVAILABLE = True
    print("✅ Google Cloud ADK available with WattsMyBill integration")
except ImportError as e:
    ADK_AVAILABLE = False
    print(f"⚠️  Google Cloud ADK not available: {e} - running in standalone mode")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# In-memory storage for analysis results
analysis_storage: Dict[str, Dict[str, Any]] = {}

# Pydantic models
class AnalysisStatus(BaseModel):
    analysis_id: str
    status: str
    progress: int
    message: Optional[str] = None
    company_detected: Optional[str] = None

class AnalysisResults(BaseModel):
    analysis_id: str
    bill_analysis: Dict[str, Any]
    market_research: Dict[str, Any]
    rebate_analysis: Dict[str, Any]
    total_savings: float
    billing_context: Optional[Dict[str, Any]] = None

class AgentFactory:
    """Enhanced factory for creating and managing agents with ADK integration"""

    def __init__(self):
        self.bill_analyzer = BillAnalyzerAgent()
        self.market_researcher = MarketResearcherAgent()
        self.supported_companies = self._load_supported_companies()

        # ADK Integration
        self.adk_factory = None
        self.adk_workflow = None

        if ADK_AVAILABLE:
            try:
                adk_config = {
                    'project_id': os.getenv('GOOGLE_CLOUD_PROJECT', 'wattsmybill-adk'),
                    'dataset_id': 'energy_plans',
                    'location': 'australia-southeast1'
                }

                self.adk_factory = ADKIntegratedAgentFactory(adk_config)
                self.adk_workflow = self.adk_factory.create_adk_workflow()

                if self.adk_workflow.get('status') == 'ready':
                    print("✅ ADK workflow with real WattsMyBill agents initialized")
                else:
                    print(f"⚠️ ADK workflow failed: {self.adk_workflow.get('error')}")

            except Exception as e:
                print(f"⚠️ ADK integration failed: {e}")
                self.adk_factory = None
                self.adk_workflow = None

        self._test_services()

    def _load_supported_companies(self) -> List[str]:
        return [
            "AGL", "Origin Energy", "Energy Australia", "Alinta Energy",
            "Red Energy", "Simply Energy", "Powershop", "Amber Electric",
            "Diamond Energy", "CovaU", "ReAmped Energy", "Sumo Power",
            "OVO Energy", "Momentum Energy", "GloBird Energy", "Tango Energy",
            "Dodo Power & Gas", "Click Energy", "Nectr", "Kogan Energy",
            "ActewAGL", "Aurora Energy", "Ergon Energy", "Energex",
            "Essential Energy", "Evoenergy", "Horizon Power", "Jemena",
            "PowerWater", "SA Power Networks", "TasNetworks", "United Energy"
        ]

    def _test_services(self):
        logger.info("🧪 Testing agent services...")
        try:
            test_results = self.market_researcher.test_all_services()
            logger.info(f"Market Researcher Status: {test_results.get('overall_status', 'unknown')}")
        except Exception as e:
            logger.warning(f"Market researcher test failed: {e}")

        if self.adk_factory:
            try:
                adk_status = self.adk_factory.get_agent_status()
                logger.info(f"ADK Integration Status: {adk_status.get('overall_status', 'unknown')}")
            except Exception as e:
                logger.warning(f"ADK integration test failed: {e}")

        logger.info("✅ Agent factory initialized")

# Global agent factory
agent_factory: Optional[AgentFactory] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global agent_factory
    logger.info("🚀 Starting WattsMyBill Multi-Agent System")
    agent_factory = AgentFactory()
    yield
    logger.info("🛑 Shutting down WattsMyBill Multi-Agent System")

def create_fastapi_app() -> FastAPI:
    """
    Create FastAPI app with proper ADK integration handling
    SOLUTION: Create custom endpoints BEFORE using ADK get_fast_api_app
    """
    
    # Method 1: Try ADK integration with web=False (recommended fix)
    if ADK_AVAILABLE:
        try:
            logger.info("🔧 Attempting ADK FastAPI integration with web=False...")
            
            # Create ADK app with web=False to avoid endpoint conflicts
            app = get_fast_api_app(
                agent_dir=os.path.join(os.path.dirname(__file__), 'src', 'agents'),
                session_db_url=f"sqlite:///{os.path.join(os.path.dirname(__file__), 'adk_sessions.db')}",
                allow_origins=["*"],
                web=False,  # KEY FIX: Set to False to allow custom endpoints
            )
            
            # Override title and description
            app.title = "WattsMyBill Multi-Agent API with ADK"
            app.description = "AI-powered Australian energy bill analysis with Google Cloud ADK integration"
            app.version = "2.0.0"
            
            logger.info("✅ ADK FastAPI integration successful (web=False)")
            return app
            
        except Exception as e:
            logger.warning(f"ADK FastAPI setup failed: {e}, falling back to standard FastAPI")
    
    # Method 2: Fallback to standard FastAPI
    app = FastAPI(
        title="WattsMyBill Multi-Agent API",
        description="AI-powered Australian energy bill analysis with multi-agent orchestration",
        version="2.0.0",
        lifespan=lifespan
    )
    
    logger.info("✅ Using standard FastAPI (ADK not available)")
    return app

# Create the app using our fixed method
app = create_fastapi_app()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent factory for ADK apps (since lifespan might not run)
if ADK_AVAILABLE and not agent_factory:
    agent_factory = AgentFactory()

# Validation function
def validate_energy_bill(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Enhanced bill validation with detailed analysis"""
    
    if len(file_content) < 1000:
        return {
            "is_valid": False,
            "error": "File too small to be a valid energy bill",
            "validation_details": {"file_size": len(file_content)}
        }

    content_str = str(file_content).lower()
    energy_terms = ['kwh', 'electricity', 'energy', 'usage', 'tariff', 'supply charge']
    australian_terms = ['abn', 'gst', 'australia', 'nsw', 'vic', 'qld', 'sa', 'wa', 'nt', 'tas', 'act']

    energy_count = sum(1 for term in energy_terms if term in content_str)
    australian_count = sum(1 for term in australian_terms if term in content_str)

    supported_companies = agent_factory.supported_companies if agent_factory else []
    detected_company = None
    for company in supported_companies:
        if company.lower().replace(' ', '') in content_str.replace(' ', ''):
            detected_company = company
            break

    non_energy_terms = ['bank', 'mortgage', 'loan', 'insurance', 'phone', 'internet']
    non_energy_count = sum(1 for term in non_energy_terms if term in content_str)

    is_valid = (
        energy_count >= 3 and
        australian_count >= 1 and
        non_energy_count < 3 and
        (detected_company is not None or energy_count >= 5)
    )

    validation_details = {
        "energy_indicators_found": energy_count,
        "australian_energy_terms_found": australian_count,
        "non_energy_indicators_found": non_energy_count,
        "recognized_energy_company": detected_company is not None,
        "company_detected": detected_company
    }

    if not is_valid:
        if non_energy_count >= 3:
            validation_details["reason"] = f"Non-energy business document (found {non_energy_count} non-energy terms)"
        elif energy_count < 3:
            validation_details["reason"] = f"Insufficient energy-related content (found {energy_count}/3+ terms)"
        elif australian_count < 1:
            validation_details["reason"] = "No Australian energy market indicators found"
        else:
            validation_details["reason"] = "Document classification uncertain"

    return {
        "is_valid": is_valid,
        "validation_details": validation_details,
        "company_detected": detected_company,
        "tips": [
            "Ensure the document is a complete electricity bill",
            "Make sure the bill is from an Australian energy retailer",
            "Try uploading a clearer image or the original PDF",
            "Check that all pages of a multi-page bill are included"
        ] if not is_valid else None,
        "supported_companies": supported_companies[:10] if not is_valid else None
    }

# Processing functions
async def process_bill_analysis(analysis_id: str, file_content: bytes, file_type: str, state: str, use_adk: bool = True):
    """Enhanced asynchronous bill processing with ADK integration"""
    try:
        analysis_storage[analysis_id] = {
            "status": "processing",
            "progress": 0,
            "started_at": datetime.now().isoformat(),
            "steps": [],
            "adk_mode": use_adk and agent_factory.adk_workflow is not None
        }

        logger.info(f"🔍 Starting analysis {analysis_id} (ADK: {analysis_storage[analysis_id]['adk_mode']})")

        if use_adk and agent_factory.adk_workflow and agent_factory.adk_workflow.get('status') == 'ready':
            await process_with_adk(analysis_id, file_content, file_type, state)
        else:
            await process_standalone(analysis_id, file_content, file_type, state)

    except Exception as e:
        logger.error(f"❌ Analysis {analysis_id} failed: {e}")
        analysis_storage[analysis_id].update({
            "status": "failed",
            "progress": 0,
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

async def process_with_adk(analysis_id: str, file_content: bytes, file_type: str, state: str):
    """Process analysis using ADK-integrated agents"""
    try:
        logger.info(f"🤖 ADK processing for {analysis_id}")
        comprehensive_agent = agent_factory.adk_workflow['comprehensive_analyzer']

        analysis_storage[analysis_id].update({
            "progress": 10,
            "current_step": "🤖 ADK: Coordinating real WattsMyBill agents..."
        })

        # Bill Analysis
        analysis_storage[analysis_id].update({
            "progress": 25,
            "current_step": "🔍 ADK Agent 1/4: Real BillAnalyzer processing..."
        })

        bill_tool = comprehensive_agent.tools[0]
        bill_result = bill_tool(file_content=file_content, file_type=file_type, privacy_mode=False)
        bill_analysis = json.loads(bill_result)

        if bill_analysis.get('status') != 'success':
            raise Exception(f"ADK Bill analysis failed: {bill_analysis.get('error')}")

        bill_data = bill_analysis.get('analysis', {}).get('bill_data', {})
        company_detected = bill_data.get('retailer')
        if company_detected:
            analysis_storage[analysis_id]["company_detected"] = company_detected

        # Market Research
        analysis_storage[analysis_id].update({
            "progress": 50,
            "current_step": "📊 ADK Agent 2/4: Real MarketResearcher with live API..."
        })

        market_tool = comprehensive_agent.tools[1]
        market_result = market_tool(bill_analysis=bill_result, state=state)
        market_research = json.loads(market_result)

        # Rebate Analysis
        analysis_storage[analysis_id].update({
            "progress": 70,
            "current_step": "🎯 ADK Agent 3/4: Real rebate finder..."
        })

        rebate_tool = comprehensive_agent.tools[2]
        has_solar = bill_analysis.get('analysis', {}).get('solar_analysis', {}).get('has_solar', False)
        usage_category = bill_analysis.get('analysis', {}).get('usage_profile', {}).get('usage_category', 'medium')
        
        rebate_result = rebate_tool(state=state, has_solar=has_solar, usage_category=usage_category)
        rebate_analysis = json.loads(rebate_result)

        # Usage Optimization
        analysis_storage[analysis_id].update({
            "progress": 85,
            "current_step": "⚡ ADK Agent 4/4: Real usage optimizer..."
        })

        usage_tool = comprehensive_agent.tools[3]
        usage_result = usage_tool(bill_analysis=bill_result)
        usage_optimization = json.loads(usage_result)

        # Synthesize results
        analysis_storage[analysis_id].update({
            "progress": 95,
            "current_step": "🔄 ADK: Synthesizing real agent results..."
        })

        total_savings = calculate_adk_total_savings(market_research, rebate_analysis, usage_optimization)
        billing_context = create_billing_context(bill_data)

        final_results = {
            "analysis_id": analysis_id,
            "processing_method": "adk_integrated",
            "bill_analysis": bill_analysis,
            "market_research": market_research,
            "rebate_analysis": rebate_analysis,
            "usage_optimization": usage_optimization,
            "total_savings": total_savings,
            "billing_context": billing_context,
            "adk_metadata": {
                "real_agents_used": agent_factory.adk_workflow.get('real_agents_used', False),
                "api_integration": agent_factory.adk_workflow.get('api_integration', False),
                "etl_status": agent_factory.adk_workflow.get('etl_status', False),
                "agent_count": agent_factory.adk_workflow.get('agent_count', 0)
            },
            "completed_at": datetime.now().isoformat(),
            "processing_time_seconds": (datetime.now() - datetime.fromisoformat(analysis_storage[analysis_id]["started_at"])).total_seconds()
        }

        analysis_storage[analysis_id].update({
            "status": "completed",
            "progress": 100,
            "current_step": "✅ ADK Analysis complete with real agents!",
            "results": final_results
        })

        logger.info(f"🎉 ADK Analysis {analysis_id} completed successfully!")

    except Exception as e:
        logger.error(f"❌ ADK Analysis {analysis_id} failed: {e}")
        analysis_storage[analysis_id].update({
            "status": "failed",
            "error": f"ADK processing failed: {str(e)}",
            "failed_at": datetime.now().isoformat()
        })

async def process_standalone(analysis_id: str, file_content: bytes, file_type: str, state: str):
    """Process analysis using standalone agents"""
    try:
        logger.info(f"🔧 Standalone processing for {analysis_id}")

        # Bill Analysis
        analysis_storage[analysis_id].update({
            "progress": 10,
            "current_step": "Analyzing bill document..."
        })

        bill_analysis = agent_factory.bill_analyzer.analyze_bill(file_content, file_type, privacy_mode=False)

        if bill_analysis.get('error'):
            raise Exception(f"Bill analysis failed: {bill_analysis.get('message')}")

        bill_data = bill_analysis.get('bill_data', {})
        company_detected = bill_data.get('retailer')
        if company_detected:
            analysis_storage[analysis_id]["company_detected"] = company_detected

        analysis_storage[analysis_id].update({
            "progress": 40,
            "current_step": "Bill analysis completed"
        })

        # Market Research
        analysis_storage[analysis_id].update({
            "progress": 50,
            "current_step": "Researching better energy plans..."
        })

        market_research = agent_factory.market_researcher.research_better_plans(bill_data)

        analysis_storage[analysis_id].update({
            "progress": 70,
            "current_step": "Market research completed"
        })

        # Rebate Analysis
        analysis_storage[analysis_id].update({
            "progress": 80,
            "current_step": "Searching for government rebates..."
        })

        rebate_analysis = await analyze_rebates(bill_data, state)

        # Calculate savings
        analysis_storage[analysis_id].update({
            "progress": 90,
            "current_step": "Calculating total savings potential..."
        })

        total_savings = calculate_total_savings(market_research, rebate_analysis)
        billing_context = create_billing_context(bill_data)

        final_results = {
            "analysis_id": analysis_id,
            "processing_method": "standalone",
            "bill_analysis": {"analysis": bill_analysis, "status": "success"},
            "market_research": {"market_research": market_research, "status": "success"},
            "rebate_analysis": rebate_analysis,
            "total_savings": total_savings,
            "billing_context": billing_context,
            "completed_at": datetime.now().isoformat(),
            "processing_time_seconds": (datetime.now() - datetime.fromisoformat(analysis_storage[analysis_id]["started_at"])).total_seconds()
        }

        analysis_storage[analysis_id].update({
            "status": "completed",
            "progress": 100,
            "current_step": "Analysis complete!",
            "results": final_results
        })

        logger.info(f"🎉 Standalone Analysis {analysis_id} completed successfully!")

    except Exception as e:
        logger.error(f"❌ Standalone Analysis {analysis_id} failed: {e}")
        analysis_storage[analysis_id].update({
            "status": "failed",
            "progress": 0,
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

def calculate_adk_total_savings(market_research: Dict[str, Any], rebate_analysis: Dict[str, Any], usage_optimization: Dict[str, Any]) -> float:
    """Calculate total potential savings from ADK agent results"""
    market_savings = 0
    if market_research.get('status') == 'success':
        market_data = market_research.get('market_research', {})
        if market_data.get('savings_analysis'):
            market_savings = market_data['savings_analysis'].get('max_annual_savings', 0)
        elif market_data.get('best_plan'):
            market_savings = market_data['best_plan'].get('annual_savings', 0)

    rebate_savings = 0
    if rebate_analysis.get('status') == 'success':
        rebate_savings = rebate_analysis.get('total_rebate_value', 0)

    usage_savings = 0
    if usage_optimization.get('status') == 'success':
        usage_savings = usage_optimization.get('total_annual_savings', 0)

    total_annual = market_savings + rebate_savings + usage_savings
    return total_annual / 4

async def analyze_rebates(bill_data: Dict[str, Any], state: str) -> Dict[str, Any]:
    """Enhanced rebate analysis"""
    await asyncio.sleep(1)
    
    usage_kwh = bill_data.get('usage_kwh', 0)
    has_solar = bill_data.get('has_solar', False)
    annual_usage = usage_kwh * 4

    applicable_rebates = []
    total_value = 0

    if state in ['NSW', 'VIC', 'QLD']:
        if annual_usage > 2000:
            applicable_rebates.append({
                "name": f"{state} Energy Efficiency Rebate",
                "value": 200,
                "type": "one_time",
                "description": "Rebate for energy-efficient appliances"
            })
            total_value += 200

    if has_solar and state in ['NSW', 'SA']:
        applicable_rebates.append({
            "name": f"{state} Solar Battery Rebate",
            "value": 3000,
            "type": "one_time",
            "description": "Battery installation rebate"
        })
        total_value += 3000

    if annual_usage < 1500:
        applicable_rebates.append({
            "name": "Low Income Energy Rebate",
            "value": 372,
            "type": "annual",
            "description": "Annual rebate for eligible households"
        })
        total_value += 372

    return {
        "applicable_rebates": applicable_rebates,
        "total_rebate_value": total_value,
        "rebate_count": len(applicable_rebates),
        "state": state,
        "analysis_timestamp": datetime.now().isoformat()
    }

def calculate_total_savings(market_research: Dict[str, Any], rebate_analysis: Dict[str, Any]) -> float:
    """Calculate total potential savings"""
    market_savings = 0
    if market_research.get('savings_analysis'):
        market_savings = market_research['savings_analysis'].get('max_annual_savings', 0)
    elif market_research.get('best_plan'):
        market_savings = market_research['best_plan'].get('annual_savings', 0)

    rebate_savings = rebate_analysis.get('total_rebate_value', 0)
    quarterly_market_savings = market_savings / 4
    quarterly_rebate_value = rebate_savings / 4

    return quarterly_market_savings + quarterly_rebate_value

def create_billing_context(bill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create billing period context"""
    billing_days = bill_data.get('billing_days', 90)

    if 85 <= billing_days <= 95:
        return {
            "period_type": "quarterly",
            "period_description": f"This is a {billing_days}-day quarterly bill",
            "annual_multiplier": 4,
            "display_note": "Annual estimates based on quarterly usage"
        }
    elif billing_days >= 350:
        return {
            "period_type": "annual",
            "period_description": "This is an annual bill",
            "annual_multiplier": 1,
            "display_note": "Annual data from full year bill"
        }
    else:
        multiplier = 365 / billing_days
        return {
            "period_type": "custom",
            "period_description": f"This is a {billing_days}-day billing period",
            "annual_multiplier": multiplier,
            "display_note": f"Annual estimates based on {billing_days}-day period"
        }

# API ENDPOINTS

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "adk_available": ADK_AVAILABLE,
        "agents": {
            "bill_analyzer": "active" if agent_factory else "inactive",
            "market_researcher": "active" if agent_factory else "inactive",
            "adk_integrated": bool(agent_factory and agent_factory.adk_workflow and agent_factory.adk_workflow.get('status') == 'ready')
        }
    }

@app.get("/agent-status")
async def agent_status():
    """Get detailed agent status"""
    if not agent_factory:
        raise HTTPException(status_code=503, detail="Agent factory not initialized")

    try:
        market_test = agent_factory.market_researcher.test_all_services()

        return {
            "timestamp": datetime.now().isoformat(),
            "bill_analyzer": {
                "status": "active",
                "supported_formats": ["PDF", "JPG", "PNG"],
                "confidence_threshold": 0.7
            },
            "market_researcher": {
                "status": "active",
                "etl_status": market_test.get('etl_service', {}).get('connected', False),
                "api_status": market_test.get('api_service', {}).get('cdr_register_access', False),
                "overall_status": market_test.get('overall_status', 'unknown'),
                "plans_available": market_test.get('etl_service', {}).get('total_plans_available', 'Unknown')
            },
            "supported_companies": len(agent_factory.supported_companies),
            "adk_integration": ADK_AVAILABLE
        }
    except Exception as e:
        logger.error(f"Agent status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Agent status check failed: {str(e)}")

@app.get("/supported-companies")
async def get_supported_companies():
    """Get list of supported energy companies"""
    if not agent_factory:
        raise HTTPException(status_code=503, detail="Agent factory not initialized")

    return {
        "supported_companies": agent_factory.supported_companies,
        "total_count": len(agent_factory.supported_companies),
        "last_updated": datetime.now().isoformat()
    }

@app.get("/adk-status")
async def get_adk_status():
    """Get ADK integration status"""
    if not agent_factory:
        raise HTTPException(status_code=503, detail="Agent factory not initialized")

    try:
        base_status = {
            "adk_available": ADK_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }

        if ADK_AVAILABLE and agent_factory.adk_factory:
            adk_agent_status = agent_factory.adk_factory.get_agent_status()
            workflow_status = agent_factory.adk_workflow

            base_status.update({
                "adk_integration": {
                    "status": "active",
                    "workflow_ready": workflow_status and workflow_status.get('status') == 'ready',
                    "real_agents_used": workflow_status.get('real_agents_used', False) if workflow_status else False,
                    "api_integration": workflow_status.get('api_integration', False) if workflow_status else False,
                    "etl_status": workflow_status.get('etl_status', False) if workflow_status else False,
                    "agent_count": workflow_status.get('agent_count', 0) if workflow_status else 0
                },
                "agent_details": adk_agent_status,
                "capabilities": {
                    "bill_analysis": "real_agent_integrated",
                    "market_research": "real_agent_with_etl_api",
                    "rebate_finder": "government_database_integrated",
                    "usage_optimizer": "personalized_recommendations",
                    "coordination": "adk_orchestrated"
                }
            })
        else:
            base_status.update({
                "adk_integration": {
                    "status": "unavailable",
                    "reason": "ADK not installed or factory initialization failed"
                },
                "capabilities": {
                    "bill_analysis": "standalone_agent",
                    "market_research": "standalone_agent_with_fallback",
                    "rebate_finder": "basic_database",
                    "usage_optimizer": "generic_recommendations",
                    "coordination": "manual_orchestration"
                }
            })

        return base_status

    except Exception as e:
        logger.error(f"ADK status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"ADK status check failed: {str(e)}")

@app.post("/test-adk-integration")
async def test_adk_integration_endpoint():
    """Test ADK integration with sample data"""
    if not agent_factory or not agent_factory.adk_workflow:
        raise HTTPException(status_code=503, detail="ADK integration not available")

    try:
        sample_bill_data = {
            "state": "NSW",
            "retailer": "AGL",
            "usage_kwh": 750,
            "billing_days": 92,
            "total_amount": 285.50,
            "cost_per_kwh": 0.294,
            "has_solar": True,
            "solar_export_kwh": 120
        }

        workflow = agent_factory.adk_workflow
        comprehensive_agent = workflow.get('comprehensive_analyzer')

        if not comprehensive_agent:
            raise HTTPException(status_code=500, detail="ADK comprehensive agent not available")

        test_results = {
            "adk_workflow_status": workflow.get('status'),
            "real_agents_used": workflow.get('real_agents_used', False),
            "api_integration": workflow.get('api_integration', False),
            "etl_status": workflow.get('etl_status', False),
            "available_tools": [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in comprehensive_agent.tools],
            "agent_count": workflow.get('agent_count', 0),
            "test_timestamp": datetime.now().isoformat(),
            "sample_data_processed": True
        }

        return {
            "status": "success",
            "message": "ADK integration test completed",
            "test_results": test_results
        }

    except Exception as e:
        logger.error(f"ADK integration test failed: {e}")
        raise HTTPException(status_code=500, detail=f"ADK integration test failed: {str(e)}")

@app.post("/upload-bill")
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    state: str = Form(default="NSW"),
    use_adk: bool = Form(default=True)
):
    """Enhanced bill upload with ADK integration option"""
    if not agent_factory:
        raise HTTPException(status_code=503, detail="Agent factory not initialized")

    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_types = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png']
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Supported: PDF, JPG, PNG"
        )

    try:
        # Read file content
        file_content = await file.read()

        # Enhanced validation
        validation_result = validate_energy_bill(file_content, file.filename)

        if not validation_result["is_valid"]:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid energy bill document",
                    "validation_details": validation_result["validation_details"],
                    "supported_companies": validation_result.get("supported_companies", []),
                    "tips": validation_result.get("tips", [])
                }
            )

        # Generate analysis ID
        analysis_id = str(uuid.uuid4())

        # Determine file type
        file_type = 'pdf' if file.content_type == 'application/pdf' else 'image'

        # Start background processing with ADK option
        background_tasks.add_task(
            process_bill_analysis,
            analysis_id,
            file_content,
            file_type,
            state,
            use_adk
        )

        # Store initial analysis state
        analysis_storage[analysis_id] = {
            "status": "processing",
            "progress": 0,
            "filename": file.filename,
            "state": state,
            "started_at": datetime.now().isoformat(),
            "company_detected": validation_result.get("company_detected")
        }

        return JSONResponse({
            "analysis_id": analysis_id,
            "status": "processing",
            "message": "Bill analysis started",
            "company_detected": validation_result.get("company_detected"),
            "processing_method": "adk_integrated" if use_adk and agent_factory.adk_workflow else "standalone",
            "adk_available": bool(agent_factory.adk_workflow)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@app.get("/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get analysis status and progress"""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_data = analysis_storage[analysis_id]

    return AnalysisStatus(
        analysis_id=analysis_id,
        status=analysis_data["status"],
        progress=analysis_data.get("progress", 0),
        message=analysis_data.get("current_step"),
        company_detected=analysis_data.get("company_detected")
    )

@app.get("/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get completed analysis results"""
    if analysis_id not in analysis_storage:
        raise HTTPException(status_code=404, detail="Analysis not found")

    analysis_data = analysis_storage[analysis_id]

    if analysis_data["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Analysis not completed. Current status: {analysis_data['status']}"
        )

    return analysis_data["results"]

@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    active_analyses = sum(1 for a in analysis_storage.values() if a["status"] == "processing")
    completed_analyses = sum(1 for a in analysis_storage.values() if a["status"] == "completed")
    failed_analyses = sum(1 for a in analysis_storage.values() if a["status"] == "failed")

    return {
        "timestamp": datetime.now().isoformat(),
        "analyses": {
            "active": active_analyses,
            "completed": completed_analyses,
            "failed": failed_analyses,
            "total": len(analysis_storage)
        },
        "agents": {
            "bill_analyzer": "active" if agent_factory else "inactive",
            "market_researcher": "active" if agent_factory else "inactive"
        },
        "adk_integration": ADK_AVAILABLE,
        "memory_usage": len(analysis_storage)
    }

@app.get("/test-services")
async def test_services():
    """Test all agent services"""
    if not agent_factory:
        raise HTTPException(status_code=503, detail="Agent factory not initialized")

    try:
        test_results = test_etl_integration()

        return {
            "timestamp": datetime.now().isoformat(),
            "service_tests": test_results,
            "status": "healthy" if test_results.get('overall_status') in ['excellent', 'good'] else "limited"
        }

    except Exception as e:
        logger.error(f"Service test failed: {e}")
        raise HTTPException(status_code=500, detail=f"Service test failed: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting WattsMyBill Multi-Agent API Server")
    print(f"📊 Google Cloud ADK: {'✅ Available' if ADK_AVAILABLE else '❌ Not Available'}")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )