from fastapi import FastAPI, File, UploadFile, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import os
import shutil
from typing import List, Optional
import logging
from datetime import datetime

from .config import settings
from .models import (
    get_db, init_database, JobDescriptionCRUD, ResumeCRUD, EvaluationCRUD,
    SystemLogCRUD, JobDescription, Resume, Evaluation
)
from .utils import DocumentParser
from .services import MatchingEngine, EmbeddingService

# Pydantic models for request/response
class EvaluationRequest(BaseModel):
    job_id: int
    resume_id: int

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API for automated resume relevance checking system"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
matching_engine = MatchingEngine()
embedding_service = EmbeddingService()
document_parser = DocumentParser()

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    try:
        init_database()
        logger.info("Application started successfully")
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        raise

# Helper functions
def save_uploaded_file(file: UploadFile, folder: str) -> str:
    """Save uploaded file and return the file path."""
    try:
        # Create folder if it doesn't exist
        os.makedirs(folder, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(folder, filename)
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return file_path
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save file")

def validate_file(file: UploadFile) -> bool:
    """Validate uploaded file."""
    if file.size > settings.max_file_size:
        raise HTTPException(status_code=413, detail="File too large")
    
    file_ext = os.path.splitext(file.filename)[1].lower()[1:]  # Remove the dot
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(settings.allowed_extensions)}"
        )
    
    return True

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Resume Relevance Check System API",
        "version": settings.app_version,
        "status": "active"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Job Description endpoints
