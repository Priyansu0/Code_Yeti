"""
CodeYeti UI Layout Module

This module provides custom Streamlit styling and UI components
for a clean, academic, and intuitive interface.
"""

import streamlit as st
from typing import Dict, List, Optional

from codeyeti.config.settings import settings
from codeyeti.utils.helpers import count_lines, is_short_code


def apply_custom_css():
    """
    Apply custom CSS styling to the Streamlit app.
    
    Creates a clean, academic look with custom colors,
    typography, and spacing.
    """
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding: 2rem 3rem;
        max-width: 1200px;
    }
    
    /* Header styling */
    .stApp header {
        background-color: transparent;
    }
    
    /* Custom title styling */
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #5A6C7D;
        margin-bottom: 2rem;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F8F9FA;
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1E3A5F;
        color: white;
    }
    
    /* Code block styling */
    .code-container {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Result containers */
    .result-container {
        background-color: #F0F7FF;
        border-left: 4px solid #1E3A5F;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
    }
    
    .error-container {
        background-color: #FFF0F0;
        border-left: 4px solid #DC3545;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
    }
    
    .success-container {
        background-color: #F0FFF4;
        border-left: 4px solid #28A745;
        padding: 1rem;
        border-radius: 0 10px 10px 0;
        margin: 1rem 0;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #F8F9FA;
    }
    
    section[data-testid="stSidebar"] .block-container {
        padding: 2rem 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Primary button */
    .stButton > button[kind="primary"] {
        background-color: #1E3A5F;
        color: white;
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #CBD5E0;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #1E3A5F;
    }
    
    /* Metric cards */
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A5F;
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #5A6C7D;
    }
    
    /* Info boxes */
    .info-box {
        background-color: #E8F4FD;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Text area styling */
    .stTextArea textarea {
        font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        font-size: 14px;
    }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the application header."""
    st.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <span style="font-size: 3rem;">{settings.app_icon}</span>
        <h1 class="main-title">{settings.app_title}</h1>
        <p class="subtitle">AI-Powered Code Search, Execution & Learning Assistant</p>
    </div>
    """, unsafe_allow_html=True)


def render_sidebar() -> Dict:
    """
    Render the sidebar with file upload and settings.
    
    Returns:
        Dictionary with sidebar selections
    """
    with st.sidebar:
        st.markdown(f"## {settings.app_icon} {settings.app_title}")
        st.markdown("---")
        
        st.markdown("### Upload Files")
        uploaded_files = st.file_uploader(
            "Upload code files (.py, .txt, .md)",
            type=['py', 'txt', 'md'],
            accept_multiple_files=True,
            help="Upload Python, text, or markdown files for analysis"
        )
        
        st.markdown("---")
        st.markdown("### Settings")
        
        top_k = st.slider(
            "Search Results",
            min_value=1,
            max_value=10,
            value=settings.top_k_results,
            help="Number of code chunks to retrieve"
        )
        
        st.markdown("---")
        st.markdown("### Status")
        
        return {
            'uploaded_files': uploaded_files,
            'top_k': top_k
        }


def render_code_display(
    code: str,
    language: str = "python",
    show_run_button: bool = True,
    title: str = None
) -> Optional[bool]:
    """
    Display code with adaptive formatting based on length.
    
    Args:
        code: Source code to display
        language: Programming language
        show_run_button: Whether to show run button
        title: Optional title for the code block
        
    Returns:
        True if run button was clicked, False otherwise
    """
    line_count = count_lines(code)
    is_short = is_short_code(code)
    
    if title:
        st.markdown(f"#### {title}")
    
    st.caption(f"{line_count} lines | {'Short code - Full display' if is_short else 'Long code - Expandable'}")
    
    run_clicked = False
    
    if is_short:
        st.code(code, language=language)
        if show_run_button:
            run_clicked = st.button("Run Code", type="primary", key=f"run_{hash(code)}")
    else:
        st.info("This code has more than 30 lines. Click below to view the full code.")
        with st.expander("View Full Code", expanded=False):
            st.code(code, language=language)
        if show_run_button:
            run_clicked = st.button("Run Code", type="primary", key=f"run_{hash(code)}")
    
    return run_clicked


def render_execution_result(result) -> None:
    """
    Display execution results with proper formatting.
    
    Args:
        result: ExecutionResult object
    """
    if result.success:
        st.markdown("#### Output")
        st.markdown('<div class="success-container">', unsafe_allow_html=True)
        if result.output.strip():
            st.code(result.output, language="text")
        else:
            st.info("Code executed successfully with no output.")
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown("#### Error")
        st.markdown('<div class="error-container">', unsafe_allow_html=True)
        st.error(result.error)
        if result.traceback_str:
            with st.expander("View Full Traceback"):
                st.code(result.traceback_str, language="python")
        st.markdown('</div>', unsafe_allow_html=True)


def render_debug_report(analysis: Dict) -> None:
    """
    Display debug analysis report.
    
    Args:
        analysis: Dictionary from DebugAgent.analyze_error
    """
    if not analysis.get('has_error'):
        show_success_message("No errors to debug. Code executed successfully!")
        return
    
    st.markdown("### Debug Report")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Error Type:** `{analysis.get('error_type', 'Unknown')}`")
    with col2:
        if analysis.get('location'):
            st.markdown(f"**Location:** {analysis['location']}")
    
    if analysis.get('error_message'):
        st.error(f"**Error:** {analysis['error_message']}")
    
    if analysis.get('analysis'):
        st.markdown("#### Cause")
        st.markdown(analysis['analysis'])
    
    if analysis.get('fix_explanation'):
        st.markdown("#### How to Fix")
        st.markdown(analysis['fix_explanation'])
    
    if analysis.get('suggested_fix'):
        st.markdown("#### Suggested Fix")
        st.warning("The code below is a **suggested fix**. Review before using.")
        st.code(analysis['suggested_fix'], language="python")


def show_info_message(message: str):
    """Display an info message."""
    st.info(message)


def show_success_message(message: str):
    """Display a success message."""
    st.success(message)


def show_error_message(message: str):
    """Display an error message."""
    st.error(message)


def show_warning_message(message: str):
    """Display a warning message."""
    st.warning(message)


def render_search_result(result: Dict, index: int) -> None:
    """
    Display a single search result.
    
    Args:
        result: Search result dictionary
        index: Result index for display
    """
    metadata = result.get('metadata', {})
    score = result.get('score', 0)
    content = result.get('content', '')
    
    filename = metadata.get('filename', 'Unknown')
    chunk_type = metadata.get('chunk_type', 'code')
    name = metadata.get('name', '')
    
    with st.expander(
        f"**{index + 1}.** {filename} | {chunk_type}: {name} | Score: {score:.2f}",
        expanded=(index == 0)
    ):
        st.code(content, language="python")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"Lines: {metadata.get('start_line', '?')}-{metadata.get('end_line', '?')}")
        with col2:
            st.caption(f"Type: {chunk_type}")
        with col3:
            st.caption(f"Relevance: {score:.2%}")


def render_stats_cards(stats: Dict) -> None:
    """
    Display statistics as cards.
    
    Args:
        stats: Dictionary with statistics
    """
    cols = st.columns(len(stats))
    for i, (label, value) in enumerate(stats.items()):
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{value}</div>
                <div class="metric-label">{label}</div>
            </div>
            """, unsafe_allow_html=True)
