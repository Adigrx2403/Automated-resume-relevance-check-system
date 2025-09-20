import numpy as np
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import logging
from ..config import settings
from ..utils.text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and managing text embeddings."""
    
    def __init__(self):
        """Initialize the embedding service."""
        try:
            self.model = SentenceTransformer(settings.embedding_model)
            self.preprocessor = TextPreprocessor()
            self._init_vector_store()
        except Exception as e:
            logger.error(f"Error initializing embedding service: {str(e)}")
            raise
    
    def _init_vector_store(self):
        """Initialize the vector store (ChromaDB)."""
        try:
            if settings.vector_db_type == "chromadb":
                self.client = chromadb.PersistentClient(
                    path=settings.vector_db_path,
                    settings=Settings(anonymized_telemetry=False)
                )
                
                # Create collections for resumes and job descriptions
                self.resume_collection = self.client.get_or_create_collection(
                    name="resumes",
                    metadata={"description": "Resume embeddings"}
                )
                
                self.job_collection = self.client.get_or_create_collection(
                    name="job_descriptions",
                    metadata={"description": "Job description embeddings"}
                )
            else:
                raise ValueError(f"Unsupported vector database: {settings.vector_db_type}")
                
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for given text.
        
        Args:
            text: Input text
            
        Returns:
            Numpy array representing the embedding
        """
        try:
            # Preprocess text
            clean_text = self.preprocessor.preprocess_text(text)
            
            if not clean_text:
                return np.zeros(self.model.get_sentence_embedding_dimension())
            
            # Generate embedding
            embedding = self.model.encode(clean_text)
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            return np.zeros(self.model.get_sentence_embedding_dimension())
    
    def store_resume_embedding(self, resume_id: str, text: str, metadata: Dict = None):
        """
        Store resume embedding in vector database.
        
        Args:
            resume_id: Unique identifier for the resume
            text: Resume text
            metadata: Additional metadata
        """
        try:
            embedding = self.generate_embedding(text)
            
            self.resume_collection.add(
                embeddings=[embedding.tolist()],
                documents=[text[:1000]],  # Store first 1000 chars as document
                metadatas=[metadata or {}],
                ids=[resume_id]
            )
            
        except Exception as e:
            logger.error(f"Error storing resume embedding: {str(e)}")
    
    def store_job_embedding(self, job_id: str, text: str, metadata: Dict = None):
        """
        Store job description embedding in vector database.
        
        Args:
            job_id: Unique identifier for the job description
            text: Job description text
            metadata: Additional metadata
        """
        try:
            embedding = self.generate_embedding(text)
            
            self.job_collection.add(
                embeddings=[embedding.tolist()],
                documents=[text[:1000]],
                metadatas=[metadata or {}],
                ids=[job_id]
            )
            
        except Exception as e:
            logger.error(f"Error storing job embedding: {str(e)}")
    
    def calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity between two texts.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            embedding1 = self.generate_embedding(text1)
            embedding2 = self.generate_embedding(text2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            
            # Ensure similarity is between 0 and 1
            similarity = max(0, min(1, (similarity + 1) / 2))
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}")
            return 0.0
    
    def find_similar_resumes(self, job_text: str, n_results: int = 10) -> List[Dict]:
        """
        Find resumes most similar to a job description.
        
        Args:
            job_text: Job description text
            n_results: Number of results to return
            
        Returns:
            List of similar resumes with metadata
        """
        try:
            embedding = self.generate_embedding(job_text)
            
            results = self.resume_collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=n_results
            )
            
            similar_resumes = []
            for i, (resume_id, distance, metadata) in enumerate(
                zip(results['ids'][0], results['distances'][0], results['metadatas'][0])
            ):
                similarity = 1 - distance  # Convert distance to similarity
                similar_resumes.append({
                    'resume_id': resume_id,
                    'similarity': similarity,
                    'metadata': metadata
                })
            
            return similar_resumes
            
        except Exception as e:
            logger.error(f"Error finding similar resumes: {str(e)}")
            return []
    
    def find_similar_jobs(self, resume_text: str, n_results: int = 10) -> List[Dict]:
        """
        Find job descriptions most similar to a resume.
        
        Args:
            resume_text: Resume text
            n_results: Number of results to return
            
        Returns:
            List of similar job descriptions with metadata
        """
        try:
            embedding = self.generate_embedding(resume_text)
            
            results = self.job_collection.query(
                query_embeddings=[embedding.tolist()],
                n_results=n_results
            )
            
            similar_jobs = []
            for i, (job_id, distance, metadata) in enumerate(
                zip(results['ids'][0], results['distances'][0], results['metadatas'][0])
            ):
                similarity = 1 - distance
                similar_jobs.append({
                    'job_id': job_id,
                    'similarity': similarity,
                    'metadata': metadata
                })
            
            return similar_jobs
            
        except Exception as e:
            logger.error(f"Error finding similar jobs: {str(e)}")
            return []
