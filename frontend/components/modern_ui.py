"""
FIXED Modern Streamlit UI Components for WattsMyBill
File: frontend/components/modern_ui.py
"""
import streamlit as st
import time
from typing import Dict, Any, List

def inject_custom_css():
    """FIXED: Inject custom CSS to make Streamlit look modern"""
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Progress indicator styling - FIXED */
    .progress-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 40px 0;
        position: relative;
        background: white;
        padding: 20px;
        border-radius: 10px;
    }
    
    .progress-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        z-index: 2;
        background: white;
        padding: 10px;
        flex: 1;
    }
    
    .progress-circle {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        margin-bottom: 8px;
        transition: all 0.3s ease;
    }
    
    .progress-circle.active {
        background: #4CAF50;
        transform: scale(1.1);
        box-shadow: 0 4px 15px rgba(76, 175, 80, 0.4);
    }
    
    .progress-circle.completed {
        background: #4CAF50;
    }
    
    .progress-circle.pending {
        background: #e0e0e0;
        color: #666;
    }
    
    .progress-line {
        position: absolute;
        top: 35px;
        left: 10%;
        right: 10%;
        height: 4px;
        background: #e0e0e0;
        z-index: 1;
    }
    
    .progress-line-filled {
        height: 100%;
        background: #4CAF50;
        transition: width 0.5s ease;
    }
    
    .progress-label {
        font-size: 0.9rem;
        text-align: center;
        margin-top: 5px;
        color: #333;
        font-weight: 500;
    }
    
    /* Results cards styling - FIXED */
    .results-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin: 30px 0;
    }
    
    .result-card {
        background: white;
        padding: 30px;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        transition: all 0.3s ease;
    }
    
    .result-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
    }
    
    .card-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 15px;
    }
    
    .card-content {
        color: #666;
        line-height: 1.6;
    }
    
    .savings-amount {
        font-size: 2.5rem;
        font-weight: 700;
        color: #4CAF50;
        margin: 15px 0;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        margin-bottom: 40px;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        color: #333;
        line-height: 1.2;
        margin-bottom: 20px;
    }
    
    .main-subtitle {
        font-size: 1.3rem;
        color: #666;
        margin-bottom: 40px;
    }
    
    /* Upload area - FIXED to work with Streamlit */
    .upload-container {
        margin: 20px 0;
    }
    
    .upload-text {
        text-align: center;
        padding: 40px;
        border: 2px dashed #e0e0e0;
        border-radius: 20px;
        background: #fafafa;
        margin-bottom: 10px;
    }
    
    .upload-icon {
        font-size: 3rem;
        color: #666;
        margin-bottom: 1rem;
    }
    
    .upload-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .upload-subtitle {
        color: #666;
        font-size: 1rem;
    }
    
    /* Streamlit file uploader styling */
    .stFileUploader > div > div > div > div {
        border: none !important;
        background: transparent !important;
    }
    
    .stFileUploader label {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #4CAF50 !important;
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background: #4CAF50;
        color: white;
        border: none;
        padding: 15px 30px;
        border-radius: 25px;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: #45a049;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(76, 175, 80, 0.3);
    }
    
    /* Footer styling */
    .footer-text {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: 40px;
        padding: 20px;
    }
    
    /* Loading animation */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(76, 175, 80, 0.3);
        border-radius: 50%;
        border-top-color: #4CAF50;
        animation: spin 1s ease-in-out infinite;
        margin-right: 10px;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .results-grid {
            grid-template-columns: 1fr;
        }
        
        .main-title {
            font-size: 2rem;
        }
        
        .progress-container {
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .progress-line {
            display: none;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_main_header():
    """Render the main header section"""
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">What's Really Going On<br>With Your Energy Bill?</h1>
        <p class="main-subtitle">Let real AI agents analyze your energy<br>bill and save you money.</p>
    </div>
    """, unsafe_allow_html=True)

def render_upload_section():
    """FIXED: Render upload section that works with Streamlit"""
    st.markdown("""
    <div class="upload-container">
        <div class="upload-text">
            <div class="upload-icon">⬆️</div>
            <div class="upload-title">Upload your bill</div>
            <div class="upload-subtitle">PDF or image</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Streamlit file uploader (this actually works)
    uploaded_file = st.file_uploader(
        "Choose your energy bill",
        type=['pdf', 'jpg', 'jpeg', 'png'],
        help="Upload your latest energy bill for analysis"
    )
    
    return uploaded_file

def render_progress_indicator(current_step: int = 1, total_steps: int = 5):
    """FIXED: Render progress indicator that displays properly"""
    steps = [
        "Upload Bill",
        "Parsing Bill", 
        "Market Scan",
        "Rebate Scan",
        "Savings Summary"
    ]
    
    progress_percentage = ((current_step - 1) / (total_steps - 1)) * 100 if total_steps > 1 else 0
    
    # Build progress HTML
    progress_html = f"""
    <div class="progress-container">
        <div class="progress-line">
            <div class="progress-line-filled" style="width: {progress_percentage}%"></div>
        </div>
    """
    
    for i, step_name in enumerate(steps, 1):
        if i < current_step:
            circle_class = "completed"
            icon = "✓"
        elif i == current_step:
            circle_class = "active"
            icon = str(i)
        else:
            circle_class = "pending"
            icon = str(i)
        
        progress_html += f"""
        <div class="progress-step">
            <div class="progress-circle {circle_class}">{icon}</div>
            <div class="progress-label">{step_name}</div>
        </div>
        """
    
    progress_html += "</div>"
    
    st.markdown(progress_html, unsafe_allow_html=True)

def render_results_cards(analysis_results: Dict[str, Any]):
    """FIXED: Render results matching your actual analysis structure"""
    if not analysis_results:
        return
    
    # Extract data from your actual analysis structure
    final_recs = analysis_results.get('final_recommendations', {})
    total_savings = final_recs.get('total_annual_savings', 0)
    
    # Bill analysis data
    bill_analysis = analysis_results.get('bill_analysis', {})
    if 'analysis' in bill_analysis:
        bill_data = bill_analysis['analysis']
    else:
        bill_data = bill_analysis
    
    usage_profile = bill_data.get('usage_profile', {})
    solar_analysis = bill_data.get('solar_analysis', {})
    efficiency_score = bill_data.get('efficiency_score', 0)
    
    # Market research data
    market_research = analysis_results.get('market_research', {})
    if 'market_research' in market_research:
        market_data = market_research['market_research']
    else:
        market_data = market_research
    
    best_plan = market_data.get('best_plan', {})
    better_plans_found = market_data.get('better_plans_found', 0)
    
    # Rebate data
    rebate_analysis = analysis_results.get('rebate_analysis', {})
    total_rebates = rebate_analysis.get('total_rebate_value', 0)
    rebate_count = rebate_analysis.get('rebate_count', 0)
    
    # Usage optimization data
    usage_optimization = analysis_results.get('usage_optimization', {})
    usage_savings = usage_optimization.get('total_annual_savings', 0)
    
    # Render the cards with actual data
    st.markdown(f"""
    <div class="results-grid">
        <div class="result-card">
            <div class="card-title">Bill Analysis</div>
            <div class="card-content">
                ✅ Usage: {usage_profile.get('total_kwh', 0):,} kWh analyzed<br>
                ✅ Daily average: {usage_profile.get('daily_average', 0):.1f} kWh<br>
                ✅ Category: {usage_profile.get('usage_category', 'Unknown').title()}<br>
                ✅ Efficiency score: {efficiency_score}/100
            </div>
        </div>
        
        <div class="result-card">
            <div class="card-title">Better Plan Available</div>
            <div class="card-content">
    """, unsafe_allow_html=True)
    
    if best_plan.get('retailer') and best_plan.get('annual_savings', 0) > 0:
        st.markdown(f"""
                <strong>{best_plan.get('retailer')}</strong> - {best_plan.get('plan_name', 'Better plan')}<br>
                Annual cost: ${best_plan.get('estimated_annual_cost', 0):,.0f}<br>
                <span style="color: #4CAF50; font-weight: 600;">Save ${best_plan.get('annual_savings', 0):,.0f}/year</span><br>
                {better_plans_found} better plans found
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
                Your current plan is competitive<br>
                No significant savings found<br>
                <span style="color: #666;">Continue with current plan</span><br>
                Market analysis complete
        """, unsafe_allow_html=True)
    
    st.markdown(f"""
            </div>
        </div>
        
        <div class="result-card">
            <div class="card-title">Potential Savings</div>
            <div class="savings-amount">${total_savings:,.0f}</div>
            <div class="card-content">
                Annual savings from all sources:<br>
                • Plan switching: ${best_plan.get('annual_savings', 0):,.0f}<br>
                • Government rebates: ${total_rebates:,.0f}<br>
                • Usage optimization: ${usage_savings:,.0f}
            </div>
        </div>
        
        <div class="result-card">
            <div class="card-title">Rebate Found</div>
            <div class="card-content">
    """, unsafe_allow_html=True)
    
    if total_rebates > 0:
        high_value_rebates = rebate_analysis.get('high_value_rebates', [])
        st.markdown(f"""
                <strong>${total_rebates:,.0f}</strong> in government rebates<br>
                {rebate_count} programs available<br>
                Key rebates: {', '.join(high_value_rebates[:2]) if high_value_rebates else 'Multiple programs'}<br>
                <span style="color: #4CAF50;">Ready to apply</span>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
                No applicable rebates found<br>
                Check eligibility criteria<br>
                Monitor for new programs<br>
                <span style="color: #666;">Keep checking quarterly</span>
        """, unsafe_allow_html=True)
    
    st.markdown("""
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_footer():
    """Render the footer"""
    st.markdown("""
    <div class="footer-text">
        Powered by Google Cloud ADK + Live API Data
    </div>
    """, unsafe_allow_html=True)

def show_analysis_progress(messages: List[str]):
    """FIXED: Show progress without breaking the flow"""
    progress_container = st.empty()
    status_container = st.empty()
    
    for i, message in enumerate(messages, 1):
        # Update progress
        with progress_container.container():
            render_progress_indicator(current_step=i)
        
        # Update status
        with status_container.container():
            st.markdown(f"""
            <div style="text-align: center; margin: 20px 0;">
                <span class="loading-spinner"></span>
                <span style="font-weight: 600;">{message}</span>
            </div>
            """, unsafe_allow_html=True)
        
        time.sleep(1.5)  # Simulate processing time
    
    # Clear the status message but keep final progress
    status_container.empty()
    
    return progress_container

def render_try_another_button():
    """Render the try another bill button"""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Try Another Bill", key="try_another_bill", use_container_width=True):
            return True
    return False