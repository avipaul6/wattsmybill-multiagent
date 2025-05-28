"""
FastAPI Backend for WattsMyBill - Agent-Focused Architecture
File: main.py (SIMPLIFIED VERSION - Let agents do the work)
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import json
import asyncio
from datetime import datetime
import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add src to path
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

# Import agents
AGENTS_AVAILABLE = False
try:
    from agents.bill_analyzer import BillAnalyzerAgent
    from agents.market_researcher import research_plans_for_bill
    AGENTS_AVAILABLE = True
    logger.info("✅ Agents imported successfully!")
except ImportError as e:
    logger.error(f"❌ Could not import agents: {e}")
    AGENTS_AVAILABLE = False

# Initialize FastAPI
app = FastAPI(
    title="WattsMyBill", 
    version="3.0", 
    description="Australian energy bill analysis with intelligent plan switching"
)

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_credentials=True, 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# Models
class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str
    progress: int = 0

class SwitchRequest(BaseModel):
    plan_id: str
    postcode: Optional[str] = None
    retailer: Optional[str] = None
    plan_name: Optional[str] = None

# Storage
analysis_store: Dict[str, Dict] = {}

# Static files
static_dir = current_dir / "static"
if static_dir.exists():
    if (static_dir / "static").exists():
        app.mount("/static", StaticFiles(directory=static_dir / "static"), name="static")
    else:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

def validate_energy_bill(file_content: bytes, file_type: str) -> Dict[str, Any]:
    """Simple validation using agents"""
    try:
        if not AGENTS_AVAILABLE:
            return {"is_valid": True, "confidence": 50, "company_detected": None}
            
        analyzer = BillAnalyzerAgent()
        result = analyzer.analyze_bill(file_content, file_type, privacy_mode=True)
        
        if result.get('error'):
            return {"is_valid": False, "confidence": 0, "company_detected": None}
        
        bill_data = result.get('bill_data', {})
        has_energy_data = bool(bill_data.get('usage_kwh', 0) and bill_data.get('total_amount', 0))
        
        return {
            "is_valid": has_energy_data,
            "confidence": 85 if has_energy_data else 30,
            "company_detected": bill_data.get('retailer') if bill_data.get('retailer') != 'Unknown' else None
        }
    except Exception as e:
        logger.warning(f"Validation failed: {e}")
        return {"is_valid": True, "confidence": 50, "company_detected": None}

# API Endpoints
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_available": AGENTS_AVAILABLE,
        "enhanced_agents_available": AGENTS_AVAILABLE,  # For frontend compatibility
        "features": {
            "bill_analysis": AGENTS_AVAILABLE,
            "plan_switching": True, 
            "energy_made_easy_integration": True,
            "multi_retailer_search": AGENTS_AVAILABLE
        }
    }

@app.get("/api/supported-companies")
async def get_supported_companies():
    """Get supported energy companies"""
    # Let the market researcher agent handle this
    supported_companies = [
        "Origin Energy", "AGL", "Energy Australia", "Alinta Energy", 
        "Red Energy", "Simply Energy", "Nectr", "Lumo Energy", 
        "Powershop", "Click Energy", "Momentum Energy"
    ]
    
    return {
        "supported_companies": supported_companies,
        "total_count": len(supported_companies),
        "message": "Companies supported by our analysis agents"
    }

@app.post("/api/upload-bill", response_model=AnalysisResponse)
async def upload_bill(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...), 
    state: str = "NSW",
    postcode: Optional[str] = None
):
    """Upload and start analysis of energy bill"""
    
    if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF or image files.")
    
    analysis_id = str(uuid.uuid4())
    
    try:
        file_content = await file.read()
        file_type = 'pdf' if file.filename.lower().endswith('.pdf') else 'image'
        
        # Validate using agents
        validation_result = validate_energy_bill(file_content, file_type)
        
        if not validation_result["is_valid"] and validation_result.get("confidence", 0) < 30:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "This doesn't appear to be an Australian energy bill",
                    "validation_details": validation_result,
                    "tips": [
                        "Make sure the bill is clearly visible and not blurry",
                        "Check that it's from an Australian energy retailer",
                        "Ensure usage and cost information is visible"
                    ]
                }
            )
        
        # Store analysis request
        analysis_store[analysis_id] = {
            "status": "started",
            "progress": 5,
            "message": "Analysis started...",
            "file_content": file_content,
            "file_type": file_type,
            "validation_result": validation_result,
            "preferences": {
                "state": state.upper(),
                "postcode": postcode
            },
            "created_at": datetime.now().isoformat()
        }
        
        # Start background analysis using agents
        background_tasks.add_task(run_agent_analysis, analysis_id)
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message=f"Analysis started for {file.filename}!",
            progress=5
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.get("/api/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get analysis status"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    return {
        "analysis_id": analysis_id,
        "status": analysis["status"],
        "progress": analysis.get("progress", 0),
        "message": analysis.get("message", ""),
        "company_detected": analysis.get("validation_result", {}).get("company_detected"),
        "enhanced_features": AGENTS_AVAILABLE,
        "location_info": analysis.get("location_info")
    }

@app.get("/api/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get analysis results"""
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    
    if analysis["status"] != "completed":
        raise HTTPException(status_code=202, detail="Analysis not completed yet")
    
    return {
        "analysis_id": analysis_id,
        "status": analysis["status"],
        "bill_analysis": analysis.get("bill_analysis"),
        "market_research": analysis.get("market_research"),
        "total_savings": analysis.get("total_savings"),
        "location_info": analysis.get("location_info"),
        "completed_at": analysis.get("completed_at")
    }

