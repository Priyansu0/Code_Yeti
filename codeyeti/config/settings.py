"""
CodeYeti Configuration Settings

This module contains all configuration parameters for the CodeYeti application.
Settings are organized by component for easy maintenance and modification.
"""

from dataclasses import dataclass, field
from typing import List
import os


@dataclass
class Settings:
    """
    Central configuration class for CodeYeti.
    
    Attributes:
        ollama_base_url: URL for Ollama API server
        llm_model: Name of the LLM model to use
        embedding_model: Sentence transformer model for embeddings
        chroma_persist_dir: Directory for ChromaDB persistence
        collection_name: Name of the ChromaDB collection
        chunk_size: Maximum size of code chunks
        chunk_overlap: Overlap between consecutive chunks
        top_k_results: Number of results to retrieve in RAG
        short_code_threshold: Line count threshold for short vs long code
        supported_extensions: List of supported file extensions
        execution_timeout: Timeout for code execution in seconds
    """
    
    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:latest"
    fallback_models: List[str] = field(default_factory=lambda: [
        "qwen2.5:latest",
        "llama3:8b",
        "llama3.2:latest",
        "mistral:latest"
    ])
    
    # Embedding Configuration
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # ChromaDB Configuration
    chroma_persist_dir: str = "./chroma_db"
    collection_name: str = "codeyeti_codebase"
    
    # Chunking Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 100
    
    # RAG Configuration
    top_k_results: int = 5
    
    # Code Display Configuration
    short_code_threshold: int = 30
    
    # File Support Configuration
    supported_extensions: List[str] = field(default_factory=lambda: [
        ".py", ".txt", ".md"
    ])
    
    # Execution Configuration
    execution_timeout: int = 30
    max_output_length: int = 10000
    
    # UI Configuration
    app_title: str = "CodeYeti"
    app_icon: str = "🦬"
    sidebar_width: int = 300
    
    def get_chroma_path(self) -> str:
        """Get the full path for ChromaDB persistence."""
        return os.path.abspath(self.chroma_persist_dir)


# Global settings instance
settings = Settings()
