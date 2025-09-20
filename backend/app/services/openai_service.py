import logging
from typing import List, Dict, Optional
import openai
from langchain_openai import OpenAI, ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_core.messages import HumanMessage, SystemMessage
import tiktoken
from ..config import settings

logger = logging.getLogger(__name__)

class OpenAIService:
    """Service for OpenAI API integration."""
    
    def __init__(self):
        """Initialize OpenAI service."""
        if not settings.openai_api_key:
            logger.warning("OpenAI API key not provided")
            self.client = None
            self.chat_model = None
        else:
            openai.api_key = settings.openai_api_key
            self.client = openai
            self.chat_model = ChatOpenAI(
                model=settings.llm_model,
                temperature=settings.temperature,
                openai_api_key=settings.openai_api_key
            )
    
    def is_available(self) -> bool:
        """Check if OpenAI service is available."""
        return self.client is not None and settings.openai_api_key
    
    def analyze_resume_job_match(self, resume_text: str, job_text: str) -> Dict:
        """
        Use OpenAI to analyze resume-job match with detailed insights.
        
        Args:
            resume_text: Resume content
            job_text: Job description content
            
        Returns:
            Dictionary with analysis results
        """
        if not self.is_available():
            logger.warning("OpenAI service not available")
            return {"error": "OpenAI service not configured"}
        
        try:
            # Create prompt for analysis
            prompt = self._create_analysis_prompt(resume_text, job_text)
            
            # Get response from OpenAI
            messages = [
                SystemMessage(content="You are an expert HR analyst specializing in resume-job matching. "
                                    "Provide detailed, actionable insights about candidate suitability."),
                HumanMessage(content=prompt)
            ]
            
            response = self.chat_model(messages)
            
            # Parse response
            analysis = self._parse_analysis_response(response.content)
            return analysis
            
        except Exception as e:
            logger.error(f"Error in OpenAI analysis: {str(e)}")
            return {"error": f"Analysis failed: {str(e)}"}
    
    def generate_improvement_suggestions(self, resume_text: str, job_text: str, 
                                       missing_skills: List[str]) -> List[str]:
        """
        Generate personalized improvement suggestions.
        
        Args:
            resume_text: Resume content
            job_text: Job description content
            missing_skills: List of missing skills
            
        Returns:
            List of improvement suggestions
        """
        if not self.is_available():
            return ["OpenAI service not available for personalized suggestions"]
        
        try:
            prompt = f"""
            Based on the following resume and job description, provide 5 specific, actionable suggestions 
            for the candidate to improve their resume to better match the job requirements.
            
            Missing Skills: {', '.join(missing_skills)}
            
            Job Description:
            {job_text[:1000]}...
            
            Resume:
            {resume_text[:1000]}...
            
            Provide suggestions in the following format:
            1. [Specific suggestion]
            2. [Specific suggestion]
            ...
            
            Focus on:
            - Adding missing technical skills
            - Improving experience descriptions
            - Adding relevant projects or achievements
            - Formatting and presentation improvements
            - Industry-specific keywords
            """
            
            messages = [
                SystemMessage(content="You are a professional resume coach. Provide specific, "
                                    "actionable advice to help candidates improve their resumes."),
                HumanMessage(content=prompt)
            ]
            
            response = self.chat_model(messages)
            
            # Parse suggestions
            suggestions = []
            lines = response.content.split('\n')
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Clean up the suggestion
                    suggestion = line.split('.', 1)[-1].strip() if '.' in line else line
                    suggestion = suggestion.lstrip('- •').strip()
                    if suggestion:
                        suggestions.append(suggestion)
            
            return suggestions[:5]  # Return top 5 suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            return [f"Error generating suggestions: {str(e)}"]
    
    def extract_key_requirements(self, job_text: str) -> Dict:
        """
        Extract key requirements from job description using OpenAI.
        
        Args:
            job_text: Job description text
            
        Returns:
            Dictionary with extracted requirements
        """
        if not self.is_available():
            return {"error": "OpenAI service not available"}
        
        try:
            prompt = f"""
            Analyze the following job description and extract key requirements in a structured format:
            
            {job_text}
            
            Extract and categorize:
            1. Required technical skills (programming languages, frameworks, tools)
            2. Required soft skills
            3. Educational requirements
            4. Experience requirements (years, specific domains)
            5. Certifications mentioned
            6. Key responsibilities
            
            Format the response as JSON with these categories.
            """
            
            messages = [
                SystemMessage(content="You are an expert at analyzing job descriptions. "
                                    "Extract information in a structured, JSON format."),
                HumanMessage(content=prompt)
            ]
            
            response = self.chat_model(messages)
            
            # Try to parse as JSON, fallback to text parsing
            try:
                import json
                return json.loads(response.content)
            except:
                return {"raw_analysis": response.content}
                
        except Exception as e:
            logger.error(f"Error extracting requirements: {str(e)}")
            return {"error": f"Extraction failed: {str(e)}"}
    
    def _create_analysis_prompt(self, resume_text: str, job_text: str) -> str:
        """Create prompt for resume-job analysis."""
        # Truncate texts to fit within token limits
        max_resume_chars = 2000
        max_job_chars = 1500
        
        truncated_resume = resume_text[:max_resume_chars] + "..." if len(resume_text) > max_resume_chars else resume_text
        truncated_job = job_text[:max_job_chars] + "..." if len(job_text) > max_job_chars else job_text
        
        prompt = f"""
        Analyze the compatibility between this resume and job description. Provide a detailed assessment.
        
        JOB DESCRIPTION:
        {truncated_job}
        
        RESUME:
        {truncated_resume}
        
        Please analyze and provide:
        1. Overall compatibility score (0-100)
        2. Key strengths of the candidate for this role
        3. Major gaps or weaknesses
        4. Specific skills that match well
        5. Missing critical skills
        6. Recommendations for the candidate
        7. Recommendations for the hiring team
        
        Be specific and provide actionable insights.
        """
        
        return prompt
    
    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse OpenAI analysis response into structured format."""
        analysis = {
            "ai_compatibility_score": 0,
            "strengths": [],
            "weaknesses": [],
            "matching_skills": [],
            "missing_skills": [],
            "candidate_recommendations": [],
            "hiring_recommendations": [],
            "raw_analysis": response_text
        }
        
        try:
            # Simple parsing logic (can be improved with more sophisticated NLP)
            lines = response_text.split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Detect sections
                if "score" in line.lower() and any(char.isdigit() for char in line):
                    # Extract score
                    import re
                    score_match = re.search(r'(\d+)', line)
                    if score_match:
                        analysis["ai_compatibility_score"] = int(score_match.group(1))
                
                elif "strength" in line.lower():
                    current_section = "strengths"
                elif "weakness" in line.lower() or "gap" in line.lower():
                    current_section = "weaknesses"
                elif "match" in line.lower() and "skill" in line.lower():
                    current_section = "matching_skills"
                elif "missing" in line.lower():
                    current_section = "missing_skills"
                elif "recommendation" in line.lower() and "candidate" in line.lower():
                    current_section = "candidate_recommendations"
                elif "recommendation" in line.lower() and "hiring" in line.lower():
                    current_section = "hiring_recommendations"
                
                # Add content to current section
                elif current_section and (line.startswith('-') or line.startswith('•') or line[0].isdigit()):
                    content = line.lstrip('- •0123456789.').strip()
                    if content:
                        analysis[current_section].append(content)
            
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
        
        return analysis
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text for the configured model."""
        try:
            encoding = tiktoken.encoding_for_model(settings.llm_model)
            return len(encoding.encode(text))
        except:
            # Fallback: approximate token count
            return len(text.split()) * 1.3