@app.post("/api/generate-switch-url")
async def generate_switch_url(switch_request: SwitchRequest):
    """Generate Energy Made Easy switch URL with correct postcode"""
    try:
        # Use the postcode from the request, or check if it's embedded in the plan
        postcode = switch_request.postcode
        plan_id = switch_request.plan_id
        
        # If no postcode provided, try to extract from recent analysis
        if not postcode:
            # Check recent analysis results for postcode
            for analysis_id, analysis in analysis_store.items():
                if analysis.get('status') == 'completed':
                    market_research = analysis.get('market_research', {})
                    research_params = market_research.get('research_parameters', {})
                    extracted_postcode = research_params.get('postcode')
                    if extracted_postcode:
                        postcode = extracted_postcode
                        break
        
        # Fallback to default if still no postcode
        if not postcode:
            postcode = "2000"
        
        # Generate Energy Made Easy URL
        switch_url = f"https://www.energymadeeasy.gov.au/plan?id={plan_id}&postcode={postcode}"
        
        logger.info(f"🔄 Generated switch URL for {switch_request.retailer} plan with postcode {postcode}: {switch_url}")
        
        return {
            "switch_url": switch_url,
            "plan_id": plan_id,
            "postcode": postcode,
            "retailer": switch_request.retailer,
            "plan_name": switch_request.plan_name,
            "message": f"Redirecting to Energy Made Easy for {postcode}"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate switch URL: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate switch URL: {str(e)}")

@app.get("/api/switch-plan")
async def redirect_to_energy_made_easy(plan_id: str, postcode: Optional[str] = None):
    """Direct redirect to Energy Made Easy"""
    try:
        postcode = postcode or "2000"
        energy_made_easy_url = f"https://www.energymadeeasy.gov.au/plan?id={plan_id}&postcode={postcode}"
        logger.info(f"🔄 Direct redirect to Energy Made Easy: {energy_made_easy_url}")
        return RedirectResponse(url=energy_made_easy_url, status_code=302)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to redirect: {str(e)}")

@app.post("/api/validate-location")
async def validate_location_endpoint(request: Dict[str, str]):
    """Validate postcode and state combination"""
    try:
        postcode = request.get("postcode")
        state = request.get("state")
        
        if not postcode or not state:
            raise HTTPException(status_code=400, detail="Postcode and state are required")
        
        # Use agent's validation if available
        if AGENTS_AVAILABLE:
            try:
                from integrations.australian_energy_api import validate_location
                validation_result = validate_location(postcode, state)
                return {"validation_result": validation_result}
            except ImportError:
                pass
        
        # Simple fallback validation
        return {
            "validation_result": {
                "valid": True,
                "confidence": "medium",
                "message": f"Location {postcode}, {state} accepted",
                "detected_state": state
            }
        }
        
    except Exception as e:
        logger.error(f"Location validation failed: {e}")
        raise HTTPException(status_code=500, detail="Location validation failed")

async def run_agent_analysis(analysis_id: str):
    """
    Main analysis workflow using agents
    """
    try:
        analysis = analysis_store[analysis_id]
        
        def update_progress(step: str, progress: int, message: str):
            analysis_store[analysis_id].update({
                "status": "processing",
                "progress": progress,
                "message": message
            })
        
        # Step 1: Bill Analysis using BillAnalyzerAgent
        update_progress("bill_analysis", 20, "🔍 AI agents analyzing your energy bill...")
        await asyncio.sleep(1)
        
        bill_analysis = None
        if AGENTS_AVAILABLE:
            try:
                bill_analyzer = BillAnalyzerAgent()
                bill_analysis = bill_analyzer.analyze_bill(
                    analysis["file_content"], 
                    analysis["file_type"], 
                    privacy_mode=False
                )
                logger.info("✅ Bill analysis completed using BillAnalyzerAgent")
            except Exception as e:
                logger.error(f"BillAnalyzerAgent failed: {e}")
                bill_analysis = None
        
        # Fallback bill analysis if agents not available
        if not bill_analysis or bill_analysis.get('error'):
            bill_analysis = {
                "bill_data": {
                    "usage_kwh": 2000,
                    "total_amount": 650,
                    "billing_days": 90,
                    "state": analysis["preferences"]["state"],
                    "postcode": analysis["preferences"].get("postcode"),
                    "has_solar": False,
                    "retailer": "Unknown"
                },
                "data_source": "fallback",
                "message": "Using estimated values for analysis"
            }
        
        analysis_store[analysis_id]["bill_analysis"] = bill_analysis
        
        # Step 2: Market Research using MarketResearcherAgent
        update_progress("market_research", 50, "📊 AI agents finding better energy plans...")
        await asyncio.sleep(1)
        
        bill_data = bill_analysis.get("bill_data", {})
        
        # Add user preferences to bill data
        if analysis["preferences"].get("postcode"):
            bill_data["postcode"] = analysis["preferences"]["postcode"]
        bill_data["state"] = analysis["preferences"]["state"]
        
        market_research = None
        if AGENTS_AVAILABLE and bill_data:
            try:
                market_research = research_plans_for_bill(bill_data)
                logger.info("✅ Market research completed using MarketResearcherAgent")
            except Exception as e:
                logger.error(f"MarketResearcherAgent failed: {e}")
                market_research = None
        
        # Fallback market research
        if not market_research or market_research.get('error'):
            market_research = create_fallback_market_research(bill_data)
        
        analysis_store[analysis_id]["market_research"] = market_research
        
        # Step 3: Calculate savings and complete
        update_progress("savings", 80, "💰 Calculating your potential savings...")
        await asyncio.sleep(1)
        
        # Extract key metrics
        max_savings = 0
        location_info = {}
        
        if market_research and market_research.get("savings_analysis"):
            max_savings = market_research["savings_analysis"].get("max_quarterly_savings", 0)
        
        if market_research and market_research.get("research_parameters"):
            location_info = {
                "postcode": market_research["research_parameters"].get("postcode"),
                "state": market_research["research_parameters"].get("state"),
                "validated": market_research.get("market_insights", {}).get("postcode_validated", False)
            }
        
        # Step 4: Complete analysis
        update_progress("complete", 100, "✅ Analysis complete - ready to switch!")
        
        analysis_store[analysis_id].update({
            "status": "completed",
            "total_savings": max_savings,
            "location_info": location_info,
            "completed_at": datetime.now().isoformat()
        })
        
        logger.info(f"✅ Analysis {analysis_id} completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Analysis {analysis_id} failed: {str(e)}")
        analysis_store[analysis_id].update({
            "status": "failed",
            "error": str(e),
            "message": "Analysis failed - please try again"
        })

def create_fallback_market_research(bill_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create fallback market research when agents aren't available"""
    
    # Extract bill info
    usage_kwh = bill_data.get('usage_kwh', 2000)
    billing_days = bill_data.get('billing_days', 90)
    current_cost = bill_data.get('total_amount', 650)
    state = bill_data.get('state', 'NSW')
    postcode = bill_data.get('postcode')
    has_solar = bill_data.get('has_solar', False)
    
    # Annualize the data
    annual_usage = int(usage_kwh * (365 / billing_days)) if billing_days > 0 else usage_kwh
    annual_cost = current_cost * (365 / billing_days) if billing_days > 0 else current_cost * 4
    
    # Simple retailer comparisons
    fallback_retailers = {
        'alinta': {'name': 'Alinta Energy', 'usage': 0.245, 'supply': 0.95, 'solar': 0.075},
        'red_energy': {'name': 'Red Energy', 'usage': 0.250, 'supply': 1.10, 'solar': 0.080},
        'nectr': {'name': 'Nectr', 'usage': 0.238, 'supply': 1.02, 'solar': 0.082},
        'simply_energy': {'name': 'Simply Energy', 'usage': 0.248, 'supply': 1.25, 'solar': 0.070}
    }
    
    recommended_plans = []
    
    for retailer_key, retailer_data in fallback_retailers.items():
        # Calculate costs
        annual_usage_cost = annual_usage * retailer_data['usage']
        annual_supply_cost = 365 * retailer_data['supply']
        annual_solar_credit = 0  # Simplified for fallback
        estimated_annual_cost = annual_usage_cost + annual_supply_cost - annual_solar_credit
        
        annual_savings = annual_cost - estimated_annual_cost
        
        if annual_savings > 50:  # Only include if saves money
            # Generate plan ID for Energy Made Easy
            plan_id = f"{retailer_key.upper()[:3]}{abs(hash(f'{retailer_key}_{state}')) % 999999:06d}MRE1"
            
            plan = {
                'retailer': retailer_data['name'],
                'plan_name': f"{retailer_data['name']} Saver",
                'plan_id': plan_id,
                'estimated_annual_cost': round(estimated_annual_cost, 2),
                'estimated_quarterly_cost': round(estimated_annual_cost / 4, 2),
                'usage_rate': retailer_data['usage'],
                'supply_charge_daily': retailer_data['supply'],
                'solar_feed_in_tariff': retailer_data['solar'],
                'annual_savings': round(annual_savings, 2),
                'quarterly_savings': round(annual_savings / 4, 2),
                'percentage_savings': round((annual_savings / annual_cost) * 100, 1) if annual_cost > 0 else 0,
                'key_features': ['Competitive rates', 'No exit fees'],
                'plan_type': 'market',
                'data_source': 'fallback',
                'switch_confidence': 'medium',
                'energy_made_easy_url': f"https://www.energymadeeasy.gov.au/plan?id={plan_id}&postcode={postcode or '2000'}",
                'retailer_website': f"https://www.{retailer_key.replace('_', '').lower()}.com.au"
            }
            recommended_plans.append(plan)
    
    # Sort by savings
    recommended_plans.sort(key=lambda x: x['annual_savings'], reverse=True)
    
    # Create response
    best_plan = recommended_plans[0] if recommended_plans else {
        'retailer': 'Current Plan',
        'plan_name': 'Your plan is competitive',
        'annual_savings': 0,
        'switch_confidence': 'low'
    }
    
    max_savings = best_plan.get('annual_savings', 0)
    
    return {
        "data_source": "fallback_market_analysis",
        "research_parameters": {
            "state": state,
            "postcode": postcode,
            "annual_usage_kwh": annual_usage,
            "current_annual_cost": round(annual_cost, 2)
        },
        "recommended_plans": recommended_plans,
        "best_plan": best_plan,
        "savings_analysis": {
            "max_annual_savings": max_savings,
            "max_quarterly_savings": max_savings / 4,
            "savings_potential": "medium" if max_savings > 200 else "low" if max_savings > 50 else "none",
            "savings_message": f"Save up to ${max_savings:.0f} annually" if max_savings > 0 else "Your current plan is competitive",
            "better_plans_available": len(recommended_plans)
        },
        "market_insights": {
            "retailers_analyzed": len(fallback_retailers),
            "switching_recommendation": "💡 RECOMMENDED: Better options available" if max_savings > 100 else "✅ Your plan is competitive",
            "postcode_validated": False
        },
        "research_timestamp": datetime.now().isoformat()
    }

# Serve React app
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React frontend"""
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    if not static_dir.exists():
        return JSONResponse({
            "error": "React app not built", 
            "message": "Please build the React frontend first"
        }, status_code=503)
    
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")
    else:
        return JSONResponse({
            "error": "React app not found",
            "available_endpoints": ["/api/health", "/api/supported-companies", "/api/upload-bill"]
        }, status_code=503)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8501))
    logger.info(f"🚀 Starting WattsMyBill on port {port}")
    logger.info(f"   Agents available: {AGENTS_AVAILABLE}")
    logger.info(f"   Features: Bill analysis, Plan switching, Energy Made Easy integration")
    
    if AGENTS_AVAILABLE:
        logger.info("   ✅ Using AI agents for analysis")
    else:
        logger.info("   ⚠️  Using fallback analysis (agents not available)")
    
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)