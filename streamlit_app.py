import streamlit as st
import json
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import sys
import os
import time

# Add the src directory to the path to import the crew
sys.path.append('src')

from stock_picker.crew import StockPicker
from memory_utils import MemoryHelper

# Page configuration
st.set_page_config(
    page_title="🏦 AI Stock Picker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .agent-card {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .success-card {
        border-left: 5px solid #28a745;
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .warning-card {
        border-left: 5px solid #ffc107;
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading {filepath}: {e}")
    return None

def load_markdown_file(filepath):
    """Load Markdown file safely"""
    try:
        if Path(filepath).exists():
            with open(filepath, 'r') as f:
                return f.read()
    except Exception as e:
        st.error(f"Error loading {filepath}: {e}")
    return None

def get_memory_stats():
    """Get memory statistics"""
    try:
        memory = MemoryHelper()
        return memory.get_memory_stats()
    except Exception as e:
        st.error(f"Error accessing memory: {e}")
        return {'ltm_count': 0, 'vector_embeddings': 0, 'memory_size_mb': 0}

def create_performance_chart():
    """Create performance chart from memory data"""
    try:
        if not Path("memory/long_term_memory_storage.db").exists():
            return None
        
        conn = sqlite3.connect("memory/long_term_memory_storage.db")
        query = """
        SELECT 
            DATE(datetime, 'unixepoch') as date,
            AVG(score) as avg_score,
            COUNT(*) as task_count
        FROM long_term_memories 
        GROUP BY DATE(datetime, 'unixepoch')
        ORDER BY date
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty:
            fig = px.line(df, x='date', y='avg_score', 
                         title='Task Performance Over Time',
                         line_shape='spline')
            fig.update_layout(height=400)
            return fig
    except Exception as e:
        st.error(f"Error creating chart: {e}")
    return None

def main():
    # Header
    st.markdown('<div class="main-header">🏦 AI Stock Picker Dashboard</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Control Panel")
        
        # Sector selection
        sectors = [
            "Technology", "Finance", "Healthcare", "Energy", 
            "Consumer Goods", "Real Estate", "Transportation",
            "Telecommunications", "Utilities", "Materials"
        ]
        selected_sector = st.selectbox("📊 Select Sector", sectors, index=1)
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        memory_stats = get_memory_stats()
        
        if memory_stats['ltm_count'] > 0:
            st.metric("Previous Analyses", memory_stats['ltm_count'])
            st.info("🧠 System is learning from past decisions")
        else:
            st.info("🆕 Ready for first analysis!")
        
        # System info
        st.subheader("ℹ️ System Info")
        st.caption("Multi-agent AI system with memory-enhanced learning")
        if memory_stats['ltm_count'] > 0:
            st.caption(f"Learning from {memory_stats['ltm_count']} past analyses")

    # Main content tabs
    tab1, tab2 = st.tabs(["🚀 Run Analysis", "📈 Results"])
    
    with tab1:
        st.header("🚀 Stock Analysis Execution")
        
        # Agent status cards
        st.subheader("🤖 AI Agent Team")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            <div class="agent-card">
                <h4>📰 News Analyst</h4>
                <p>Finds trending companies in the news</p>
                <small>Model: GPT-4o-mini</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="agent-card">
                <h4>🔬 Financial Researcher</h4>
                <p>Provides comprehensive company analysis</p>
                <small>Model: GPT-4o-mini</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="agent-card">
                <h4>💰 Stock Picker</h4>
                <p>Selects the best investment opportunity</p>
                <small>Model: GPT-4o-mini</small>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="agent-card">
                <h4>👨‍💼 Manager</h4>
                <p>Coordinates the entire workflow</p>
                <small>Model: GPT-4o-mini</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Execution section
        st.subheader(f"🎯 Analyze {selected_sector} Sector")
        
        # Initialize session state for analysis
        if 'analysis_running' not in st.session_state:
            st.session_state.analysis_running = False
        if 'cancel_analysis' not in st.session_state:
            st.session_state.cancel_analysis = False
        if 'analysis_completed' not in st.session_state:
            st.session_state.analysis_completed = False
        if 'last_analysis_sector' not in st.session_state:
            st.session_state.last_analysis_sector = None
        
        # Disable button during analysis
        analysis_disabled = st.session_state.analysis_running
        
        # Show start button or cancel button based on state
        if not analysis_disabled:
            if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                # Set analysis as running and refresh UI immediately
                st.session_state.analysis_running = True
                st.session_state.cancel_analysis = False
                st.rerun()
        else:
            # Show cancel button when analysis is running
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info("🔄 Analysis in progress... Please wait for completion.")
            with col2:
                if st.button("🛑 Cancel", type="secondary"):
                    st.session_state.cancel_analysis = True
                    st.session_state.analysis_running = False
                    st.warning("⚠️ Analysis cancelled by user")
                    st.rerun()
        
        # Run analysis if triggered and not cancelled
        if st.session_state.analysis_running and not st.session_state.get('cancel_analysis', False):
            with st.spinner("🔄 AI agents are working..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Check for cancellation before each step
                    if st.session_state.get('cancel_analysis', False):
                        st.warning("⚠️ Analysis was cancelled")
                        return
                    
                    # Update progress step by step with timing
                    status_text.text("🔍 Finding trending companies...")
                    progress_bar.progress(25)
                    time.sleep(1)  # Give user time to see progress and potentially cancel
                    
                    if st.session_state.get('cancel_analysis', False):
                        st.warning("⚠️ Analysis was cancelled")
                        return
                    
                    status_text.text("🔬 Conducting financial research...")
                    progress_bar.progress(50)
                    time.sleep(1)  # Give user time to see progress and potentially cancel
                    
                    if st.session_state.get('cancel_analysis', False):
                        st.warning("⚠️ Analysis was cancelled")
                        return
                    
                    status_text.text("💰 Making investment decision...")
                    progress_bar.progress(75)
                    time.sleep(1)  # Give user time to see progress and potentially cancel
                    
                    if st.session_state.get('cancel_analysis', False):
                        st.warning("⚠️ Analysis was cancelled")
                        return
                    
                    # Run the crew
                    inputs = {'sector': selected_sector}
                    result = StockPicker().crew().kickoff(inputs=inputs)
                    
                    if st.session_state.get('cancel_analysis', False):
                        st.warning("⚠️ Analysis was cancelled")
                        return
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Analysis completed!")
                    time.sleep(1)  # Show completion message
                    
                    # Store result in session state
                    st.session_state.last_result = result.raw
                    st.session_state.last_analysis_sector = selected_sector
                    st.session_state.analysis_completed = True
                    
                except Exception as e:
                    st.error(f"❌ Error during analysis: {e}")
                    
                finally:
                    # Reset analysis state
                    st.session_state.analysis_running = False
                    st.session_state.cancel_analysis = False
                    progress_bar.empty()
                    status_text.empty()
                    st.rerun()
        
        # Show success message if analysis just completed
        if st.session_state.analysis_completed:
            st.success("🎉 Stock analysis completed successfully!")
            st.info(f"📊 Analysis for {st.session_state.last_analysis_sector} sector completed. Check the Results tab!")
            # Reset the completed flag after showing the message
            if st.button("✅ Acknowledged", type="secondary"):
                st.session_state.analysis_completed = False
                st.rerun()

    with tab2:
        st.header("📈 Analysis Results")
        
        # Load and display results
        trending_companies = load_json_file("output/trending_companies.json")
        research_report = load_json_file("output/research_report.json")
        decision = load_markdown_file("output/decision.md")
        
        if trending_companies:
            st.subheader("🔥 Trending Companies")
            
            if hasattr(trending_companies, 'get') and trending_companies.get('companies'):
                companies_data = trending_companies['companies']
                df = pd.DataFrame(companies_data)
                
                for idx, company in enumerate(companies_data):
                    with st.expander(f"🏢 {company.get('name', 'Unknown Company')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Ticker:** {company.get('ticker', 'N/A')}")
                        with col2:
                            st.write(f"**Trending Reason:** {company.get('reason', 'N/A')}")
            else:
                st.info("No trending companies data available.")
        
        if research_report:
            st.subheader("📊 Research Analysis")
            
            if hasattr(research_report, 'get') and research_report.get('reports'):
                reports = research_report['reports']
                
                for report in reports:
                    with st.expander(f"📋 {report.get('name', 'Company Report')}"):
                        st.write("**Market Position:**")
                        st.write(report.get('market_position', 'N/A'))
                        
                        st.write("**Future Outlook:**")
                        st.write(report.get('future_outlook', 'N/A'))
                        
                        st.write("**Investment Potential:**")
                        st.write(report.get('investment_potential', 'N/A'))
            else:
                st.info("No research reports available.")
        
        if decision:
            st.subheader("💰 Investment Decision")
            
            # Parse the text decision to extract key information
            def parse_text_decision(text):
                lines = text.strip().split('\n')
                result = {
                    'selected_company': '',
                    'selection_reason': '',
                    'rejected_companies': []
                }
                
                # Extract selected company from first line
                first_line = lines[0] if lines else ''
                if 'chosen company' in first_line.lower():
                    # Extract company name from text like "The chosen company for investment is Baker Hughes Company"
                    parts = first_line.split(' is ')
                    if len(parts) > 1:
                        result['selected_company'] = parts[1].replace('.', '').strip()
                
                # Find selection reason (first paragraph)
                current_paragraph = []
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('The companies that were not selected'):
                        current_paragraph.append(line)
                    elif line.startswith('The companies that were not selected'):
                        break
                
                if len(current_paragraph) > 1:
                    result['selection_reason'] = ' '.join(current_paragraph[1:])
                
                # Extract rejected companies
                in_rejected_section = False
                current_company = None
                current_reason = []
                
                for line in lines:
                    line = line.strip()
                    if 'companies that were not selected' in line.lower():
                        in_rejected_section = True
                        continue
                    elif line.startswith('Overall,') or line.startswith('In conclusion'):
                        break
                    elif in_rejected_section and line:
                        if ':' in line and not line.startswith(' '):
                            # Save previous company if exists
                            if current_company and current_reason:
                                result['rejected_companies'].append({
                                    'name': current_company,
                                    'reason': ' '.join(current_reason)
                                })
                            # Start new company
                            current_company = line.split(':')[0].strip()
                            current_reason = [line.split(':', 1)[1].strip()]
                        elif current_company and line:
                            current_reason.append(line)
                
                # Add last company
                if current_company and current_reason:
                    result['rejected_companies'].append({
                        'name': current_company,
                        'reason': ' '.join(current_reason)
                    })
                
                return result
            
            # Parse the decision text
            parsed_decision = parse_text_decision(decision)
            
            # Display selected company
            if parsed_decision['selected_company']:
                st.markdown("""
                <div class="success-card">
                    <h3>🏆 Selected Investment</h3>
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns([1, 2])
                with col1:
                    st.metric("Company", parsed_decision['selected_company'])
                with col2:
                    st.write("**Investment Rationale:**")
                    st.write(parsed_decision['selection_reason'])
                
                # Display rejected companies
                if parsed_decision['rejected_companies']:
                    st.markdown("---")
                    st.markdown("**🚫 Companies Not Selected:**")
                    
                    for company in parsed_decision['rejected_companies']:
                        with st.expander(f"❌ {company['name']}"):
                            st.write(company['reason'])
            else:
                # Fallback to original markdown display
                st.markdown(decision)
        else:
            st.info("💡 No investment decision available yet. Run an analysis first!")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>🤖 Powered by CrewAI | 📊 Intelligent Stock Analysis | 🎯 Data-Driven Decisions</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main() 