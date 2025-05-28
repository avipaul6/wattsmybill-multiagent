"""
FastAPI Backend for WattsMyBill - Fixed Static File Serving
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_available": AGENTS_AVAILABLE,
        "environment": os.getenv("ENVIRONMENT", "development"),
        "static_files": static_dir.exists() if 'static_dir' in locals() else False,
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
        "environment": os.getenv("ENVIRONMENT", "development")
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
    """Upload bill and start analysis"""
    
    logger.info(f"📤 Received file upload: {file.filename}")
    
    # Validate file
    if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    try:
        # Read file content
        file_content = await file.read()
        file_type = 'pdf' if file.filename.lower().endswith('.pdf') else 'image'
        
        logger.info(f"📊 Starting analysis {analysis_id}")
        
        # Store analysis request
        analysis_store[analysis_id] = {
            "status": "started",
            "progress": 5,
            "message": "Analysis started...",
            "file_content": file_content,
            "file_type": file_type,
            "file_name": file.filename,
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
        
        return AnalysisResponse(
            analysis_id=analysis_id,
            status="started",
            message=f"Analysis started for {file.filename}!",
            progress=5
        )
        
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
        "completed_at": analysis.get("completed_at")
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
    
    return {
        "analysis_id": analysis_id,
        "status": analysis["status"],
        "bill_analysis": analysis.get("bill_analysis"),
        "market_research": analysis.get("market_research"),
        "rebate_analysis": analysis.get("rebate_analysis"),
        "total_savings": analysis.get("total_savings"),
        "completed_at": analysis.get("completed_at")
    }

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
    
    # Step 1: Bill Analysis (25%)
    update_progress("bill_analysis", 25, "🔍 Analyzing your energy bill...")
    await asyncio.sleep(1)
    
    bill_analyzer = BillAnalyzerAgent()
    bill_analysis = bill_analyzer.analyze_bill(
        file_content, 
        file_type, 
        preferences["privacy_mode"]
    )
    analysis_store[analysis_id]["bill_analysis"] = bill_analysis
    
    # Step 2: Market Research (50%)
    update_progress("market_research", 50, "📊 Researching better energy plans...")
    await asyncio.sleep(1)
    
    market_researcher = MarketResearcherAgent()
    bill_data = bill_analysis.get("bill_data", {}) if not bill_analysis.get("error") else {}
    
    if bill_data:
        market_research = market_researcher.research_better_plans(bill_data)
    else:
        market_research = {
            "best_plan": {"retailer": "Alinta Energy", "plan_name": "Home Deal Plus", "annual_savings": 420},
            "savings_analysis": {"max_annual_savings": 420}
        }
    
    analysis_store[analysis_id]["market_research"] = market_research
    
    # Step 3: Rebate Analysis (75%)
    update_progress("rebate_analysis", 75, "💰 Finding government rebates...")
    await asyncio.sleep(1)
    
    state = preferences.get("state", "QLD")
    has_solar = bill_analysis.get("solar_analysis", {}).get("has_solar", False) if bill_analysis else False
    
    rebate_analysis = generate_rebate_analysis(state, has_solar)
    analysis_store[analysis_id]["rebate_analysis"] = rebate_analysis
    
    # Step 4: Complete (100%)
    update_progress("complete", 100, "✅ Analysis complete!")
    
    plan_savings = market_research.get("savings_analysis", {}).get("max_annual_savings", 0)
    rebate_savings = rebate_analysis.get("total_rebate_value", 0)
    total_savings = plan_savings + rebate_savings
    
    analysis_store[analysis_id].update({
        "status": "completed",
        "total_savings": total_savings,
        "completed_at": datetime.now().isoformat()
    })

async def run_mock_analysis(analysis_id: str, update_progress):
    """Run mock analysis when agents aren't available"""
    
    update_progress("bill_analysis", 25, "🔍 Analyzing bill (demo mode)...")
    await asyncio.sleep(2)
    
    update_progress("market_research", 50, "📊 Researching plans (demo mode)...")
    await asyncio.sleep(2)
    
    update_progress("rebate_analysis", 75, "💰 Finding rebates (demo mode)...")
    await asyncio.sleep(1)
    
    update_progress("complete", 100, "✅ Demo analysis complete!")
    
    analysis_store[analysis_id].update({
        "status": "completed",
        "bill_analysis": {"cost_breakdown": {"total_cost": 2850}, "usage_profile": {"total_kwh": 8240}, "efficiency_score": 72},
        "market_research": {"best_plan": {"retailer": "Alinta Energy", "plan_name": "Home Deal Plus", "annual_savings": 420}},
        "rebate_analysis": {"total_rebate_value": 572, "rebate_count": 3},
        "total_savings": 992,
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
    
    uvicorn.run(app, host="0.0.0.0", port=port, reload=True)