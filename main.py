"""
FastAPI Backend for WattsMyBill - Enhanced Bill Validation
File: main.py
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
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
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ADD THIS HERE - SUPPORTED COMPANIES LIST
SUPPORTED_COMPANIES = [
    "Origin Energy", "AGL", "Energy Australia", "Red Energy", "Alinta Energy",
    "Simply Energy", "Momentum Energy", "Powershop", "Click Energy", "ActewAGL",
    "Ergon Energy", "Energex", "Aurora Energy", "TasNetworks", "SA Power Networks",
    "Western Power", "Endeavour Energy", "Essential Energy", "Ausgrid", "Jemena",
    "CitiPower", "Powercor", "United Energy", "Diamond Energy", "Sumo Power",
    "Lumo Energy", "Dodo Power & Gas", "Kogan Energy", "GloBird Energy", "Nectr"
]

# Add src to path to import your existing agents
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

# Import your existing agents
AGENTS_AVAILABLE = False
try:
    from agents.bill_analyzer import BillAnalyzerAgent
    from agents.market_researcher import MarketResearcherAgent
    logger.info("✅ Your existing agents imported successfully!")
    AGENTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"⚠️  Could not import agents: {e}")
    AGENTS_AVAILABLE = False

# Initialize FastAPI
app = FastAPI(
    title="WattsMyBill",
    version="2.0",
    description="AI-powered Australian energy bill analysis"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str
    progress: int = 0

# In-memory storage
analysis_store: Dict[str, Dict] = {}

# Check for static files and mount them correctly
static_dir = current_dir / "static"
if static_dir.exists():
    # Check if it's a React build directory structure
    if (static_dir / "static").exists():
        # React creates build/static/js and build/static/css
        app.mount("/static", StaticFiles(directory=static_dir / "static"), name="static")
        logger.info(f"✅ Mounted React static files from {static_dir / 'static'}")
    else:
        # Direct static files
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info(f"✅ Mounted static files from {static_dir}")
    
    logger.info(f"📂 Static directory contents: {list(static_dir.iterdir())}")
    if (static_dir / "static").exists():
        logger.info(f"📂 React static contents: {list((static_dir / 'static').iterdir())}")
else:
    logger.warning(f"⚠️  Static directory not found: {static_dir}")

def validate_energy_bill_with_agent(file_content: bytes, file_type: str):
    """Use BillAnalyzerAgent for validation"""
    try:
        from agents.bill_analyzer import BillAnalyzerAgent
        analyzer = BillAnalyzerAgent()
        result = analyzer.analyze_bill(file_content, file_type, privacy_mode=True)
        
        if result.get('error'):
            return {
                "is_valid": False, 
                "confidence": 0, 
                "company_detected": None,
                "reason": "BillAnalyzerAgent could not parse this as an energy bill"
            }
        
        bill_data = result.get('bill_data', {})
        usage_kwh = bill_data.get('usage_kwh', 0)
        total_amount = bill_data.get('total_amount', 0)
        retailer = bill_data.get('retailer', '')
        
        has_energy_data = bool(usage_kwh and total_amount)
        
        return {
            "is_valid": has_energy_data,
            "confidence": 85 if has_energy_data else 0,
            "company_detected": retailer if retailer != 'Unknown' else None,
            "reason": "BillAnalyzerAgent successfully parsed energy bill data" if has_energy_data else "No energy data found"
        }
    except Exception as e:
        # Allow through if validation fails
        return {
            "is_valid": True, 
            "confidence": 50, 
            "company_detected": None,
            "reason": f"Validation failed: {e} - proceeding with analysis"
        }
    
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_available": AGENTS_AVAILABLE,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "static_files": static_dir.exists() if 'static_dir' in locals() else False,
        "supported_companies": len(SUPPORTED_COMPANIES),
        "static_structure": {
            "static_dir_exists": static_dir.exists(),
            "react_static_exists": (static_dir / "static").exists() if static_dir.exists() else False,
            "index_html_exists": (static_dir / "index.html").exists() if static_dir.exists() else False
        }
    }

@app.get("/api")
async def api_root():
    """API information endpoint"""
    return {
        "service": "WattsMyBill API",
        "version": "2.0",
        "status": "operational",
        "agents_available": AGENTS_AVAILABLE,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "supported_companies": SUPPORTED_COMPANIES[:10]  # Return first 10 for brevity
    }

@app.get("/api/supported-companies")
async def get_supported_companies():
    """Get list of supported energy companies"""
    supported_companies = [
        "Origin Energy", "AGL", "Energy Australia", "Red Energy", "Alinta Energy",
        "Simply Energy", "Momentum Energy", "Powershop", "Click Energy", "ActewAGL",
        "Ergon Energy", "Energex", "Aurora Energy", "TasNetworks", "SA Power Networks",
        "Western Power", "Endeavour Energy", "Essential Energy", "Ausgrid", "Jemena",
        "CitiPower", "Powercor", "United Energy", "Diamond Energy", "Sumo Power",
        "Lumo Energy", "Dodo Power & Gas", "Kogan Energy", "GloBird Energy", "Nectr"
    ]
    
    return {
        "supported_companies": supported_companies,
        "total_count": len(supported_companies),
        "message": "These are the Australian energy companies we currently support"
    }

@app.post("/api/upload-bill", response_model=AnalysisResponse)
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    state: str = "QLD",
    postcode: Optional[str] = None,
    privacy_mode: bool = False,
    include_solar: bool = True
):
    """Upload bill and start analysis with validation"""
    
    logger.info(f"📤 Received file upload: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(
            status_code=400, 
            detail="Invalid file type. Please upload a PDF or image file (JPG, JPEG, PNG)."
        )
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    try:
        # Read file content
        file_content = await file.read()
        file_type = 'pdf' if file.filename.lower().endswith('.pdf') else 'image'
        
        # Validate using the real BillAnalyzerAgent
        logger.info(f"🔍 Validating {file.filename} using BillAnalyzerAgent...")
        validation_result = validate_energy_bill_with_agent(file_content, file_type)
        
        # Only reject if the BillAnalyzerAgent clearly couldn't parse it as an energy bill
        if not validation_result["is_valid"] and validation_result.get("confidence", 0) == 0:
            error_msg = "This doesn't appear to be an Australian energy bill. "
            
            # Provide specific feedback based on BillAnalyzerAgent results
            agent_reason = validation_result.get("reason", "Unknown validation failure")
            agent_error = validation_result.get("agent_error", "")
            
            if "could not parse" in agent_reason.lower():
                error_msg += "Our energy bill parser couldn't extract energy data from this document. "
            elif agent_error:
                error_msg += f"Analysis failed: {agent_error}. "
            else:
                error_msg += f"{agent_reason}. "
            
            error_msg += "Please upload a valid Australian energy bill."
            
            # Create detailed error response
            error_detail = {
                "error": error_msg,
                "validation_details": validation_result,
                "supported_companies": SUPPORTED_COMPANIES[:15],
                "tips": [
                    "Ensure the bill is from an Australian energy retailer",
                    "Make sure the document shows electricity usage (kWh) and charges",
                    "Check that the bill contains tariff information",
                    "PDF files typically work better than images",
                    "Ensure the full bill is visible and text is readable"
                ]
            }
            
            # Add specific tip based on validation failure
            if "could not parse" in agent_reason.lower():
                error_detail["tips"].insert(0, "The document structure suggests this may not be an energy bill")
            elif agent_error:
                error_detail["tips"].insert(0, "The document may be corrupted or in an unsupported format")
            
            raise HTTPException(
                status_code=400,
                detail=error_detail
            )
        
        # Log validation results
        confidence = validation_result.get("confidence", 0)
        if confidence >= 80:
            logger.info(f"✅ BillAnalyzerAgent validation passed with {confidence}% confidence")
        elif confidence >= 50:
            logger.info(f"⚠️ BillAnalyzerAgent validation passed with {confidence}% confidence (proceeding)")
        else:
            logger.warning(f"⚠️ BillAnalyzerAgent validation uncertain ({confidence}%) - proceeding anyway")
        
        company_detected = validation_result.get("company_detected")
        if company_detected:
            logger.info(f"🏢 BillAnalyzerAgent detected: {company_detected}")
        
        # Store validation results for later use
        validation_preview = validation_result.get("analysis_preview", {})
        
        logger.info(f"📊 Starting analysis {analysis_id}")
        
        # Store analysis request
        analysis_store[analysis_id] = {
            "status": "started",
            "progress": 5,
            "message": "Analysis started...",
            "file_content": file_content,
            "file_type": file_type,
            "file_name": file.filename,
            "validation_result": validation_result,
            "validation_preview": validation_preview,
            "preferences": {
                "state": state,
                "postcode": postcode,
                "privacy_mode": privacy_mode,
                "include_solar": include_solar
            },
            "created_at": datetime.now().isoformat()
        }
        
        # Start background analysis
        background_tasks.add_task(run_analysis_task, analysis_id)
        
        company_msg = f" (detected: {validation_result['company_detected']})" if validation_result.get('company_detected') else ""
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message=f"Analysis started for {file.filename}{company_msg}!",
            progress=5
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"❌ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.get("/api/analysis/{analysis_id}/status")
async def get_analysis_status(analysis_id: str):
    """Get analysis status and progress"""
    
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    
    return {
        "analysis_id": analysis_id,
        "status": analysis["status"],
        "progress": analysis.get("progress", 0),
        "message": analysis.get("message", ""),
        "current_step": analysis.get("current_step", ""),
        "created_at": analysis.get("created_at"),
        "completed_at": analysis.get("completed_at"),
        "company_detected": analysis.get("validation_result", {}).get("company_detected")
    }

@app.get("/api/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get complete analysis results"""
    
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    
    if analysis["status"] == "processing":
        raise HTTPException(status_code=202, detail="Analysis still in progress")
    elif analysis["status"] == "failed":
        raise HTTPException(status_code=500, detail=f"Analysis failed: {analysis.get('error', 'Unknown error')}")
    elif analysis["status"] != "completed":
        raise HTTPException(status_code=202, detail="Analysis not completed yet")
    
    # Add billing period context to results
    results = {
        "analysis_id": analysis_id,
        "status": analysis["status"],
        "bill_analysis": analysis.get("bill_analysis"),
        "market_research": analysis.get("market_research"),
        "rebate_analysis": analysis.get("rebate_analysis"),
        "total_savings": analysis.get("total_savings"),
        "completed_at": analysis.get("completed_at"),
        "company_detected": analysis.get("validation_result", {}).get("company_detected"),
        "billing_context": {
            "period_type": "quarterly",  # Most Australian bills are quarterly
            "period_description": "Most Australian energy bills are issued quarterly (every 3 months)",
            "annual_multiplier": 4  # To convert quarterly to annual
        }
    }
    
    return results

