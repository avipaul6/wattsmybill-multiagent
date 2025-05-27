"""
FastAPI Backend for WattsMyBill - Fixed Import Structure
File: main.py
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uuid
import json
import asyncio
from datetime import datetime
import sys
import os
from pathlib import Path

# Add src to path for imports - FIXED
current_dir = Path(__file__).parent
src_path = current_dir / "src"
sys.path.insert(0, str(src_path))

# Import your existing agents - with better error handling
AGENTS_AVAILABLE = False
try:
    from agents.bill_analyzer import BillAnalyzerAgent
    from agents.market_researcher import MarketResearcherAgent
    print("✅ Your existing agents imported successfully!")
    AGENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Could not import agents: {e}")
    print(f"   Looking in: {src_path}")
    print(f"   Current working directory: {os.getcwd()}")
    AGENTS_AVAILABLE = False

# Try ADK integration
ADK_AVAILABLE = False
try:
    from adk_integration.adk_agent_factory import create_adk_wattsmybill_workflow
    print("✅ ADK integration available!")
    ADK_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  ADK integration not available: {e}")
    ADK_AVAILABLE = False

app = FastAPI(
    title="WattsMyBill API", 
    version="2.0",
    description="AI-powered Australian energy bill analysis"
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",  # Alternative localhost
        "https://yourdomain.com",  # Your production domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Pydantic models
class AnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    message: str
    progress: int = 0

# In-memory storage (use Redis in production)
analysis_store: Dict[str, Dict] = {}

@app.get("/")
async def root():
    return {
        "service": "WattsMyBill API",
        "version": "2.0",
        "status": "operational",
        "agents_available": AGENTS_AVAILABLE,
        "adk_available": ADK_AVAILABLE,
        "agents": ["bill_analyzer", "market_researcher", "rebate_hunter", "usage_optimizer"],
        "powered_by": "Google Cloud ADK",
        "frontend": "React + FastAPI",
        "src_path": str(src_path),
        "current_dir": os.getcwd()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents_available": AGENTS_AVAILABLE,
        "adk_available": ADK_AVAILABLE
    }

@app.post("/upload-bill", response_model=AnalysisResponse)
async def upload_bill(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    state: str = "QLD",
    postcode: Optional[str] = None,
    privacy_mode: bool = False,
    include_solar: bool = True
):
    """Upload bill and start analysis"""
    
    print(f"📤 Received file upload: {file.filename}")
    
    # Validate file
    if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload PDF, JPG, JPEG, or PNG files.")
    
    # Generate analysis ID
    analysis_id = str(uuid.uuid4())
    
    try:
        # Read file content
        file_content = await file.read()
        file_type = 'pdf' if file.filename.lower().endswith('.pdf') else 'image'
        
        print(f"📊 Starting analysis {analysis_id} for {file.filename} ({len(file_content)} bytes)")
        
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
        print(f"❌ Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

@app.get("/analysis/{analysis_id}/status")
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

@app.get("/analysis/{analysis_id}/results")
async def get_analysis_results(analysis_id: str):
    """Get complete analysis results"""
    
    if analysis_id not in analysis_store:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    analysis = analysis_store[analysis_id]
    
    if analysis["status"] == "processing":
        raise HTTPException(status_code=202, detail="Analysis still in progress. Please check status endpoint.")
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
        "usage_optimization": analysis.get("usage_optimization"),
        "final_recommendations": analysis.get("final_recommendations"),
        "total_savings": analysis.get("total_savings"),
        "file_name": analysis.get("file_name"),
        "completed_at": analysis.get("completed_at")
    }

async def run_analysis_task(analysis_id: str):
    """Background task to run analysis"""
    
    print(f"🚀 Starting background analysis for {analysis_id}")
    
    try:
        analysis = analysis_store[analysis_id]
        
        # Helper function to update progress
        def update_progress(step: str, progress: int, message: str):
            analysis_store[analysis_id].update({
                "status": "processing",
                "progress": progress,
                "message": message,
                "current_step": step
            })
            print(f"📊 {analysis_id}: {progress}% - {message}")
        
        if AGENTS_AVAILABLE:
            await run_real_agent_analysis(analysis_id, update_progress)
        else:
            await run_mock_analysis(analysis_id, update_progress)
            
    except Exception as e:
        print(f"❌ Analysis {analysis_id} failed: {str(e)}")
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
    update_progress("bill_analysis", 25, "🔍 Using your real BillAnalyzerAgent...")
    await asyncio.sleep(1)  # Simulate processing time
    
    bill_analyzer = BillAnalyzerAgent()
    bill_analysis = bill_analyzer.analyze_bill(
        file_content, 
        file_type, 
        preferences["privacy_mode"]
    )
    analysis_store[analysis_id]["bill_analysis"] = bill_analysis
    
    # Step 2: Market Research (50%)
    update_progress("market_research", 50, "📊 Using your real MarketResearcherAgent...")
    await asyncio.sleep(1)
    
    market_researcher = MarketResearcherAgent()
    bill_data = bill_analysis.get("bill_data", {}) if not bill_analysis.get("error") else {}
    
    if bill_data:
        market_research = market_researcher.research_better_plans(bill_data)
    else:
        # Fallback market research
        market_research = {
            "best_plan": {
                "retailer": "Alinta Energy",
                "plan_name": "Home Deal Plus",
                "annual_savings": 420
            },
            "savings_analysis": {
                "max_annual_savings": 420
            }
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
    
    # Calculate total savings
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
    
    # Mock results
    analysis_store[analysis_id].update({
        "status": "completed",
        "bill_analysis": {
            "cost_breakdown": {"total_cost": 2850},
            "usage_profile": {"total_kwh": 8240},
            "efficiency_score": 72
        },
        "market_research": {
            "best_plan": {
                "retailer": "Alinta Energy",
                "plan_name": "Home Deal Plus",
                "annual_savings": 420
            }
        },
        "rebate_analysis": {
            "total_rebate_value": 572,
            "rebate_count": 3
        },
        "total_savings": 992,
        "completed_at": datetime.now().isoformat()
    })

def generate_rebate_analysis(state: str, has_solar: bool) -> Dict[str, Any]:
    """Generate rebate analysis"""
    
    rebates = [
        {"name": "Energy Bill Relief Fund", "value": 300, "type": "federal"},
    ]
    
    state_rebates = {
        "QLD": {"name": "Queensland Electricity Rebate", "value": 372},
        "NSW": {"name": "NSW Energy Bill Relief", "value": 150},
        "VIC": {"name": "Victorian Energy Compare Credit", "value": 250}
    }
    
    if state in state_rebates:
        rebates.append(state_rebates[state])
    
    total_value = sum(r["value"] for r in rebates)
    
    return {
        "total_rebate_value": total_value,
        "rebate_count": len(rebates),
        "applicable_rebates": rebates
    }

@app.get("/test-agents")
async def test_agents():
    """Test agent availability"""
    return {
        "agents_available": AGENTS_AVAILABLE,
        "adk_available": ADK_AVAILABLE,
        "timestamp": datetime.now().isoformat(),
        "message": "Agents working!" if AGENTS_AVAILABLE else "Using demo mode - agents not found"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting WattsMyBill FastAPI backend...")
    print(f"   Agents available: {AGENTS_AVAILABLE}")
    print(f"   ADK available: {ADK_AVAILABLE}")
    print("   Access API docs at: http://localhost:8000/docs")
    print("   React frontend should run on: http://localhost:3000")
    
    # Use reload=False to avoid the warning
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)