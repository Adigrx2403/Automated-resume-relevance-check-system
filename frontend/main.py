import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu
import json
from datetime import datetime
import os

# Configuration
API_BASE_URL = "http://localhost:8000"  # FastAPI backend URL

# Page configuration
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
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #1f77b4;
    }
    .suitability-high {
        color: #28a745;
        font-weight: bold;
    }
    .suitability-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .suitability-low {
        color: #dc3545;
        font-weight: bold;
    }
    .upload-area {
        border: 2px dashed #1f77b4;
        border-radius: 10px;
        padding: 2rem;
        text-align: center;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Utility functions
def make_api_request(endpoint, method="GET", data=None, files=None):
    """Make API request to the backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to the backend server. Please ensure the FastAPI server is running.")
        return None
    except Exception as e:
        st.error(f"Error making API request: {str(e)}")
        return None

def get_suitability_color(suitability):
    """Get color class for suitability."""
    if suitability == "High":
        return "suitability-high"
    elif suitability == "Medium":
        return "suitability-medium"
    else:
        return "suitability-low"

# Main navigation
def main():
    st.markdown('<h1 class="main-header">📄 Resume Relevance Check System</h1>', unsafe_allow_html=True)
    
    # Navigation menu
    selected = option_menu(
        menu_title=None,
        options=["Dashboard", "Upload Job Description", "Upload Resume", "Evaluations", "Analytics"],
        icons=["speedometer2", "file-earmark-plus", "person-plus", "clipboard-check", "graph-up"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
    )
    
    if selected == "Dashboard":
        dashboard_page()
    elif selected == "Upload Job Description":
        upload_job_description_page()
    elif selected == "Upload Resume":
        upload_resume_page()
    elif selected == "Evaluations":
        evaluations_page()
    elif selected == "Analytics":
        analytics_page()

def dashboard_page():
    """Main dashboard page."""
    st.header("📊 System Dashboard")
    
    # Get dashboard data
    jobs_data = make_api_request("/api/job-descriptions")
    resumes_data = make_api_request("/api/resumes")
    
    if jobs_data is not None and resumes_data is not None:
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Job Descriptions", len(jobs_data))
        
        with col2:
            st.metric("Total Resumes", len(resumes_data))
        
        with col3:
            # Get evaluation count (approximate)
            total_evaluations = 0
            for job in jobs_data[:5]:  # Check first 5 jobs to avoid too many API calls
                evaluations = make_api_request(f"/api/evaluations/job/{job['id']}")
                if evaluations:
                    total_evaluations += len(evaluations)
            st.metric("Total Evaluations", f"{total_evaluations}+")
        
        with col4:
            st.metric("System Status", "🟢 Online")
        
        # Recent activity
        st.subheader("📋 Recent Job Descriptions")
        if jobs_data:
            recent_jobs = jobs_data[:5]  # Show last 5
            df_jobs = pd.DataFrame(recent_jobs)
            
            # Display job descriptions table
            display_cols = ['id', 'title', 'company', 'location', 'created_at']
            available_cols = [col for col in display_cols if col in df_jobs.columns]
            
            if available_cols:
                st.dataframe(df_jobs[available_cols], use_container_width=True)
            else:
                st.write("No job descriptions available.")
        
        st.subheader("👥 Recent Resumes")
        if resumes_data:
            recent_resumes = resumes_data[:5]
            df_resumes = pd.DataFrame(recent_resumes)
            
            display_cols = ['id', 'candidate_name', 'candidate_email', 'original_filename', 'created_at']
            available_cols = [col for col in display_cols if col in df_resumes.columns]
            
            if available_cols:
                st.dataframe(df_resumes[available_cols], use_container_width=True)
            else:
                st.write("No resumes available.")
    else:
        st.warning("⚠️ Unable to load dashboard data. Please check the backend connection.")

def upload_job_description_page():
    """Job description upload page."""
    st.header("📝 Upload Job Description")
    
    with st.form("job_upload_form"):
        st.markdown('<div class="upload-area">', unsafe_allow_html=True)
        
        # File upload
        uploaded_file = st.file_uploader(
            "Choose a job description file",
            type=['pdf', 'docx'],
            help="Upload PDF or DOCX files only"
        )
        
        # Job details
        col1, col2 = st.columns(2)
        with col1:
            job_title = st.text_input("Job Title", placeholder="e.g., Software Engineer")
            company = st.text_input("Company", placeholder="e.g., Tech Corp")
        
        with col2:
            location = st.text_input("Location", placeholder="e.g., New York, NY")
            created_by = st.text_input("Uploaded by", placeholder="Your name")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Upload Job Description", type="primary")
        
        if submitted and uploaded_file is not None:
            with st.spinner("Uploading and processing job description..."):
                # Prepare files and data for upload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {
                    "title": job_title,
                    "company": company,
                    "location": location,
                    "created_by": created_by
                }
                
                # Upload job description
                result = make_api_request("/api/job-descriptions/upload", method="POST", data=data, files=files)
                
                if result:
                    st.success("✅ Job description uploaded successfully!")
                    st.json(result)
                    
                    # Show next steps
                    st.info("💡 **Next Steps:**\n"
                           "1. Go to the Evaluations page to evaluate resumes against this job\n"
                           "2. Or upload resumes and run batch evaluation")
                else:
                    st.error("❌ Failed to upload job description.")

def upload_resume_page():
    """Resume upload page."""
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
            candidate_name = st.text_input("Candidate Name", placeholder="Full name")
            candidate_email = st.text_input("Email", placeholder="email@example.com")
        
        with col2:
            candidate_phone = st.text_input("Phone", placeholder="+1 (555) 123-4567")
            uploaded_by = st.text_input("Uploaded by", placeholder="Your name")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        submitted = st.form_submit_button("Upload Resume", type="primary")
        
        if submitted and uploaded_file is not None:
            with st.spinner("Uploading and processing resume..."):
                # Prepare files and data for upload
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                data = {
                    "candidate_name": candidate_name,
                    "candidate_email": candidate_email,
                    "candidate_phone": candidate_phone,
                    "uploaded_by": uploaded_by
                }
                
                # Upload resume
                result = make_api_request("/api/resumes/upload", method="POST", data=data, files=files)
                
                if result:
                    st.success("✅ Resume uploaded successfully!")
                    st.json(result)
                    
                    # Show next steps
                    st.info("💡 **Next Steps:**\n"
                           "1. Go to the Evaluations page to evaluate this resume against job descriptions\n"
                           "2. Check Analytics to see performance insights")
                else:
                    st.error("❌ Failed to upload resume.")

def evaluations_page():
    """Evaluations management page."""
    st.header("🔍 Resume Evaluations")
    
    # Get job descriptions and resumes
    jobs_data = make_api_request("/api/job-descriptions")
    resumes_data = make_api_request("/api/resumes")
    
    if not jobs_data or not resumes_data:
        st.warning("⚠️ No job descriptions or resumes available. Please upload some first.")
        return
    
    # Evaluation options
    tab1, tab2, tab3 = st.tabs(["Single Evaluation", "Batch Evaluation", "View Results"])
    
    with tab1:
        st.subheader("Evaluate Single Resume")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Job selection
            job_options = {f"{job['title']} - {job['company']}": job['id'] for job in jobs_data}
            selected_job = st.selectbox("Select Job Description", options=list(job_options.keys()))
            
        with col2:
            # Resume selection
            resume_options = {f"{resume['candidate_name']} ({resume['original_filename']})": resume['id'] 
                            for resume in resumes_data}
            selected_resume = st.selectbox("Select Resume", options=list(resume_options.keys()))
        
        if st.button("🚀 Start Evaluation", type="primary"):
            if selected_job and selected_resume:
                job_id = job_options[selected_job]
                resume_id = resume_options[selected_resume]
                
                with st.spinner("Starting evaluation..."):
                    result = make_api_request(
                        "/api/evaluations/evaluate",
                        method="POST",
                        data={"job_id": job_id, "resume_id": resume_id}
                    )
                    
                    if result:
                        st.success("✅ Evaluation started successfully!")
                        st.json(result)
                    else:
                        st.error("❌ Failed to start evaluation.")
    
    with tab2:
        st.subheader("Batch Evaluate All Resumes")
        
        # Job selection for batch evaluation
        job_options = {f"{job['title']} - {job['company']}": job['id'] for job in jobs_data}
        selected_job_batch = st.selectbox("Select Job Description for Batch Evaluation", 
                                         options=list(job_options.keys()))
        
        st.info(f"This will evaluate all {len(resumes_data)} resumes against the selected job description.")
        
        if st.button("🚀 Start Batch Evaluation", type="primary"):
            if selected_job_batch:
                job_id = job_options[selected_job_batch]
                
                with st.spinner("Starting batch evaluation..."):
                    result = make_api_request(
                        "/api/evaluations/batch-evaluate",
                        method="POST",
                        data={"job_id": job_id}
                    )
                    
                    if result:
                        st.success("✅ Batch evaluation started successfully!")
                        st.json(result)
                        st.info("⏳ This may take a few minutes. Check the 'View Results' tab to see progress.")
                    else:
                        st.error("❌ Failed to start batch evaluation.")
    
    with tab3:
        st.subheader("Evaluation Results")
        
        # Job selection for viewing results
        job_options = {f"{job['title']} - {job['company']}": job['id'] for job in jobs_data}
        selected_job_results = st.selectbox("Select Job Description to View Results", 
                                           options=list(job_options.keys()))
        
        if selected_job_results:
            job_id = job_options[selected_job_results]
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                suitability_filter = st.selectbox("Filter by Suitability", 
                                                 options=["All", "High", "Medium", "Low"])
            with col2:
                min_score = st.slider("Minimum Score", 0.0, 100.0, 0.0, 5.0)
            
            # Get evaluations
            params = {"min_score": min_score / 100.0}
            if suitability_filter != "All":
                params["suitability"] = suitability_filter
            
            evaluations = make_api_request(f"/api/evaluations/job/{job_id}", data=params)
            
            if evaluations:
                st.success(f"Found {len(evaluations)} evaluations")
                
                # Display results
                for eval_data in evaluations:
                    with st.expander(f"Resume ID: {eval_data['resume_id']} - Score: {eval_data['score_percentage']:.1f}% - "
                                   f"Suitability: {eval_data['suitability']}"):
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Combined Score", f"{eval_data['score_percentage']:.1f}%")
                            st.markdown(f"<span class='{get_suitability_color(eval_data['suitability'])}'>"
                                      f"Suitability: {eval_data['suitability']}</span>", 
                                      unsafe_allow_html=True)
                        
                        with col2:
                            st.metric("Hard Match Score", f"{eval_data['hard_match_score']:.2f}")
                            st.metric("Semantic Match Score", f"{eval_data['semantic_match_score']:.2f}")
                        
                        with col3:
                            if eval_data.get('skill_matches'):
                                st.write("**Skill Matches:**")
                                st.write(", ".join(eval_data['skill_matches'][:5]))
                            
                            if eval_data.get('missing_skills'):
                                st.write("**Missing Skills:**")
                                st.write(", ".join(eval_data['missing_skills'][:5]))
                        
                        # Improvement suggestions
                        if eval_data.get('improvement_suggestions'):
                            st.write("**💡 Improvement Suggestions:**")
                            for suggestion in eval_data['improvement_suggestions']:
                                st.write(f"• {suggestion}")
            else:
                st.info("No evaluations found for this job description.")

def analytics_page():
    """Analytics and reporting page."""
    st.header("📈 Analytics & Reports")
    
    # Get data for analytics
    jobs_data = make_api_request("/api/job-descriptions")
    resumes_data = make_api_request("/api/resumes")
    
    if not jobs_data or not resumes_data:
        st.warning("⚠️ No data available for analytics.")
        return
    
    # Job selection for analytics
    job_options = {f"{job['title']} - {job['company']}": job['id'] for job in jobs_data}
    selected_job_analytics = st.selectbox("Select Job Description for Analytics", 
                                         options=list(job_options.keys()))
    
    if selected_job_analytics:
        job_id = job_options[selected_job_analytics]
        
        # Get evaluation data
        evaluations = make_api_request(f"/api/evaluations/job/{job_id}")
        
        if evaluations and len(evaluations) > 0:
            # Convert to DataFrame
            df = pd.DataFrame(evaluations)
            
            # Analytics tabs
            tab1, tab2, tab3 = st.tabs(["Score Distribution", "Suitability Analysis", "Skills Analysis"])
            
            with tab1:
                st.subheader("Score Distribution")
                
                # Score histogram
                fig_hist = px.histogram(df, x='score_percentage', nbins=20, 
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
                
                # Most common missing skills
                all_missing_skills = []
                for eval_data in evaluations:
                    if eval_data.get('missing_skills'):
                        all_missing_skills.extend(eval_data['missing_skills'])
                
                if all_missing_skills:
                    missing_skills_df = pd.DataFrame({'skill': all_missing_skills})
                    missing_skills_counts = missing_skills_df['skill'].value_counts().head(10)
                    
                    fig_missing = px.bar(x=missing_skills_counts.values, y=missing_skills_counts.index,
                                       orientation='h', title="Top Missing Skills")
                    fig_missing.update_layout(xaxis_title="Number of Resumes Missing This Skill",
                                            yaxis_title="Skills")
                    st.plotly_chart(fig_missing, use_container_width=True)
                
                # Score vs Skills correlation
                st.subheader("Hard Match vs Semantic Match Analysis")
                fig_scatter = px.scatter(df, x='hard_match_score', y='semantic_match_score',
                                       color='suitability', size='score_percentage',
                                       title="Hard Match vs Semantic Match Scores")
                st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No evaluation data available for analytics. Please run some evaluations first.")

if __name__ == "__main__":
    main()
