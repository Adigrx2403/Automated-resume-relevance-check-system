import re
import string
from typing import List, Dict, Set
import spacy
from fuzzywuzzy import fuzz, process
import textdistance
import logging

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Text preprocessing utilities for resume and job description analysis."""
    
    def __init__(self):
        """Initialize the preprocessor with spaCy model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")
            self.nlp = None
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess text for analysis.
        
        Args:
            text: Raw text
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '', text)
        
        # Remove phone numbers
        text = re.sub(r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text.strip()
    
    def extract_keywords(self, text: str, min_length: int = 2) -> List[str]:
        """
        Extract keywords from text using various techniques.
        
        Args:
            text: Input text
            min_length: Minimum length of keywords
            
        Returns:
            List of extracted keywords
        """
        keywords = set()
        
        if not text:
            return list(keywords)
        
        # Preprocess text
        clean_text = self.preprocess_text(text)
        
        # Extract using spaCy if available
        if self.nlp:
            doc = self.nlp(clean_text)
            
            # Extract named entities
            for ent in doc.ents:
                if len(ent.text) >= min_length:
                    keywords.add(ent.text.lower())
            
            # Extract noun chunks
            for chunk in doc.noun_chunks:
                if len(chunk.text) >= min_length:
                    keywords.add(chunk.text.lower())
            
            # Extract tokens that are not stop words
            for token in doc:
                if (not token.is_stop and 
                    not token.is_punct and 
                    len(token.text) >= min_length):
                    keywords.add(token.lemma_.lower())
        
        # Fallback: simple word extraction
        words = clean_text.split()
        for word in words:
            if len(word) >= min_length:
                keywords.add(word)
        
        return list(keywords)
    
    def extract_technical_skills(self, text: str) -> List[str]:
        """
        Extract technical skills from text using predefined skill lists.
        
        Args:
            text: Input text
            
        Returns:
            List of technical skills found
        """
        # Common technical skills (this can be expanded)
        technical_skills = {
            'programming_languages': [
                'python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
                'typescript', 'kotlin', 'swift', 'scala', 'r', 'matlab', 'perl'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express',
                'laravel', 'rails', 'fastapi', 'node.js', 'asp.net'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'sqlite', 'redis', 'elasticsearch',
                'oracle', 'sql server', 'cassandra', 'firebase'
            ],
            'cloud_platforms': [
                'aws', 'azure', 'gcp', 'google cloud', 'heroku', 'digitalocean',
                'docker', 'kubernetes', 'terraform'
            ],
            'tools': [
                'git', 'jenkins', 'jira', 'confluence', 'postman', 'figma',
                'photoshop', 'illustrator', 'tableau', 'power bi'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch',
                'scikit-learn', 'pandas', 'numpy', 'matplotlib', 'seaborn',
                'jupyter', 'data analysis', 'statistics'
            ]
        }
        
        found_skills = []
        text_lower = text.lower()
        
        for category, skills in technical_skills.items():
            for skill in skills:
                if skill in text_lower:
                    found_skills.append(skill)
        
        return list(set(found_skills))
    
    def extract_certifications(self, text: str) -> List[str]:
        """
        Extract certifications from text.
        
        Args:
            text: Input text
            
        Returns:
            List of certifications found
        """
        certifications = [
            'aws certified', 'azure certified', 'google cloud certified',
            'pmp', 'cissp', 'ceh', 'ccna', 'ccnp', 'ccie',
            'oracle certified', 'microsoft certified', 'comptia',
            'scrum master', 'product owner', 'six sigma'
        ]
        
        found_certs = []
        text_lower = text.lower()
        
        for cert in certifications:
            if cert in text_lower:
                found_certs.append(cert)
        
        return found_certs
    
    def fuzzy_match_skills(self, resume_skills: List[str], job_skills: List[str], 
                          threshold: int = 80) -> Dict[str, float]:
        """
        Perform fuzzy matching between resume and job skills.
        
        Args:
            resume_skills: Skills from resume
            job_skills: Skills from job description
            threshold: Similarity threshold
            
        Returns:
            Dictionary of matched skills with similarity scores
        """
        matches = {}
        
        for job_skill in job_skills:
            best_match = process.extractOne(job_skill, resume_skills, scorer=fuzz.token_sort_ratio)
            
            if best_match and best_match[1] >= threshold:
                matches[job_skill] = {
                    'matched_skill': best_match[0],
                    'similarity': best_match[1] / 100.0
                }
        
        return matches
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts using multiple algorithms.
        
        Args:
            text1: First text
            text2: Second text
            
        Returns:
            Similarity score between 0 and 1
        """
        if not text1 or not text2:
            return 0.0
        
        # Preprocess texts
        clean_text1 = self.preprocess_text(text1)
        clean_text2 = self.preprocess_text(text2)
        
        # Calculate various similarity metrics
        jaccard_sim = textdistance.jaccard(clean_text1.split(), clean_text2.split())
        cosine_sim = textdistance.cosine(clean_text1.split(), clean_text2.split())
        jaro_winkler_sim = textdistance.jaro_winkler(clean_text1, clean_text2)
        
        # Combine similarities (weighted average)
        combined_similarity = (jaccard_sim * 0.3 + cosine_sim * 0.4 + jaro_winkler_sim * 0.3)
        
        return combined_similarity
