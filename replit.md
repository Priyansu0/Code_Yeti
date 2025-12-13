# CodeYeti

AI-Powered Code Retrieval, Execution, Analysis, and Learning Assistant

## Overview

CodeYeti is an intelligent assistant that helps developers search, understand, run, debug, and learn from codebases using RAG (Retrieval-Augmented Generation) and local LLMs via Ollama.

## Architecture

```
codeyeti/
├── app.py                  # Main Streamlit application entry point
├── config/
│   └── settings.py         # Application configuration settings
├── utils/
│   └── helpers.py          # Utility functions
├── rag/
│   ├── loader.py           # File loading and parsing
│   ├── chunker.py          # AST-based code chunking
│   ├── embeddings.py       # Sentence Transformer embeddings + ChromaDB
│   └── retriever.py        # RAG semantic search + LLM answer generation
├── runner/
│   └── python_runner.py    # Safe Python code execution
├── agents/
│   ├── explainer.py        # Learning-focused code explanations
│   └── debugger.py         # Error analysis and debugging assistance
├── summarizer/
│   └── summary.py          # File and project summarization
└── ui/
    └── layout.py           # Custom Streamlit CSS and UI components
```

## Technical Stack

- **Frontend**: Streamlit with custom CSS theming
- **LLM**: Ollama (Qwen2.5 / LLaMA 3 / Mistral)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Database**: ChromaDB (persistent storage)
- **Code Analysis**: Python AST for intelligent chunking

## Features

### 1. Code Search (RAG)
- Upload Python, text, or markdown files
- Semantic search using natural language queries
- Retrieves relevant code chunks with context

### 2. Run Code
- Safe Python execution environment
- Captures stdout, stderr, and tracebacks
- Timeout protection and output truncation

### 3. Explain Code
- Adaptive explanation based on code length:
  - Short code (≤30 lines): Full display + line-by-line explanation
  - Long code (>30 lines): High-level overview + expandable view
- Beginner-friendly explanations

### 4. Debug Assistant
- Automatic error analysis on execution failures
- Root cause identification
- Step-by-step fix explanations
- Suggested code fixes (shown separately, clearly labeled)

### 5. Project Summary
- Summarize individual files or entire projects
- Extract functions, classes, and imports
- High-level architecture overview

## Requirements for Full Functionality

For the AI-powered features (explanations, debugging, summaries, RAG answers), you need:
- **Ollama** installed and running locally
- A compatible model: `qwen2.5:latest`, `llama3:8b`, or `mistral:latest`

Without Ollama, the app will still work for:
- Code execution
- File indexing
- Syntax validation

## Running the Application

```bash
streamlit run app.py --server.port 5000
```

## Configuration

Key settings in `codeyeti/config/settings.py`:
- `llm_model`: Default LLM model for Ollama
- `embedding_model`: Sentence transformer model
- `short_code_threshold`: 30 lines (for adaptive display)
- `top_k_results`: Number of search results
- `execution_timeout`: Code execution timeout (seconds)

## Recent Changes

- **December 2024**: Initial implementation with all core features
  - Modular architecture with clean separation of concerns
  - Custom CSS theming for academic/professional look
  - Adaptive code display based on line count
  - Comprehensive error handling and user feedback
