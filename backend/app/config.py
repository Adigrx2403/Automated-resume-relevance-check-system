import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import field_validator

class Settings(BaseSettings):
    app_name: str = "Resume Relevance Check System"
    app_version: str = "1.0.0"
    secret_key: str = "demo_secret_key_change_in_production"
    
    # Database
    database_url: str = "sqlite:///./resume_relevance.db"
    
    # API Keys
    openai_api_key: str = ""
    huggingface_api_token: str = ""
    langsmith_api_key: str = ""
    langsmith_project: str = "resume-relevance-system"
    
    # File Upload Settings
    max_file_size: int = 10485760  # 10MB
    allowed_extensions: List[str] = ["pdf", "docx"]
    upload_dir: str = "./uploads"
    
    # Model Settings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_model: str = "gpt-3.5-turbo"
    temperature: float = 0.1
    
    # Scoring Weights
    hard_match_weight: float = 0.4
    semantic_match_weight: float = 0.6
    
    # Vector Database
    vector_db_type: str = "chromadb"
    vector_db_path: str = "./vector_store"
    
    @field_validator('allowed_extensions', mode='before')
    @classmethod
    def parse_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v
    
    model_config = {"env_file": ".env", "case_sensitive": False}

# Create settings instance
settings = Settings()

# Ensure upload directories exist
os.makedirs(os.path.join(settings.upload_dir, "resumes"), exist_ok=True)
os.makedirs(os.path.join(settings.upload_dir, "job_descriptions"), exist_ok=True)
os.makedirs(settings.vector_db_path, exist_ok=True)
