"""
CodeYeti Embeddings Module

This module handles generating embeddings using Sentence Transformers
and managing the ChromaDB vector store.
"""

import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

from codeyeti.config.settings import settings


class EmbeddingManager:
    """
    Manages embedding generation and ChromaDB vector storage.
    
    Uses Sentence Transformers for generating embeddings and
    ChromaDB for persistent vector storage and retrieval.
    """
    
    def __init__(self):
        """Initialize the EmbeddingManager with models and database."""
        self.model = None
        self.client = None
        self.collection = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the embedding model and ChromaDB client."""
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=settings.get_chroma_path(),
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"description": "CodeYeti code embeddings"}
        )
    
    def _get_model(self):
        """Lazy load the sentence transformer model."""
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(settings.embedding_model)
            except Exception as e:
                print(f"Error loading embedding model: {e}")
                raise
        return self.model
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        model = self._get_model()
        embeddings = model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()
    
    def add_chunks(self, chunks: List[Dict]) -> int:
        """
        Add code chunks to the vector database.
        
        Args:
            chunks: List of chunk dictionaries with content and metadata
            
        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0
        
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            content = chunk.get('content', '')
            if not content.strip():
                continue
            
            chunk_id = chunk.get('chunk_id', f"chunk_{len(ids)}")
            
            metadata = {
                'filename': chunk.get('filename', 'unknown'),
                'filepath': chunk.get('filepath', ''),
                'chunk_type': chunk.get('chunk_type', 'unknown'),
                'name': chunk.get('name', ''),
                'start_line': chunk.get('start_line', 0),
                'end_line': chunk.get('end_line', 0),
            }
            
            if chunk.get('docstring'):
                metadata['docstring'] = chunk['docstring'][:500]
            
            documents.append(content)
            metadatas.append(metadata)
            ids.append(chunk_id)
        
        if documents:
            embeddings = self.generate_embeddings(documents)
            
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
        
        return len(documents)
    
    def search(self, query: str, top_k: int = None) -> List[Dict]:
        """
        Search for similar code chunks.
        
        Args:
            query: Natural language query
            top_k: Number of results to return
            
        Returns:
            List of matching chunks with scores
        """
        if top_k is None:
            top_k = settings.top_k_results
        
        query_embedding = self.generate_embeddings([query])[0]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=['documents', 'metadatas', 'distances']
        )
        
        matches = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                match = {
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                    'distance': results['distances'][0][i] if results['distances'] else 0,
                    'score': 1 - (results['distances'][0][i] if results['distances'] else 0)
                }
                matches.append(match)
        
        return matches
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the vector collection.
        
        Returns:
            Dictionary with collection statistics
        """
        count = self.collection.count()
        return {
            'total_chunks': count,
            'collection_name': settings.collection_name,
            'persist_directory': settings.chroma_persist_dir
        }
    
    def clear_collection(self) -> bool:
        """
        Clear all documents from the collection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(settings.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=settings.collection_name,
                metadata={"description": "CodeYeti code embeddings"}
            )
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False
    
    def delete_by_filename(self, filename: str) -> int:
        """
        Delete all chunks from a specific file.
        
        Args:
            filename: Name of the file to delete chunks for
            
        Returns:
            Number of chunks deleted
        """
        try:
            results = self.collection.get(
                where={"filename": filename},
                include=[]
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                return len(results['ids'])
            return 0
        except Exception as e:
            print(f"Error deleting chunks for {filename}: {e}")
            return 0
