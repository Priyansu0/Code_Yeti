"""
CodeYeti Retriever Module

This module handles the complete RAG pipeline for code retrieval,
combining semantic search with LLM-based answer generation.
"""

from typing import List, Dict, Optional
import ollama

from codeyeti.config.settings import settings
from codeyeti.rag.embeddings import EmbeddingManager


class CodeRetriever:
    """
    Handles semantic code retrieval and RAG-based answer generation.
    
    Combines vector similarity search with local LLM processing
    to answer questions about code using retrieved context.
    """
    
    def __init__(self, embedding_manager: Optional[EmbeddingManager] = None):
        """
        Initialize the CodeRetriever.
        
        Args:
            embedding_manager: Optional EmbeddingManager instance
        """
        self.embedding_manager = embedding_manager or EmbeddingManager()
        self.llm_model = settings.llm_model
        self.ollama_url = settings.ollama_base_url
    
    def retrieve(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Retrieve relevant code chunks for a query.
        
        Args:
            query: Natural language question
            top_k: Number of results to return
            
        Returns:
            List of relevant code chunks with metadata
        """
        if top_k is None:
            top_k = settings.top_k_results
        
        results = self.embedding_manager.search(query, top_k)
        return results
    
    def generate_answer(self, query: str, context_chunks: List[Dict]) -> str:
        """
        Generate an answer using retrieved context and LLM.
        
        Args:
            query: User's question
            context_chunks: Retrieved code chunks
            
        Returns:
            Generated answer string
        """
        context = self._format_context(context_chunks)
        
        prompt = f"""You are CodeYeti, an expert code assistant. Answer the user's question based on the provided code context.

CODE CONTEXT:
{context}

USER QUESTION: {query}

Provide a clear, helpful answer. If the code context is relevant, reference it specifically. If the context doesn't contain relevant information, say so honestly.

ANSWER:"""

        try:
            response = ollama.generate(
                model=self.llm_model,
                prompt=prompt,
                options={
                    'temperature': 0.3,
                    'num_predict': 1024
                }
            )
            return response['response'].strip()
        except Exception as e:
            return f"Error generating answer: {str(e)}. Please ensure Ollama is running with the {self.llm_model} model."
    
    def search_and_answer(self, query: str, top_k: int = None) -> Dict:
        """
        Complete RAG pipeline: retrieve and generate answer.
        
        Args:
            query: User's question
            top_k: Number of chunks to retrieve
            
        Returns:
            Dictionary with answer and retrieved chunks
        """
        chunks = self.retrieve(query, top_k)
        
        if not chunks:
            return {
                'answer': "No relevant code found in the indexed codebase. Please upload and index some code files first.",
                'chunks': [],
                'query': query
            }
        
        answer = self.generate_answer(query, chunks)
        
        return {
            'answer': answer,
            'chunks': chunks,
            'query': query
        }
    
    def _format_context(self, chunks: List[Dict]) -> str:
        """
        Format retrieved chunks into a context string.
        
        Args:
            chunks: List of retrieved chunks
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            metadata = chunk.get('metadata', {})
            filename = metadata.get('filename', 'unknown')
            chunk_type = metadata.get('chunk_type', 'code')
            name = metadata.get('name', '')
            content = chunk.get('content', '')
            
            header = f"[{i+1}] File: {filename}"
            if name:
                header += f" | {chunk_type}: {name}"
            
            context_parts.append(f"{header}\n```\n{content}\n```")
        
        return "\n\n".join(context_parts)
    
    def check_ollama_status(self) -> Dict:
        """
        Check if Ollama is running and model is available.
        
        Returns:
            Dictionary with status information
        """
        try:
            models = ollama.list()
            model_names = [m['name'] for m in models.get('models', [])]
            
            model_available = any(
                self.llm_model in name or name.startswith(self.llm_model.split(':')[0])
                for name in model_names
            )
            
            return {
                'connected': True,
                'model_available': model_available,
                'current_model': self.llm_model,
                'available_models': model_names
            }
        except Exception as e:
            return {
                'connected': False,
                'model_available': False,
                'error': str(e),
                'current_model': self.llm_model,
                'available_models': []
            }
    
    def set_model(self, model_name: str):
        """
        Set the LLM model to use.
        
        Args:
            model_name: Name of the Ollama model
        """
        self.llm_model = model_name
