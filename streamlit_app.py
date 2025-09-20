import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import io
import base64
from datetime import datetime
import os
import tempfile

# Configure page
st.set_page_config(
    page_title="Resume Relevance Check System",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .upload-area {
        border: 2px dashed #cccccc;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Mock data and functions for standalone demo
class MockAPI:
    def __init__(self):
        self.jobs = []
        self.resumes = []
        self.evaluations = []
        
    def add_job(self, job_data):
        job_id = len(self.jobs) + 1
        job_data['id'] = job_id
        job_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.jobs.append(job_data)
        return {"message": "Job description uploaded successfully", "job_id": job_id}
    
    def add_resume(self, resume_data):
        resume_id = len(self.resumes) + 1
        resume_data['id'] = resume_id
        resume_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.resumes.append(resume_data)
        return {"message": "Resume uploaded successfully", "resume_id": resume_id}
    
    def evaluate_resume(self, job_id, resume_id):
        # Mock evaluation with realistic results
        import random
        
        combined_score = random.uniform(0.3, 0.9)
        score_percentage = round(combined_score * 100, 2)
        
        if score_percentage >= 70:
            suitability = "High"
        elif score_percentage >= 40:
            suitability = "Medium"
        else:
            suitability = "Low"
            
        skills = ["Python", "Machine Learning", "SQL", "Docker", "AWS"]
        missing_skills = ["Kubernetes", "React", "Node.js"]
        
        evaluation = {
            "id": len(self.evaluations) + 1,
            "job_description_id": job_id,
            "resume_id": resume_id,
            "combined_score": combined_score,
            "score_percentage": score_percentage,
            "suitability": suitability,
            "hard_match_score": random.uniform(0.2, 0.8),
            "semantic_match_score": random.uniform(0.4, 0.9),
            "skill_matches": random.sample(skills, 3),
            "missing_skills": random.sample(missing_skills, 2),
            "improvement_suggestions": [
                "Consider adding more cloud platform experience",
                "Include specific project examples with quantifiable results",
                "Add relevant certifications to strengthen your profile"
            ],
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        self.evaluations.append(evaluation)
        return evaluation

# Initialize mock API
if 'mock_api' not in st.session_state:
    st.session_state.mock_api = MockAPI()
    
    # Add sample data
    sample_job = {
        "title": "Senior Python Developer",
        "company": "TechCorp Inc.",
        "location": "San Francisco, CA",
        "extracted_text": "We are looking for a Senior Python Developer with experience in machine learning, web development, and cloud platforms. Required skills: Python, Django, SQL, AWS, Docker."
    }
    
    sample_resume = {
        "candidate_name": "John Smith",
        "candidate_email": "john.smith@email.com",
        "original_filename": "john_smith_resume.pdf",
        "extracted_text": "Experienced Software Developer with 5 years in Python development, web applications, and database management. Skills: Python, Flask, PostgreSQL, Git."
    }
    
    st.session_state.mock_api.add_job(sample_job)
    st.session_state.mock_api.add_resume(sample_resume)

def extract_text_from_file(uploaded_file):
    """Extract text from uploaded file (mock implementation)"""
    if uploaded_file is not None:
        # For demo purposes, return mock extracted text
        return f"Extracted text from {uploaded_file.name}. This is a demo version showing mock extracted content."
    return ""

def get_suitability_color(suitability):
    """Get color for suitability badge"""
    colors = {
        "High": "success",
        "Medium": "warning", 
        "Low": "error"
    }
    return colors.get(suitability, "info")

def display_evaluation_results(evaluation):
    """Display detailed evaluation results"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Overall Score", 
            f"{evaluation['score_percentage']:.1f}%",
            delta=f"Suitability: {evaluation['suitability']}"
        )
    
    with col2:
        st.metric(
            "Hard Match Score", 
            f"{evaluation['hard_match_score']:.2f}",
            delta="Keyword matching"
        )
    
    with col3:
        st.metric(
            "Semantic Score", 
            f"{evaluation['semantic_match_score']:.2f}",
            delta="AI analysis"
        )
    
    # Skills analysis
    st.subheader("📊 Skills Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if evaluation.get('skill_matches'):
            st.success("**✅ Matching Skills:**")
            for skill in evaluation['skill_matches']:
                st.write(f"• {skill}")
    
    with col2:
        if evaluation.get('missing_skills'):
            st.error("**❌ Missing Skills:**")
            for skill in evaluation['missing_skills']:
                st.write(f"• {skill}")
    
    # Improvement suggestions
    if evaluation.get('improvement_suggestions'):
        st.subheader("💡 Improvement Suggestions")
        for i, suggestion in enumerate(evaluation['improvement_suggestions'], 1):
            st.info(f"{i}. {suggestion}")

def main():
    # Header
    st.markdown('<h1 class="main-header">📄 Resume Relevance Check System</h1>', unsafe_allow_html=True)
    st.markdown("### AI-Powered Resume Analysis & Job Matching")
    
    # Navigation
    selected = option_menu(
        menu_title=None,
        options=["🏠 Dashboard", "📝 Upload Job", "👤 Upload Resume", "🔍 Evaluate", "📈 Analytics"],
        icons=["house", "file-text", "person", "search", "bar-chart"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "0!important", "background-color": "#fafafa"},
            "icon": {"color": "orange", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#667eea"},
        }
    )
    
    if selected == "🏠 Dashboard":
        dashboard_page()
    elif selected == "📝 Upload Job":
        upload_job_page()
    elif selected == "👤 Upload Resume":
        upload_resume_page()
    elif selected == "🔍 Evaluate":
        evaluate_page()
    elif selected == "📈 Analytics":
        analytics_page()

def dashboard_page():
    """Main dashboard page"""
    st.header("📊 Dashboard Overview")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Jobs", len(st.session_state.mock_api.jobs))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Total Resumes", len(st.session_state.mock_api.resumes))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Evaluations", len(st.session_state.mock_api.evaluations))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        avg_score = 0
        if st.session_state.mock_api.evaluations:
            avg_score = sum(e['score_percentage'] for e in st.session_state.mock_api.evaluations) / len(st.session_state.mock_api.evaluations)
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Avg Score", f"{avg_score:.1f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 Recent Job Descriptions")
        if st.session_state.mock_api.jobs:
            df_jobs = pd.DataFrame(st.session_state.mock_api.jobs)
            st.dataframe(df_jobs[['title', 'company', 'location', 'created_at']], use_container_width=True)
        else:
            st.info("No job descriptions uploaded yet.")
    
    with col2:
        st.subheader("👥 Recent Resumes")
        if st.session_state.mock_api.resumes:
            df_resumes = pd.DataFrame(st.session_state.mock_api.resumes)
            st.dataframe(df_resumes[['candidate_name', 'candidate_email', 'created_at']], use_container_width=True)
        else:
            st.info("No resumes uploaded yet.")

def upload_job_page():
    """Job description upload page"""
    st.header("📝 Upload Job Description")
    
    with st.form("job_upload_form"):
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a job description file",
            type=['pdf', 'docx', 'txt'],
            help="Upload PDF, DOCX, or TXT files"
        )
        
        # Job details
        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
            company = st.text_input("Company", placeholder="e.g., Tech Corp")
        
        with col2:
            location = st.text_input("Location", placeholder="e.g., New York, NY")
            job_type = st.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Internship"])
        
        # Text input option
        st.subheader("Or paste job description text:")
        job_text = st.text_area("Job Description", height=200, placeholder="Paste the job description here...")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("📤 Upload Job Description", type="primary")
        
        if submitted:
            if uploaded_file or job_text:
                extracted_text = job_text if job_text else extract_text_from_file(uploaded_file)
                
                job_data = {
                    "title": job_title or "Untitled Position",
                    "company": company or "Unknown Company",
                    "location": location or "Not specified",
                    "job_type": job_type,
                    "extracted_text": extracted_text,
                    "original_filename": uploaded_file.name if uploaded_file else "text_input"
                }
                
                result = st.session_state.mock_api.add_job(job_data)
                st.success(f"✅ {result['message']} (ID: {result['job_id']})")
            else:
                st.error("Please upload a file or paste job description text.")

def upload_resume_page():
    """Resume upload page"""
    st.header("👤 Upload Resume")
    
    with st.form("resume_upload_form"):
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a resume file",
            type=['pdf', 'docx'],
            help="Upload PDF or DOCX files only"
        )
        
        # Candidate details
        col1, col2 = st.columns(2)
        with col1:
            candidate_name = st.text_input("Candidate Name", placeholder="e.g., John Smith")
            candidate_email = st.text_input("Email", placeholder="e.g., john@example.com")
        
        with col2:
            candidate_phone = st.text_input("Phone", placeholder="e.g., +1-555-123-4567")
            experience_years = st.number_input("Years of Experience", min_value=0, max_value=50, value=0)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("📤 Upload Resume", type="primary")
        
        if submitted:
            if uploaded_file and candidate_name and candidate_email:
                extracted_text = extract_text_from_file(uploaded_file)
                
                resume_data = {
                    "candidate_name": candidate_name,
                    "candidate_email": candidate_email,
                    "candidate_phone": candidate_phone,
                    "experience_years": experience_years,
                    "original_filename": uploaded_file.name,
                    "extracted_text": extracted_text
                }
                
                result = st.session_state.mock_api.add_resume(resume_data)
                st.success(f"✅ {result['message']} (ID: {result['resume_id']})")
            else:
                st.error("Please upload a file and fill in the required candidate information.")

def evaluate_page():
    """Evaluation page"""
    st.header("🔍 Resume Evaluation")
    
    if not st.session_state.mock_api.jobs:
        st.warning("⚠️ Please upload at least one job description first.")
        return
    
    if not st.session_state.mock_api.resumes:
        st.warning("⚠️ Please upload at least one resume first.")
        return
    
    tab1, tab2 = st.tabs(["Single Evaluation", "Batch Evaluation"])
    
    with tab1:
        st.subheader("Evaluate Single Resume")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Job selection
            job_options = {f"{job['title']} - {job['company']}": job['id'] for job in st.session_state.mock_api.jobs}
            selected_job = st.selectbox("Select Job Description", options=list(job_options.keys()))
            
        with col2:
            # Resume selection
            resume_options = {f"{resume['candidate_name']} ({resume['original_filename']})": resume['id'] 
                            for resume in st.session_state.mock_api.resumes}
            selected_resume = st.selectbox("Select Resume", options=list(resume_options.keys()))
        
        if st.button("🚀 Start Evaluation", type="primary"):
            if selected_job and selected_resume:
                job_id = job_options[selected_job]
                resume_id = resume_options[selected_resume]
                
                with st.spinner("Analyzing resume..."):
                    evaluation = st.session_state.mock_api.evaluate_resume(job_id, resume_id)
                    
                st.success("✅ Evaluation completed!")
                
                # Display results
                st.subheader("📊 Evaluation Results")
                display_evaluation_results(evaluation)
    
    with tab2:
        st.subheader("Batch Evaluate All Resumes")
        
        # Job selection for batch evaluation
        job_options = {f"{job['title']} - {job['company']}": job['id'] for job in st.session_state.mock_api.jobs}
        selected_job_batch = st.selectbox("Select Job Description for Batch Evaluation", 
                                         options=list(job_options.keys()))
        
        st.info(f"This will evaluate all {len(st.session_state.mock_api.resumes)} resumes against the selected job description.")
        
        if st.button("🚀 Start Batch Evaluation", type="primary"):
            if selected_job_batch:
                job_id = job_options[selected_job_batch]
                
                progress_bar = st.progress(0)
                evaluations = []
                
                for i, resume in enumerate(st.session_state.mock_api.resumes):
                    evaluation = st.session_state.mock_api.evaluate_resume(job_id, resume['id'])
                    evaluations.append(evaluation)
                    progress_bar.progress((i + 1) / len(st.session_state.mock_api.resumes))
                
                st.success(f"✅ Batch evaluation completed! {len(evaluations)} resumes evaluated.")
                
                # Display summary
                df = pd.DataFrame(evaluations)
                st.subheader("📊 Batch Evaluation Summary")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Score", f"{df['score_percentage'].mean():.1f}%")
                with col2:
                    high_count = len(df[df['suitability'] == 'High'])
                    st.metric("High Suitability", f"{high_count}/{len(df)}")
                with col3:
                    st.metric("Best Score", f"{df['score_percentage'].max():.1f}%")

def analytics_page():
    """Analytics and reporting page"""
    st.header("📈 Analytics & Reports")
    
    if not st.session_state.mock_api.evaluations:
        st.info("No evaluations available yet. Please run some evaluations first.")
        return
    
    # Convert evaluations to DataFrame
    df = pd.DataFrame(st.session_state.mock_api.evaluations)
    
    # Analytics tabs
    tab1, tab2, tab3 = st.tabs(["Score Distribution", "Suitability Analysis", "Skills Analysis"])
    
    with tab1:
        st.subheader("Score Distribution")
        
        # Score histogram
        fig_hist = px.histogram(df, x='score_percentage', nbins=10, 
                               title="Distribution of Resume Scores")
        fig_hist.update_layout(xaxis_title="Score Percentage", yaxis_title="Number of Resumes")
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Score statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Average Score", f"{df['score_percentage'].mean():.1f}%")
        with col2:
            st.metric("Median Score", f"{df['score_percentage'].median():.1f}%")
        with col3:
            st.metric("Highest Score", f"{df['score_percentage'].max():.1f}%")
        with col4:
            st.metric("Lowest Score", f"{df['score_percentage'].min():.1f}%")
    
    with tab2:
        st.subheader("Suitability Analysis")
        
        # Suitability pie chart
        suitability_counts = df['suitability'].value_counts()
        fig_pie = px.pie(values=suitability_counts.values, names=suitability_counts.index,
                       title="Resume Suitability Distribution")
        st.plotly_chart(fig_pie, use_container_width=True)
        
        # Suitability metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            high_count = len(df[df['suitability'] == 'High'])
            st.metric("High Suitability", high_count, f"{high_count/len(df)*100:.1f}%")
        with col2:
            medium_count = len(df[df['suitability'] == 'Medium'])
            st.metric("Medium Suitability", medium_count, f"{medium_count/len(df)*100:.1f}%")
        with col3:
            low_count = len(df[df['suitability'] == 'Low'])
            st.metric("Low Suitability", low_count, f"{low_count/len(df)*100:.1f}%")
    
    with tab3:
        st.subheader("Skills Analysis")
        st.info("Skills analysis will show the most common skills and gaps across all evaluations.")
        
        # Most common skills
        all_skills = []
        all_missing = []
        
        for _, row in df.iterrows():
            if row['skill_matches']:
                all_skills.extend(row['skill_matches'])
            if row['missing_skills']:
                all_missing.extend(row['missing_skills'])
        
        if all_skills:
            skills_df = pd.DataFrame({'skill': all_skills}).value_counts().head(10).reset_index()
            skills_df.columns = ['Skill', 'Count']
            
            fig_skills = px.bar(skills_df, x='Skill', y='Count', title="Most Common Skills Found")
            st.plotly_chart(fig_skills, use_container_width=True)
        
        if all_missing:
            missing_df = pd.DataFrame({'skill': all_missing}).value_counts().head(10).reset_index()
            missing_df.columns = ['Missing Skill', 'Count']
            
            fig_missing = px.bar(missing_df, x='Missing Skill', y='Count', title="Most Common Missing Skills")
            st.plotly_chart(fig_missing, use_container_width=True)

if __name__ == "__main__":
    main()
