import logging
from typing import List, Dict, Optional
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from huggingface_hub import login
from ..config import settings

logger = logging.getLogger(__name__)

class HuggingFaceService:
    """Service for HuggingFace model integration."""
    
    def __init__(self):
        """Initialize HuggingFace service."""
        self.token = settings.huggingface_api_token
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Initialize models
        self.summarizer = None
        self.classifier = None
        self.question_answerer = None
        
        if self.token:
            try:
                login(self.token)
                self._initialize_models()
            except Exception as e:
                logger.warning(f"Failed to login to HuggingFace: {str(e)}")
        else:
            logger.warning("HuggingFace API token not provided")
    
    def _initialize_models(self):
        """Initialize HuggingFace models."""
        try:
            # Text summarization model
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn",
                device=self.device
            )
            
            # Text classification model for skill extraction
            self.classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli",
                device=self.device
            )
            
            # Question answering model for information extraction
            self.question_answerer = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad",
                device=self.device
            )
            
            logger.info("HuggingFace models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing HuggingFace models: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if HuggingFace service is available."""
        return self.summarizer is not None
    
    def summarize_text(self, text: str, max_length: int = 150) -> str:
        """
        Summarize text using HuggingFace model.
        
        Args:
            text: Input text to summarize
            max_length: Maximum length of summary
            
        Returns:
            Summarized text
        """
        if not self.is_available():
            return "HuggingFace service not available"
        
        try:
            # Truncate text if too long
            max_input_length = 1024
            if len(text) > max_input_length:
                text = text[:max_input_length]
            
            result = self.summarizer(
                text,
                max_length=max_length,
                min_length=30,
                do_sample=False
            )
            
            return result[0]['summary_text']
            
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return f"Summarization failed: {str(e)}"
    
    def extract_skills_from_text(self, text: str, candidate_skills: List[str]) -> Dict:
        """
        Extract and classify skills from text using zero-shot classification.
        
        Args:
            text: Input text
            candidate_skills: List of potential skills to look for
            
        Returns:
            Dictionary with classified skills and confidence scores
        """
        if not self.is_available():
            return {"error": "HuggingFace service not available"}
        
        try:
            # Limit candidate skills to avoid API limits
            skills_subset = candidate_skills[:20] if len(candidate_skills) > 20 else candidate_skills
            
            if not skills_subset:
                return {"skills": [], "scores": []}
            
            result = self.classifier(text, skills_subset)
            
            # Filter skills with confidence > 0.3
            filtered_skills = []
            filtered_scores = []
            
            for label, score in zip(result['labels'], result['scores']):
                if score > 0.3:
                    filtered_skills.append(label)
                    filtered_scores.append(score)
            
            return {
                "skills": filtered_skills,
                "scores": filtered_scores,
                "all_results": result
            }
            
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            return {"error": f"Skill extraction failed: {str(e)}"}
    
    def answer_questions_about_candidate(self, resume_text: str, questions: List[str]) -> Dict:
        """
        Answer specific questions about a candidate using their resume.
        
        Args:
            resume_text: Resume content
            questions: List of questions to answer
            
        Returns:
            Dictionary with questions and answers
        """
        if not self.is_available():
            return {"error": "HuggingFace service not available"}
        
        try:
            answers = {}
            
            for question in questions:
                try:
                    result = self.question_answerer(
                        question=question,
                        context=resume_text
                    )
                    
                    # Only include confident answers
                    if result['score'] > 0.1:
                        answers[question] = {
                            "answer": result['answer'],
                            "confidence": result['score']
                        }
                    else:
                        answers[question] = {
                            "answer": "Not found in resume",
                            "confidence": 0.0
                        }
                        
                except Exception as e:
                    answers[question] = {
                        "answer": f"Error: {str(e)}",
                        "confidence": 0.0
                    }
            
            return answers
            
        except Exception as e:
            logger.error(f"Error answering questions: {str(e)}")
            return {"error": f"Question answering failed: {str(e)}"}
    
    def analyze_job_resume_compatibility(self, resume_text: str, job_text: str) -> Dict:
        """
        Analyze compatibility between resume and job description using HuggingFace models.
        
        Args:
            resume_text: Resume content
            job_text: Job description content
            
        Returns:
            Dictionary with compatibility analysis
        """
        if not self.is_available():
            return {"error": "HuggingFace service not available"}
        
        try:
            analysis = {}
            
            # Summarize both texts
            analysis['resume_summary'] = self.summarize_text(resume_text, max_length=100)
            analysis['job_summary'] = self.summarize_text(job_text, max_length=100)
            
            # Extract key information using question answering
            resume_questions = [
                "What programming languages does the candidate know?",
                "How many years of experience does the candidate have?",
                "What is the candidate's highest education level?",
                "What companies has the candidate worked for?",
                "What projects has the candidate worked on?"
            ]
            
            job_questions = [
                "What programming languages are required?",
                "How many years of experience are required?",
                "What education level is required?",
                "What are the main responsibilities?",
                "What skills are required?"
            ]
            
            analysis['resume_info'] = self.answer_questions_about_candidate(resume_text, resume_questions)
            analysis['job_requirements'] = self.answer_questions_about_candidate(job_text, job_questions)
            
            # Skill compatibility analysis
            common_skills = [
                "Python", "Java", "JavaScript", "C++", "React", "Node.js", "Django", 
                "Flask", "SQL", "MongoDB", "AWS", "Docker", "Kubernetes", "Git",
                "Machine Learning", "Data Analysis", "Project Management"
            ]
            
            resume_skills = self.extract_skills_from_text(resume_text, common_skills)
            job_skills = self.extract_skills_from_text(job_text, common_skills)
            
            analysis['resume_skills'] = resume_skills
            analysis['job_skills'] = job_skills
            
            # Calculate skill overlap
            if (resume_skills.get('skills') and job_skills.get('skills')):
                matching_skills = set(resume_skills['skills']) & set(job_skills['skills'])
                analysis['skill_overlap'] = {
                    'matching_skills': list(matching_skills),
                    'overlap_percentage': len(matching_skills) / len(job_skills['skills']) * 100 if job_skills['skills'] else 0
                }
            else:
                analysis['skill_overlap'] = {'matching_skills': [], 'overlap_percentage': 0}
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in compatibility analysis: {str(e)}")
            return {"error": f"Compatibility analysis failed: {str(e)}"}
    
    def generate_candidate_insights(self, resume_text: str) -> Dict:
        """
        Generate insights about a candidate using HuggingFace models.
        
        Args:
            resume_text: Resume content
            
        Returns:
            Dictionary with candidate insights
        """
        if not self.is_available():
            return {"error": "HuggingFace service not available"}
        
        try:
            insights = {}
            
            # Summarize resume
            insights['summary'] = self.summarize_text(resume_text)
            
            # Extract key career information
            career_questions = [
                "What is the candidate's current job title?",
                "What industry does the candidate work in?",
                "What are the candidate's main achievements?",
                "What certifications does the candidate have?",
                "What technologies is the candidate experienced with?"
            ]
            
            insights['career_info'] = self.answer_questions_about_candidate(resume_text, career_questions)
            
            # Analyze career level using classification
            career_levels = ["Entry Level", "Mid Level", "Senior Level", "Executive Level"]
            career_level_analysis = self.classifier(resume_text, career_levels)
            
            insights['career_level'] = {
                'predicted_level': career_level_analysis['labels'][0],
                'confidence': career_level_analysis['scores'][0]
            }
            
            # Analyze domain expertise
            domains = [
                "Software Development", "Data Science", "Machine Learning", "Web Development",
                "Mobile Development", "DevOps", "Cybersecurity", "Product Management",
                "Project Management", "Business Analysis", "Quality Assurance"
            ]
            
            domain_analysis = self.classifier(resume_text, domains)
            insights['domain_expertise'] = {
                'primary_domain': domain_analysis['labels'][0],
                'confidence': domain_analysis['scores'][0],
                'all_domains': list(zip(domain_analysis['labels'][:3], domain_analysis['scores'][:3]))
            }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating insights: {str(e)}")
            return {"error": f"Insight generation failed: {str(e)}"}
    
    def enhance_job_description_analysis(self, job_text: str) -> Dict:
        """
        Enhance job description analysis using HuggingFace models.
        
        Args:
            job_text: Job description content
            
        Returns:
            Dictionary with enhanced analysis
        """
        if not self.is_available():
            return {"error": "HuggingFace service not available"}
        
        try:
            analysis = {}
            
            # Summarize job description
            analysis['summary'] = self.summarize_text(job_text)
            
            # Extract job details
            job_questions = [
                "What is the job title?",
                "What company is hiring?",
                "What is the salary range?",
                "What are the main responsibilities?",
                "What qualifications are required?",
                "What benefits are offered?"
            ]
            
            analysis['job_details'] = self.answer_questions_about_candidate(job_text, job_questions)
            
            # Classify job level
            job_levels = ["Entry Level", "Mid Level", "Senior Level", "Executive Level"]
            level_analysis = self.classifier(job_text, job_levels)
            
            analysis['job_level'] = {
                'predicted_level': level_analysis['labels'][0],
                'confidence': level_analysis['scores'][0]
            }
            
            # Classify job type
            job_types = ["Full-time", "Part-time", "Contract", "Freelance", "Internship"]
            type_analysis = self.classifier(job_text, job_types)
            
            analysis['job_type'] = {
                'predicted_type': type_analysis['labels'][0],
                'confidence': type_analysis['scores'][0]
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in job analysis: {str(e)}")
            return {"error": f"Job analysis failed: {str(e)}"}