async def run_analysis_task(analysis_id: str):
    """Background task to run analysis"""
    
    logger.info(f"🚀 Starting background analysis for {analysis_id}")
    
    try:
        analysis = analysis_store[analysis_id]
        
        def update_progress(step: str, progress: int, message: str):
            analysis_store[analysis_id].update({
                "status": "processing",
                "progress": progress,
                "message": message,
                "current_step": step
            })
            logger.info(f"📊 {analysis_id}: {progress}% - {message}")
        
        if AGENTS_AVAILABLE:
            await run_real_agent_analysis(analysis_id, update_progress)
        else:
            await run_mock_analysis(analysis_id, update_progress)
            
    except Exception as e:
        logger.error(f"❌ Analysis {analysis_id} failed: {str(e)}")
        analysis_store[analysis_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Analysis failed: {str(e)}",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

async def run_real_agent_analysis(analysis_id: str, update_progress):
    """Run analysis using your real agents"""
    
    analysis = analysis_store[analysis_id]
    file_content = analysis["file_content"]
    file_type = analysis["file_type"]
    preferences = analysis["preferences"]
    
    # Check if we already have some validation data to use
    validation_preview = analysis.get("validation_preview", {})
    
    # Step 1: Bill Analysis (25%)
    update_progress("bill_analysis", 25, "🔍 Analyzing your energy bill...")
    await asyncio.sleep(1)
    
    bill_analyzer = BillAnalyzerAgent()
    
    # If validation already parsed some data, we can still run full analysis
    # The BillAnalyzerAgent is designed to handle this properly
    bill_analysis = bill_analyzer.analyze_bill(
        file_content, 
        file_type, 
        preferences["privacy_mode"]
    )
    
    # If BillAnalyzerAgent failed but we have validation preview, use that
    if bill_analysis.get('error') and validation_preview:
        logger.warning("BillAnalyzerAgent failed, but validation found some data")
        bill_analysis = {
            'bill_data': validation_preview,
            'analysis_timestamp': datetime.now().isoformat(),
            'confidence': 0.6,
            'note': 'Using validation preview data'
        }
    
    analysis_store[analysis_id]["bill_analysis"] = bill_analysis
    
    # Step 2: Market Research (50%)
    update_progress("market_research", 50, "📊 Researching better energy plans...")
    await asyncio.sleep(1)
    
    market_researcher = MarketResearcherAgent()
    bill_data = bill_analysis.get("bill_data", {}) if not bill_analysis.get("error") else validation_preview
    
    if bill_data and bill_data.get('usage_kwh'):
        market_research = market_researcher.research_better_plans(bill_data)
    else:
        market_research = create_mock_market_research()
    
    analysis_store[analysis_id]["market_research"] = market_research
    
    # Step 3: Rebate Analysis (75%)
    update_progress("rebate_analysis", 75, "💰 Finding government rebates...")
    await asyncio.sleep(1)
    
    state = preferences.get("state", "QLD")
    has_solar = bill_data.get("has_solar", False) if bill_data else False
    
    rebate_analysis = generate_rebate_analysis(state, has_solar)
    analysis_store[analysis_id]["rebate_analysis"] = rebate_analysis
    
    # Step 4: Complete (100%)
    update_progress("complete", 100, "✅ Analysis complete!")
    
    plan_savings = market_research.get("savings_analysis", {}).get("max_quarterly_savings", 0)
    rebate_savings = rebate_analysis.get("total_rebate_value", 0)
    total_savings = plan_savings + rebate_savings
    
    analysis_store[analysis_id].update({
        "status": "completed",
        "total_savings": total_savings,
        "completed_at": datetime.now().isoformat()
    })

def create_mock_market_research():
    """Create mock market research with proper quarterly/annual context"""
    quarterly_savings = 105  # $105 per quarter
    annual_savings = quarterly_savings * 4  # $420 per year
    
    return {
        "best_plan": {
            "retailer": "Alinta Energy",
            "plan_name": "Home Deal Plus",
            "quarterly_savings": quarterly_savings,
            "annual_savings": annual_savings,
            "quarterly_cost": 607.5,  # $2430/4
            "annual_cost": 2430
        },
        "savings_analysis": {
            "max_quarterly_savings": quarterly_savings,
            "max_annual_savings": annual_savings
        }
    }

async def run_mock_analysis(analysis_id: str, update_progress):
    """Run mock analysis when agents aren't available"""
    
    update_progress("bill_analysis", 25, "🔍 Analyzing bill (demo mode)...")
    await asyncio.sleep(2)
    
    update_progress("market_research", 50, "📊 Researching plans (demo mode)...")
    await asyncio.sleep(2)
    
    update_progress("rebate_analysis", 75, "💰 Finding rebates (demo mode)...")
    await asyncio.sleep(1)
    
    update_progress("complete", 100, "✅ Demo analysis complete!")
    
    # Mock data with proper quarterly context
    quarterly_cost = 712.5  # $2850/4 
    quarterly_usage = 2060  # 8240/4
    quarterly_savings = 105  # $420/4
    
    analysis_store[analysis_id].update({
        "status": "completed",
        "bill_analysis": {
            "cost_breakdown": {
                "quarterly_cost": quarterly_cost,
                "annual_cost": quarterly_cost * 4
            },
            "usage_profile": {
                "quarterly_kwh": quarterly_usage,
                "annual_kwh": quarterly_usage * 4
            },
            "efficiency_score": 72,
            "billing_period": {
                "type": "quarterly",
                "days": 92,
                "description": "3-month billing period"
            }
        },
        "market_research": create_mock_market_research(),
        "rebate_analysis": {"total_rebate_value": 572, "rebate_count": 3},
        "total_savings": quarterly_savings + 143,  # quarterly plan + rebate portion
        "completed_at": datetime.now().isoformat()
    })

def generate_rebate_analysis(state: str, has_solar: bool) -> Dict[str, Any]:
    """Generate rebate analysis"""
    rebates = [{"name": "Energy Bill Relief Fund", "value": 300, "type": "federal"}]
    
    state_rebates = {
        "QLD": {"name": "Queensland Electricity Rebate", "value": 372},
        "NSW": {"name": "NSW Energy Bill Relief", "value": 150},
        "VIC": {"name": "Victorian Energy Compare Credit", "value": 250}
    }
    
    if state in state_rebates:
        rebates.append(state_rebates[state])
    
    return {
        "total_rebate_value": sum(r["value"] for r in rebates),
        "rebate_count": len(rebates),
        "applicable_rebates": rebates
    }

# Serve React app for all non-API routes
@app.get("/{full_path:path}")
async def serve_react_app(full_path: str):
    """Serve React app for all non-API routes"""
    
    # Don't serve React for API routes
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # Check if static files exist
    if not static_dir.exists():
        return JSONResponse({"error": "React app not built"}, status_code=503)
    
    # Serve index.html for all routes (React Router will handle routing)
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file, media_type="text/html")
    else:
        return JSONResponse({"error": "React app not found"}, status_code=503)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8501))
    logger.info(f"🚀 Starting WattsMyBill on port {port}")
    logger.info(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"   Agents available: {AGENTS_AVAILABLE}")
    logger.info(f"   Static files: {static_dir.exists() if 'static_dir' in locals() else False}")
    logger.info(f"   Supported companies: {len(SUPPORTED_COMPANIES)}")
    
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)