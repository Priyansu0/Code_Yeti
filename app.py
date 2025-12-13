"""
CodeYeti - AI-Powered Code Retrieval, Execution, Analysis, and Learning Assistant

Main Streamlit application entry point.
This file orchestrates all modules and provides the user interface.
"""

import streamlit as st
from typing import Optional

from codeyeti.config.settings import settings
from codeyeti.ui.layout import (
    apply_custom_css,
    render_header,
    render_sidebar,
    render_code_display,
    render_execution_result,
    render_debug_report,
    render_search_result,
    show_info_message,
    show_success_message,
    show_error_message,
    show_warning_message
)
from codeyeti.rag.loader import FileLoader
from codeyeti.rag.chunker import CodeChunker
from codeyeti.rag.embeddings import EmbeddingManager
from codeyeti.rag.retriever import CodeRetriever
from codeyeti.runner.python_runner import PythonRunner
from codeyeti.agents.explainer import CodeExplainer
from codeyeti.agents.debugger import DebugAgent
from codeyeti.summarizer.summary import CodeSummarizer
from codeyeti.utils.helpers import is_short_code, count_lines


st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_css()


@st.cache_resource
def get_embedding_manager():
    """Get or create the embedding manager (cached)."""
    return EmbeddingManager()


@st.cache_resource
def get_retriever():
    """Get or create the code retriever (cached)."""
    return CodeRetriever(get_embedding_manager())


@st.cache_resource
def get_runner():
    """Get or create the Python runner (cached)."""
    return PythonRunner()


@st.cache_resource
def get_explainer():
    """Get or create the code explainer (cached)."""
    return CodeExplainer()


@st.cache_resource
def get_debugger():
    """Get or create the debug agent (cached)."""
    return DebugAgent()


@st.cache_resource
def get_summarizer():
    """Get or create the code summarizer (cached)."""
    return CodeSummarizer()


def initialize_session_state():
    """Initialize session state variables."""
    if 'indexed_files' not in st.session_state:
        st.session_state.indexed_files = []
    if 'last_execution_result' not in st.session_state:
        st.session_state.last_execution_result = None
    if 'last_code' not in st.session_state:
        st.session_state.last_code = ""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None


def handle_file_upload(uploaded_files, embedding_manager: EmbeddingManager):
    """
    Handle file upload and indexing.
    
    Args:
        uploaded_files: List of Streamlit uploaded files
        embedding_manager: EmbeddingManager instance
    """
    if not uploaded_files:
        return
    
    loader = FileLoader()
    chunker = CodeChunker()
    
    files = loader.load_uploaded_files(uploaded_files)
    
    if not files:
        show_warning_message("No supported files found in upload.")
        return
    
    all_chunks = []
    for file_data in files:
        chunks = chunker.chunk_file(file_data)
        all_chunks.extend(chunks)
    
    if all_chunks:
        count = embedding_manager.add_chunks(all_chunks)
        st.session_state.indexed_files.extend([f['filename'] for f in files])
        show_success_message(f"Indexed {count} code chunks from {len(files)} file(s).")


def render_code_search_tab(retriever: CodeRetriever, top_k: int):
    """Render the Code Search (RAG) tab."""
    st.markdown("### Search Your Codebase")
    st.markdown("Ask questions about your code in natural language.")
    
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., How does the authentication function work?",
        key="search_query"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        search_clicked = st.button("Search", type="primary", key="search_btn")
    
    if search_clicked and query:
        with st.spinner("Searching codebase..."):
            result = retriever.search_and_answer(query, top_k)
            st.session_state.search_results = result
    
    if st.session_state.search_results:
        result = st.session_state.search_results
        
        st.markdown("---")
        st.markdown("### Answer")
        st.markdown(result['answer'])
        
        if result['chunks']:
            st.markdown("---")
            st.markdown("### Relevant Code")
            
            for i, chunk in enumerate(result['chunks']):
                render_search_result(chunk, i)
    
    stats = retriever.embedding_manager.get_collection_stats()
    st.sidebar.markdown(f"**Indexed Chunks:** {stats['total_chunks']}")