@app.post("/api/job-descriptions/upload")
async def upload_job_description(
    file: UploadFile = File(...),
    title: str = "",
    company: str = "",
    location: str = "",
    created_by: str = "",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Upload and process a job description."""
    try:
        # Validate file
        validate_file(file)
        
        # Save file
        folder = os.path.join(settings.upload_dir, "job_descriptions")
        file_path = save_uploaded_file(file, folder)
        
        # Extract text
        extracted_text = document_parser.extract_text(file_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Create job description record
        job_data = {
            "title": title or file.filename,
            "company": company,
            "location": location,
            "original_filename": file.filename,
            "file_path": file_path,
            "extracted_text": extracted_text,
            "created_by": created_by
        }
        
        job = JobDescriptionCRUD.create(db, job_data)
        
        # Process in background
        background_tasks.add_task(process_job_description, job.id, extracted_text)
        
        # Log activity
        SystemLogCRUD.create_log(db, {
            "action": "job_description_uploaded",
            "resource_type": "job_description",
            "resource_id": job.id,
            "details": {"filename": file.filename, "title": title}
        })
        
        return {
            "message": "Job description uploaded successfully",
            "job_id": job.id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error uploading job description: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload job description")

@app.get("/api/job-descriptions")
async def get_job_descriptions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all job descriptions."""
    try:
        jobs = JobDescriptionCRUD.get_all(db, skip=skip, limit=limit)
        return jobs
    except Exception as e:
        logger.error(f"Error fetching job descriptions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch job descriptions")

@app.get("/api/job-descriptions/{job_id}")
async def get_job_description(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job description."""
    try:
        job = JobDescriptionCRUD.get_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")
        return job
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job description: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch job description")

# Resume endpoints
@app.post("/api/resumes/upload")
async def upload_resume(
    file: UploadFile = File(...),
    candidate_name: str = "",
    candidate_email: str = "",
    candidate_phone: str = "",
    uploaded_by: str = "",
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Upload and process a resume."""
    try:
        # Validate file
        validate_file(file)
        
        # Save file
        folder = os.path.join(settings.upload_dir, "resumes")
        file_path = save_uploaded_file(file, folder)
        
        # Extract text
        extracted_text = document_parser.extract_text(file_path)
        if not extracted_text:
            raise HTTPException(status_code=400, detail="Could not extract text from file")
        
        # Create resume record
        resume_data = {
            "candidate_name": candidate_name or "Unknown",
            "candidate_email": candidate_email,
            "candidate_phone": candidate_phone,
            "original_filename": file.filename,
            "file_path": file_path,
            "extracted_text": extracted_text,
            "uploaded_by": uploaded_by
        }
        
        resume = ResumeCRUD.create(db, resume_data)
        
        # Process in background
        background_tasks.add_task(process_resume, resume.id, extracted_text)
        
        # Log activity
        SystemLogCRUD.create_log(db, {
            "action": "resume_uploaded",
            "resource_type": "resume",
            "resource_id": resume.id,
            "details": {"filename": file.filename, "candidate_name": candidate_name}
        })
        
        return {
            "message": "Resume uploaded successfully",
            "resume_id": resume.id,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"Error uploading resume: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload resume")

@app.get("/api/resumes")
async def get_resumes(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all resumes with optional search."""
    try:
        if search:
            resumes = ResumeCRUD.search_resumes(db, search)
        else:
            resumes = ResumeCRUD.get_all(db, skip=skip, limit=limit)
        return resumes
    except Exception as e:
        logger.error(f"Error fetching resumes: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch resumes")

@app.get("/api/resumes/{resume_id}")
async def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get a specific resume."""
    try:
        resume = ResumeCRUD.get_by_id(db, resume_id)
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        return resume
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resume: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch resume")

# Evaluation endpoints
@app.post("/api/evaluations/evaluate")
async def evaluate_resume_against_job(
    request: EvaluationRequest,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Evaluate a specific resume against a specific job description."""
    try:
        # Get job and resume
        job = JobDescriptionCRUD.get_by_id(db, request.job_id)
        resume = ResumeCRUD.get_by_id(db, request.resume_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Check if evaluation already exists
        existing_evaluation = EvaluationCRUD.get_by_job_and_resume(db, request.job_id, request.resume_id)
        if existing_evaluation:
            return {
                "message": "Evaluation already exists",
                "evaluation_id": existing_evaluation.id,
                "evaluation": existing_evaluation
            }
        
        # Start evaluation in background
        background_tasks.add_task(perform_evaluation, request.job_id, request.resume_id, job.extracted_text, resume.extracted_text)
        
        return {
            "message": "Evaluation started",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start evaluation")

@app.post("/api/evaluations/batch-evaluate")
async def batch_evaluate_resumes(
    job_id: int,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """Evaluate all resumes against a specific job description."""
    try:
        # Get job
        job = JobDescriptionCRUD.get_by_id(db, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        # Get all resumes
        resumes = ResumeCRUD.get_all(db, limit=1000)  # Adjust limit as needed
        
        # Start batch evaluation in background
        background_tasks.add_task(perform_batch_evaluation, job_id, [r.id for r in resumes])
        
        return {
            "message": f"Batch evaluation started for {len(resumes)} resumes",
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting batch evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start batch evaluation")

@app.get("/api/evaluations/job/{job_id}")
async def get_evaluations_for_job(
    job_id: int,
    suitability: Optional[str] = None,
    min_score: Optional[float] = None,
    db: Session = Depends(get_db)
):
    """Get all evaluations for a specific job."""
    try:
        evaluations = EvaluationCRUD.get_evaluations_for_job(
            db, job_id, suitability=suitability, min_score=min_score
        )
        return evaluations
    except Exception as e:
        logger.error(f"Error fetching evaluations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch evaluations")

@app.get("/api/evaluations/resume/{resume_id}")
async def get_evaluations_for_resume(resume_id: int, db: Session = Depends(get_db)):
    """Get all evaluations for a specific resume."""
    try:
        evaluations = EvaluationCRUD.get_evaluations_for_resume(db, resume_id)
        return evaluations
    except Exception as e:
        logger.error(f"Error fetching evaluations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch evaluations")

@app.get("/api/evaluations/top-candidates/{job_id}")
async def get_top_candidates(
    job_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get top candidates for a job."""
    try:
        evaluations = EvaluationCRUD.get_top_candidates(db, job_id, limit=limit)
        
        # Enrich with resume data
        results = []
        for evaluation in evaluations:
            resume = ResumeCRUD.get_by_id(db, evaluation.resume_id)
            results.append({
                "evaluation": evaluation,
                "resume": resume
            })
        
        return results
    except Exception as e:
        logger.error(f"Error fetching top candidates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch top candidates")

# Background task functions
async def process_job_description(job_id: int, text: str):
    """Process job description in background."""
    try:
        from .models import get_db_session
        
        with get_db_session() as db:
            # Extract skills and keywords
            skills = matching_engine.preprocessor.extract_technical_skills(text)
            keywords = matching_engine.preprocessor.extract_keywords(text)
            certs = matching_engine.preprocessor.extract_certifications(text)
            
            # Update job description
            JobDescriptionCRUD.update(db, job_id, {
                "skills_required": skills,
                "certifications_required": certs,
                "keywords": keywords
            })
            
            # Store embedding
            embedding_service.store_job_embedding(str(job_id), text, {"job_id": job_id})
            
            logger.info(f"Processed job description {job_id}")
            
    except Exception as e:
        logger.error(f"Error processing job description {job_id}: {str(e)}")

async def process_resume(resume_id: int, text: str):
    """Process resume in background."""
    try:
        from .models import get_db_session
        
        with get_db_session() as db:
            # Extract structured information
            structured_info = document_parser.extract_structured_info(text)
            skills = matching_engine.preprocessor.extract_technical_skills(text)
            keywords = matching_engine.preprocessor.extract_keywords(text)
            certs = matching_engine.preprocessor.extract_certifications(text)
            
            # Update resume
            update_data = {
                "skills": skills,
                "certifications": certs,
                "keywords": keywords
            }
            
            # Add extracted contact info if not provided
            if structured_info['emails'] and not ResumeCRUD.get_by_id(db, resume_id).candidate_email:
                update_data["candidate_email"] = structured_info['emails'][0]
            
            ResumeCRUD.update(db, resume_id, update_data)
            
            # Store embedding
            embedding_service.store_resume_embedding(str(resume_id), text, {"resume_id": resume_id})
            
            logger.info(f"Processed resume {resume_id}")
            
    except Exception as e:
        logger.error(f"Error processing resume {resume_id}: {str(e)}")

async def perform_evaluation(job_id: int, resume_id: int, job_text: str, resume_text: str):
    """Perform evaluation in background."""
    try:
        from .models import get_db_session
        
        # Calculate scores
        results = matching_engine.calculate_combined_score(resume_text, job_text)
        
        # Prepare evaluation data
        evaluation_data = {
            "job_description_id": job_id,
            "resume_id": resume_id,
            "hard_match_score": results['hard_match_results']['hard_match_score'],
            "semantic_match_score": results['semantic_match_results']['semantic_match_score'],
            "combined_score": results['combined_score'],
            "score_percentage": results['score_percentage'],
            "suitability": results['suitability'],
            "skill_matches": results['hard_match_results'].get('skill_matches', []),
            "keyword_matches": results['hard_match_results'].get('keyword_matches', []),
            "certification_matches": results['hard_match_results'].get('cert_matches', []),
            "fuzzy_skill_matches": results['hard_match_results'].get('fuzzy_skill_matches', {}),
            "missing_skills": results['feedback'].get('missing_skills', []),
            "missing_certifications": results['feedback'].get('missing_certifications', []),
            "improvement_suggestions": results['feedback'].get('improvement_suggestions', []),
            "evaluation_metadata": {
                "hard_match_weight": settings.hard_match_weight,
                "semantic_match_weight": settings.semantic_match_weight,
                "model_used": settings.embedding_model
            }
        }
        
        # Save evaluation
        with get_db_session() as db:
            evaluation = EvaluationCRUD.create(db, evaluation_data)
            
            # Log activity
            SystemLogCRUD.create_log(db, {
                "action": "evaluation_completed",
                "resource_type": "evaluation",
                "resource_id": evaluation.id,
                "details": {
                    "job_id": job_id,
                    "resume_id": resume_id,
                    "score": results['score_percentage'],
                    "suitability": results['suitability']
                }
            })
        
        logger.info(f"Completed evaluation for job {job_id} and resume {resume_id}")
        
    except Exception as e:
        logger.error(f"Error performing evaluation: {str(e)}")

async def perform_batch_evaluation(job_id: int, resume_ids: List[int]):
    """Perform batch evaluation in background."""
    try:
        from .models import get_db_session
        
        with get_db_session() as db:
            job = JobDescriptionCRUD.get_by_id(db, job_id)
            if not job:
                return
            
            for resume_id in resume_ids:
                try:
                    # Check if evaluation already exists
                    existing = EvaluationCRUD.get_by_job_and_resume(db, job_id, resume_id)
                    if existing:
                        continue
                    
                    resume = ResumeCRUD.get_by_id(db, resume_id)
                    if not resume:
                        continue
                    
                    await perform_evaluation(job_id, resume_id, job.extracted_text, resume.extracted_text)
                    
                except Exception as e:
                    logger.error(f"Error evaluating resume {resume_id}: {str(e)}")
                    continue
        
        logger.info(f"Completed batch evaluation for job {job_id}")
        
    except Exception as e:
        logger.error(f"Error performing batch evaluation: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
