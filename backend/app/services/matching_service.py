from typing import Dict, List, Tuple, Optional
import logging
from ..utils.text_preprocessor import TextPreprocessor
from .embedding_service import EmbeddingService
from .openai_service import OpenAIService
from .huggingface_service import HuggingFaceService
from ..config import settings

logger = logging.getLogger(__name__)

class MatchingEngine:
    """Engine for matching resumes with job descriptions using hard and semantic matching."""
    
    def __init__(self):
        """Initialize the matching engine."""
        self.preprocessor = TextPreprocessor()
        self.embedding_service = EmbeddingService()
        self.openai_service = OpenAIService()
        self.huggingface_service = HuggingFaceService()
        self.hard_match_weight = settings.hard_match_weight
        self.semantic_match_weight = settings.semantic_match_weight
    
    def calculate_hard_match_score(self, resume_text: str, job_text: str) -> Dict:
        """
        Calculate hard matching score using keyword and fuzzy matching.
        
        Args:
            resume_text: Resume text
            job_text: Job description text
            
        Returns:
            Dictionary containing hard match results
        """
        try:
            # Extract skills and keywords
            resume_skills = self.preprocessor.extract_technical_skills(resume_text)
            job_skills = self.preprocessor.extract_technical_skills(job_text)
            
            resume_keywords = self.preprocessor.extract_keywords(resume_text)
            job_keywords = self.preprocessor.extract_keywords(job_text)
            
            resume_certs = self.preprocessor.extract_certifications(resume_text)
            job_certs = self.preprocessor.extract_certifications(job_text)
            
            # Calculate exact matches
            skill_matches = set(resume_skills) & set(job_skills)
            keyword_matches = set(resume_keywords) & set(job_keywords)
            cert_matches = set(resume_certs) & set(job_certs)
            
            # Calculate fuzzy matches for skills
            fuzzy_skill_matches = self.preprocessor.fuzzy_match_skills(
                resume_skills, job_skills, threshold=75
            )
            
            # Calculate scores
            skill_score = 0
            if job_skills:
                exact_skill_score = len(skill_matches) / len(job_skills)
                fuzzy_skill_score = sum(match['similarity'] for match in fuzzy_skill_matches.values()) / len(job_skills)
                skill_score = max(exact_skill_score, fuzzy_skill_score * 0.8)  # Fuzzy gets 80% weight
            
            keyword_score = 0
            if job_keywords:
                keyword_score = len(keyword_matches) / len(job_keywords)
            
            cert_score = 0
            if job_certs:
                cert_score = len(cert_matches) / len(job_certs)
            
            # Weighted combination
            hard_match_score = (
                skill_score * 0.6 +       # Skills are most important
                keyword_score * 0.3 +     # Keywords are moderately important
                cert_score * 0.1          # Certifications are least important
            )
            
            return {
                'hard_match_score': min(1.0, hard_match_score),
                'skill_matches': list(skill_matches),
                'keyword_matches': list(keyword_matches),
                'cert_matches': list(cert_matches),
                'fuzzy_skill_matches': fuzzy_skill_matches,
                'missing_skills': list(set(job_skills) - set(resume_skills)),
                'missing_certs': list(set(job_certs) - set(resume_certs)),
                'skill_score': skill_score,
                'keyword_score': keyword_score,
                'cert_score': cert_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating hard match score: {str(e)}")
            return {
                'hard_match_score': 0.0,
                'skill_matches': [],
                'keyword_matches': [],
                'cert_matches': [],
                'fuzzy_skill_matches': {},
                'missing_skills': [],
                'missing_certs': [],
                'skill_score': 0.0,
                'keyword_score': 0.0,
                'cert_score': 0.0
            }
    
    def calculate_semantic_match_score(self, resume_text: str, job_text: str) -> Dict:
        """
        Calculate semantic matching score using embeddings.
        
        Args:
            resume_text: Resume text
            job_text: Job description text
            
        Returns:
            Dictionary containing semantic match results
        """
        try:
            # Calculate overall semantic similarity
            overall_similarity = self.embedding_service.calculate_semantic_similarity(
                resume_text, job_text
            )
            
            # Extract structured information for section-wise comparison
            resume_info = self.preprocessor.nlp(resume_text) if self.preprocessor.nlp else None
            job_info = self.preprocessor.nlp(job_text) if self.preprocessor.nlp else None
            
            section_similarities = {}
            
            # If spaCy is available, calculate section-wise similarities
            if resume_info and job_info:
                # Extract sentences for more granular comparison
                resume_sentences = [sent.text for sent in resume_info.sents]
                job_sentences = [sent.text for sent in job_info.sents]
                
                # Find best matching sentences
                best_matches = []
                for job_sent in job_sentences[:5]:  # Top 5 job sentences
                    best_sim = 0
                    best_resume_sent = ""
                    for resume_sent in resume_sentences:
                        sim = self.embedding_service.calculate_semantic_similarity(
                            job_sent, resume_sent
                        )
                        if sim > best_sim:
                            best_sim = sim
                            best_resume_sent = resume_sent
                    
                    if best_sim > 0.3:  # Threshold for meaningful similarity
                        best_matches.append({
                            'job_sentence': job_sent,
                            'resume_sentence': best_resume_sent,
                            'similarity': best_sim
                        })
                
                section_similarities['sentence_matches'] = best_matches
            
            return {
                'semantic_match_score': overall_similarity,
                'section_similarities': section_similarities,
                'contextual_relevance': overall_similarity
            }
            
        except Exception as e:
            logger.error(f"Error calculating semantic match score: {str(e)}")
            return {
                'semantic_match_score': 0.0,
                'section_similarities': {},
                'contextual_relevance': 0.0
            }
    
    def calculate_combined_score(self, resume_text: str, job_text: str) -> Dict:
        """
        Calculate combined relevance score using both hard and semantic matching.
        
        Args:
            resume_text: Resume text
            job_text: Job description text
            
        Returns:
            Dictionary containing all matching results and final score
        """
        try:
            # Calculate individual scores
            hard_match_results = self.calculate_hard_match_score(resume_text, job_text)
            semantic_match_results = self.calculate_semantic_match_score(resume_text, job_text)
            
            # Calculate combined score
            combined_score = (
                hard_match_results['hard_match_score'] * self.hard_match_weight +
                semantic_match_results['semantic_match_score'] * self.semantic_match_weight
            )
            
            # Determine suitability classification
            if combined_score >= 0.7:
                suitability = "High"
            elif combined_score >= 0.4:
                suitability = "Medium"
            else:
                suitability = "Low"
            
            # Generate feedback and improvement suggestions
            feedback = self._generate_feedback(hard_match_results, semantic_match_results, resume_text, job_text)
            
            # Get AI-powered insights if available
            ai_insights = self._get_ai_insights(resume_text, job_text)
            
            return {
                'combined_score': combined_score,
                'score_percentage': round(combined_score * 100, 2),
                'suitability': suitability,
                'hard_match_results': hard_match_results,
                'semantic_match_results': semantic_match_results,
                'feedback': feedback,
                'ai_insights': ai_insights
            }
            
        except Exception as e:
            logger.error(f"Error calculating combined score: {str(e)}")
            return {
                'combined_score': 0.0,
                'score_percentage': 0.0,
                'suitability': "Low",
                'hard_match_results': {},
                'semantic_match_results': {},
                'feedback': {
                    'missing_skills': [],
                    'missing_certifications': [],
                    'improvement_suggestions': ["Error occurred during analysis"]
                },
                'ai_insights': {}
            }
    
    def _generate_feedback(self, hard_match_results: Dict, semantic_match_results: Dict, 
                          resume_text: str, job_text: str) -> Dict:
        """
        Generate feedback and improvement suggestions.
        
        Args:
            hard_match_results: Results from hard matching
            semantic_match_results: Results from semantic matching
            resume_text: Resume content
            job_text: Job description content
            
        Returns:
            Dictionary containing feedback
        """
        feedback = {
            'missing_skills': hard_match_results.get('missing_skills', []),
            'missing_certifications': hard_match_results.get('missing_certs', []),
            'improvement_suggestions': []
        }
        
        # Generate improvement suggestions based on missing elements
        if feedback['missing_skills']:
            feedback['improvement_suggestions'].append(
                f"Consider adding these technical skills to your resume: {', '.join(feedback['missing_skills'][:5])}"
            )
        
        if feedback['missing_certifications']:
            feedback['improvement_suggestions'].append(
                f"Consider obtaining these certifications: {', '.join(feedback['missing_certifications'])}"
            )
        
        # Suggestions based on semantic match score
        semantic_score = semantic_match_results.get('semantic_match_score', 0)
        if semantic_score < 0.5:
            feedback['improvement_suggestions'].append(
                "Consider rephrasing your experience descriptions to better align with the job requirements"
            )
            feedback['improvement_suggestions'].append(
                "Add more specific examples and quantifiable achievements related to the job"
            )
        
        # Suggestions based on hard match score
        hard_score = hard_match_results.get('hard_match_score', 0)
        if hard_score < 0.4:
            feedback['improvement_suggestions'].append(
                "Focus on acquiring the key technical skills mentioned in the job description"
            )
            feedback['improvement_suggestions'].append(
                "Include relevant projects that demonstrate your skills in the required technologies"
            )
        
        # Get AI-powered suggestions if available
        if self.openai_service.is_available():
            try:
                ai_suggestions = self.openai_service.generate_improvement_suggestions(
                    resume_text, job_text, feedback['missing_skills']
                )
                feedback['ai_improvement_suggestions'] = ai_suggestions
            except Exception as e:
                logger.error(f"Error getting AI suggestions: {str(e)}")
                feedback['ai_improvement_suggestions'] = []
        
        return feedback
    
    def _get_ai_insights(self, resume_text: str, job_text: str) -> Dict:
        """
        Get AI-powered insights about the match.
        
        Args:
            resume_text: Resume content
            job_text: Job description content
            
        Returns:
            Dictionary with AI insights
        """
        insights = {}
        
        # OpenAI analysis
        if self.openai_service.is_available():
            try:
                openai_analysis = self.openai_service.analyze_resume_job_match(resume_text, job_text)
                insights['openai_analysis'] = openai_analysis
            except Exception as e:
                logger.error(f"Error getting OpenAI analysis: {str(e)}")
                insights['openai_analysis'] = {"error": str(e)}
        
        # HuggingFace analysis
        if self.huggingface_service.is_available():
            try:
                hf_analysis = self.huggingface_service.analyze_job_resume_compatibility(resume_text, job_text)
                insights['huggingface_analysis'] = hf_analysis
            except Exception as e:
                logger.error(f"Error getting HuggingFace analysis: {str(e)}")
                insights['huggingface_analysis'] = {"error": str(e)}
        
        return insights
    
    def batch_process_resumes(self, job_text: str, resume_data: List[Dict]) -> List[Dict]:
        """
        Process multiple resumes against a single job description.
        
        Args:
            job_text: Job description text
            resume_data: List of dictionaries containing resume information
            
        Returns:
            List of processed results sorted by score
        """
        results = []
        
        for resume in resume_data:
            try:
                resume_text = resume.get('text', '')
                resume_id = resume.get('id', '')
                
                # Calculate scores
                match_results = self.calculate_combined_score(resume_text, job_text)
                
                # Add resume metadata
                match_results.update({
                    'resume_id': resume_id,
                    'resume_metadata': resume.get('metadata', {})
                })
                
                results.append(match_results)
                
            except Exception as e:
                logger.error(f"Error processing resume {resume.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Sort by combined score (descending)
        results.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return results