def render_run_code_tab(runner: PythonRunner, debugger: DebugAgent):
    """Render the Run Code tab."""
    st.markdown("### Python Code Runner")
    st.markdown("Enter Python code to execute safely.")
    
    code = st.text_area(
        "Enter Python code:",
        height=300,
        placeholder="# Enter your Python code here\nprint('Hello, CodeYeti!')",
        key="run_code_input"
    )
    
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        run_clicked = st.button("Run Code", type="primary", key="run_btn")
    with col2:
        validate_clicked = st.button("Validate Only", key="validate_btn")
    
    if validate_clicked and code:
        is_valid, error = runner.validate_code(code)
        if is_valid:
            show_success_message("Code syntax is valid!")
        else:
            show_error_message(f"Syntax Error: {error}")
    
    if run_clicked and code:
        st.session_state.last_code = code
        
        with st.spinner("Executing code..."):
            result = runner.execute(code)
            st.session_state.last_execution_result = result
        
        st.markdown("---")
        render_execution_result(result)
        
        if not result.success:
            st.markdown("---")
            with st.expander("View Debug Analysis", expanded=True):
                analysis = debugger.analyze_error(code, result)
                render_debug_report(analysis)


def render_explain_code_tab(explainer: CodeExplainer, runner: PythonRunner):
    """Render the Explain Code tab."""
    st.markdown("### Code Explanation")
    st.markdown("Get beginner-friendly explanations of Python code.")
    
    code = st.text_area(
        "Enter code to explain:",
        height=250,
        placeholder="# Paste Python code here to get an explanation",
        key="explain_code_input"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        explain_clicked = st.button("Explain", type="primary", key="explain_btn")
    
    if explain_clicked and code:
        line_count = count_lines(code)
        is_short = is_short_code(code)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Lines of Code", line_count)
        with col2:
            st.metric("Display Mode", "Full + Detailed" if is_short else "Overview")
        
        if is_short:
            st.markdown("#### Code")
            st.code(code, language="python")
        else:
            st.info("Code has more than 30 lines. Showing high-level overview.")
            with st.expander("View Full Code"):
                st.code(code, language="python")
        
        st.markdown("---")
        st.markdown("#### Explanation")
        
        with st.spinner("Generating explanation..."):
            result = explainer.explain(code)
        
        st.markdown(result['explanation'])
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Run This Code", key="explain_run_btn"):
                with st.spinner("Executing..."):
                    exec_result = runner.execute(code)
                render_execution_result(exec_result)


def render_debug_tab(debugger: DebugAgent, runner: PythonRunner):
    """Render the Debug Assistant tab."""
    st.markdown("### Debug Assistant")
    st.markdown("Analyze errors and get step-by-step fix suggestions.")
    
    code = st.text_area(
        "Enter code with error:",
        height=250,
        placeholder="# Paste Python code that has an error",
        key="debug_code_input"
    )
    
    col1, col2 = st.columns([1, 1])
    with col1:
        debug_clicked = st.button("Run & Debug", type="primary", key="debug_btn")
    with col2:
        if st.session_state.last_execution_result and not st.session_state.last_execution_result.success:
            if st.button("Debug Last Execution", key="debug_last_btn"):
                code = st.session_state.last_code
                debug_clicked = True
    
    if debug_clicked and code:
        st.markdown("---")
        
        with st.spinner("Executing and analyzing..."):
            result = runner.execute(code)
        
        st.markdown("#### Execution Result")
        render_execution_result(result)
        
        if not result.success:
            st.markdown("---")
            
            with st.spinner("Analyzing error..."):
                analysis = debugger.analyze_error(code, result)
            
            render_debug_report(analysis)
            
            quick_fixes = debugger.suggest_quick_fixes(code, analysis.get('error_type', ''))
            if quick_fixes:
                st.markdown("#### Quick Fix Suggestions")
                for fix in quick_fixes:
                    st.markdown(f"- {fix}")
        else:
            show_success_message("Code executed successfully! No errors to debug.")


def render_summary_tab(summarizer: CodeSummarizer):
    """Render the Project Summary tab."""
    st.markdown("### Project Summary")
    st.markdown("Get summaries of individual files or entire projects.")
    
    tab1, tab2 = st.tabs(["Summarize Code", "Summarize Files"])
    
    with tab1:
        code = st.text_area(
            "Enter code to summarize:",
            height=250,
            placeholder="# Paste code here to get a summary",
            key="summary_code_input"
        )
        
        if st.button("Generate Summary", type="primary", key="summary_code_btn"):
            if code:
                with st.spinner("Generating summary..."):
                    result = summarizer.summarize_code(code)
                
                st.markdown("---")
                st.markdown("#### Summary")
                st.markdown(result['summary'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Lines", result['line_count'])
                with col2:
                    st.metric("Characters", result['char_count'])
                
                st.markdown("---")
                st.markdown("#### Code Components")
                components = summarizer.extract_components(code)
                
                if components['functions']:
                    st.markdown("**Functions:**")
                    for func in components['functions']:
                        st.markdown(f"- `{func['name']}` (lines {func['start_line']}-{func['end_line']})")
                
                if components['classes']:
                    st.markdown("**Classes:**")
                    for cls in components['classes']:
                        st.markdown(f"- `{cls['name']}` (lines {cls['start_line']}-{cls['end_line']})")
                
                if components['imports']:
                    st.markdown("**Imports:**")
                    for imp in components['imports'][:10]:
                        st.markdown(f"- `{imp}`")
    
    with tab2:
        uploaded = st.file_uploader(
            "Upload files to summarize:",
            type=['py', 'txt', 'md'],
            accept_multiple_files=True,
            key="summary_file_upload"
        )
        
        if uploaded and st.button("Summarize Project", type="primary", key="summary_files_btn"):
            loader = FileLoader()
            files = loader.load_uploaded_files(uploaded)
            
            if files:
                with st.spinner("Generating project summary..."):
                    result = summarizer.summarize_files(files)
                
                st.markdown("---")
                st.markdown("#### Project Overview")
                st.markdown(result['project_summary'])
                
                st.markdown("---")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Files", result['stats']['total_files'])
                with col2:
                    st.metric("Total Lines", result['stats']['total_lines'])
                
                st.markdown("---")
                st.markdown("#### File Details")
                for file_info in result['file_summaries']:
                    with st.expander(f"{file_info['filename']} ({file_info['lines']} lines)"):
                        if file_info['components']:
                            for comp in file_info['components']:
                                st.markdown(f"- {comp}")
                        else:
                            st.markdown("No major components detected.")


def render_status_sidebar(retriever: CodeRetriever):
    """Render status information in sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.markdown("### System Status")
    
    status = retriever.check_ollama_status()
    
    if status['connected']:
        st.sidebar.success("Ollama: Connected")
        if status['model_available']:
            st.sidebar.success(f"Model: {status['current_model']}")
        else:
            st.sidebar.warning(f"Model '{status['current_model']}' not found")
            if status['available_models']:
                st.sidebar.info(f"Available: {', '.join(status['available_models'][:3])}")
    else:
        st.sidebar.error("Ollama: Not Connected")
        st.sidebar.info("Start Ollama to enable AI features")
    
    stats = retriever.embedding_manager.get_collection_stats()
    st.sidebar.metric("Indexed Chunks", stats['total_chunks'])
    
    if st.session_state.indexed_files:
        st.sidebar.markdown("**Indexed Files:**")
        for fname in st.session_state.indexed_files[-5:]:
            st.sidebar.caption(f"- {fname}")


def main():
    """Main application entry point."""
    initialize_session_state()
    
    render_header()
    
    sidebar_data = render_sidebar()
    
    embedding_manager = get_embedding_manager()
    retriever = get_retriever()
    runner = get_runner()
    explainer = get_explainer()
    debugger = get_debugger()
    summarizer = get_summarizer()
    
    if sidebar_data['uploaded_files']:
        handle_file_upload(sidebar_data['uploaded_files'], embedding_manager)
    
    render_status_sidebar(retriever)
    
    tabs = st.tabs([
        "Search Code",
        "Run Code",
        "Explain Code",
        "Debug Assistant",
        "Project Summary"
    ])
    
    with tabs[0]:
        render_code_search_tab(retriever, sidebar_data['top_k'])
    
    with tabs[1]:
        render_run_code_tab(runner, debugger)
    
    with tabs[2]:
        render_explain_code_tab(explainer, runner)
    
    with tabs[3]:
        render_debug_tab(debugger, runner)
    
    with tabs[4]:
        render_summary_tab(summarizer)


if __name__ == "__main__":
    main()
