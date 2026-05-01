# CodeYeti

CodeYeti is an AI-powered coding assistant designed to help learners understand, search, run, summarize, and debug code. It uses local LLM support through Ollama, semantic retrieval with ChromaDB, and a Streamlit-based interface for an interactive learning experience.

## GitHub Repository

SSH remote:

```bash
git@github.com:Priyansu0/Code_Yeti.git
```

Repository URL:

[github.com/Priyansu0/Code_Yeti](https://github.com/Priyansu0/Code_Yeti)

## Features

- AI code explanations for short and long code snippets
- Beginner-friendly debugging help with suggested fixes
- Safe Python code execution with security checks and timeout handling
- Semantic code search using ChromaDB vector storage
- RAG-based question answering over uploaded code files
- File and project summarization
- Clean Streamlit UI components

## Project Structure

```text
codeyeti/
├── agents/        # Code explanation and debugging agents
├── config/        # Application settings
├── rag/           # File loading, chunking, embeddings, and retrieval
├── runner/        # Safe Python code execution
├── summarizer/    # Code and project summarization
├── ui/            # Streamlit layout and styling helpers
└── utils/         # Shared utility functions
```

## Requirements

- Python 3.10+
- Ollama installed and running locally
- An Ollama model such as `qwen2.5:latest`

Python packages used by the project include:

- `ollama`
- `streamlit`
- `chromadb`

## Setup

1. Clone the repository:

```bash
git clone git@github.com:Priyansu0/Code_Yeti.git
cd Code_Yeti
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install ollama streamlit chromadb
```

4. Start Ollama and pull the recommended model:

```bash
ollama pull qwen2.5:latest
```

## Usage

Import and use CodeYeti modules in Python:

```python
from codeyeti.agents.explainer import CodeExplainer

explainer = CodeExplainer()
result = explainer.explain("print('Hello, CodeYeti!')")
print(result["explanation"])
```

## Notes

- The default Ollama endpoint is `http://localhost:11434`.
- The default model is `qwen2.5:latest`.
- ChromaDB data is stored locally in `./chroma_db` and should not be committed to Git.

## License

Add a license file if you plan to make this project open source.
