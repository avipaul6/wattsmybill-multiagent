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
git clone https://github.com/avipaul6/wattsmybill-multiagent.git
cd wattsmybill-multiagent

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your Google Cloud credentials
# Change the API creds including LLM keys 

# Run locally
streamlit run app.py
```

## 🚀 Project Structure
```bash

wattsmybill-multiagent/
├── README.md                           # Project overview & setup instructions
├── requirements.txt                    # Python dependencies
├── .env.example                        # Environment variables template
├── .gitignore                          # Git ignore file
├── app.py                             # Main Streamlit application
├── src/
│   ├── __init__.py
│   ├── agents/                        # Individual agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Base agent class
│   │   ├── bill_analyzer.py          # Bill analysis agent
│   │   ├── market_researcher.py      # Market research agent
│   │   ├── savings_calculator.py     # Savings calculation agent
│   │   ├── rebate_hunter.py          # Rebate finding agent
│   │   ├── usage_optimizer.py        # Usage optimization agent
│   │   └── orchestrator.py           # Main orchestrator agent
│   ├── adk_integration/               # Agent Development Kit integration
│   │   ├── __init__.py
│   │   ├── agent_factory.py          # Agent creation and management
│   │   └── task_manager.py           # Task coordination
│   ├── gcp_services/                  # Google Cloud Platform integrations
│   │   ├── __init__.py
│   │   ├── document_ai.py            # Document AI for bill parsing
│   │   ├── bigquery_client.py        # BigQuery data access
│   │   ├── vertex_ai.py              # Vertex AI predictions
│   │   └── storage_client.py         # Cloud Storage operations
│   └── utils/                         # Utility functions
│       ├── __init__.py
│       ├── bill_parser.py            # Bill parsing utilities
│       ├── data_models.py            # Data structures
│       └── config.py                 # Configuration management
├── deployment/                        # Deployment configurations
│   ├── cloud_run/
│   │   ├── Dockerfile
│   │   └── service.yaml
│   └── bigquery/
│       ├── schema.sql
│       └── sample_data.sql
├── demo/                              # Demo materials
│   ├── sample_bills/                 # Sample energy bills for testing
│   └── videos/                       # Demo videos
├── docs/                              # Documentation
│   ├── ARCHITECTURE.md               # System architecture
│   ├── API.md                        # API documentation
│   └── DEPLOYMENT.md                 # Deployment guide
└── tests/                             # Test files
    ├── __init__.py
    ├── test_agents.py
    └── test_integration.py

```