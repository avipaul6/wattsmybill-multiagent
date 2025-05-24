# ⚡ WattsMyBill Multi-Agent AI System

> AI agents that figure out exactly what's up with your energy bill - using Google Cloud's Agent Development Kit to navigate Australia's energy market.

## 🎯 Problem Statement
Australian households are struggling with rising energy costs, with [57% citing "keeping day-to-day living costs down"](https://www.roymorgan.com/findings/9797-most-important-issues-facing-australia-january-2025) as their top concern. Energy bills have increased 25% in 2025, costing families hundreds of dollars annually. 

## 🤖 Solution: Multi-Agent Collaboration
WattsMyBill uses 6 specialized AI agents working together to answer the question every Australian household asks: "What's really going on with my energy bill?"

- **🔍 Bill Analysis Agent**: Processes energy bills using Google Document AI
- **📊 Market Research Agent**: Finds better plans using real-time data
- **💰 Savings Calculator Agent**: Calculates potential savings with Vertex AI
- **🎯 Rebate Hunter Agent**: Discovers applicable government rebates
- **⚡ Usage Optimizer Agent**: Suggests behavioral changes
- **🎯 Orchestrator Agent**: Coordinates all agents for optimal results

## 🏗️ Technical Architecture
- **Framework**: Google Cloud Agent Development Kit (ADK)
- **Deployment**: Google Cloud Run
- **Data**: BigQuery + Australian energy APIs
- **AI**: Vertex AI - Gemini as the LLM, Document AI for parsing, Claude 
- **Frontend**: Streamlit web interface

## 🚀 Quick Start
```bash
# Clone the repository
git clone https://github.com/yourusername/wattsmybill-multiagent.git
cd wattsmybill-multiagent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Google Cloud credentials

# Run locally
streamlit run app.py