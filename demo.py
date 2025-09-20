#!/usr/bin/env python3
"""
Demo script for the Resume Relevance Check System.
This script demonstrates how to use the API to upload documents and run evaluations.
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8000"
SAMPLE_DATA_DIR = "sample_data"

def check_api_health():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

def upload_job_description(file_path, title, company="Sample Company", location="Remote"):
    """Upload a job description."""
    url = f"{API_BASE_URL}/api/job-descriptions/upload"
    
    with open(file_path, 'rb') as file:
        files = {"file": file}
        data = {
            "title": title,
            "company": company,
            "location": location,
            "created_by": "Demo Script"
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()

def upload_resume(file_path, name, email="demo@example.com"):
    """Upload a resume."""
    url = f"{API_BASE_URL}/api/resumes/upload"
    
    with open(file_path, 'rb') as file:
        files = {"file": file}
        data = {
            "candidate_name": name,
            "candidate_email": email,
            "uploaded_by": "Demo Script"
        }
        
        response = requests.post(url, files=files, data=data)
        return response.json()

def start_evaluation(job_id, resume_id):
    """Start an evaluation."""
    url = f"{API_BASE_URL}/api/evaluations/evaluate"
    data = {"job_id": job_id, "resume_id": resume_id}
    
    response = requests.post(url, json=data)
    return response.json()

def get_evaluation_results(job_id):
    """Get evaluation results for a job."""
    url = f"{API_BASE_URL}/api/evaluations/job/{job_id}"
    response = requests.get(url)
    return response.json()

def wait_for_processing(seconds=10):
    """Wait for background processing to complete."""
    print(f"⏳ Waiting {seconds} seconds for processing...")
    time.sleep(seconds)

def main():
    """Main demo function."""
    print("🚀 Resume Relevance Check System Demo")
    print("=" * 50)
    
    # Check API health
    print("🔍 Checking API health...")
    if not check_api_health():
        print("❌ API is not running. Please start the backend server first.")
        print("Run: ./start_backend.sh or uvicorn backend.app.main:app --reload")
        return
    
    print("✅ API is running!")
    
    # Check for sample data
    sample_dir = Path(SAMPLE_DATA_DIR)
    if not sample_dir.exists():
        print(f"❌ Sample data directory '{SAMPLE_DATA_DIR}' not found.")
        print("Please ensure sample PDF files are in the sample_data directory.")
        return
    
    # Find sample files
    job_files = list(sample_dir.glob("*jd*.pdf")) + list(sample_dir.glob("*job*.pdf"))
    resume_files = [f for f in sample_dir.glob("*.pdf") if f not in job_files]
    
    if not job_files:
        print("❌ No job description files found in sample_data/")
        print("Expected files with 'jd' or 'job' in the filename.")
        return
    
    if not resume_files:
        print("❌ No resume files found in sample_data/")
        return
    
    print(f"📁 Found {len(job_files)} job description(s) and {len(resume_files)} resume(s)")
    
    # Upload job descriptions
    job_ids = []
    print("\n📝 Uploading job descriptions...")
    
    for i, job_file in enumerate(job_files[:2]):  # Upload first 2 job descriptions
        print(f"   Uploading: {job_file.name}")
        result = upload_job_description(
            job_file, 
            f"Sample Job Position {i+1}",
            "Demo Company",
            "San Francisco, CA"
        )
        
        if "job_id" in result:
            job_ids.append(result["job_id"])
            print(f"   ✅ Uploaded with ID: {result['job_id']}")
        else:
            print(f"   ❌ Failed to upload: {result}")
    
    # Upload resumes
    resume_ids = []
    print(f"\n👤 Uploading resumes...")
    
    for i, resume_file in enumerate(resume_files[:5]):  # Upload first 5 resumes
        print(f"   Uploading: {resume_file.name}")
        result = upload_resume(
            resume_file,
            f"Candidate {i+1}",
            f"candidate{i+1}@example.com"
        )
        
        if "resume_id" in result:
            resume_ids.append(result["resume_id"])
            print(f"   ✅ Uploaded with ID: {result['resume_id']}")
        else:
            print(f"   ❌ Failed to upload: {result}")
    
    if not job_ids or not resume_ids:
        print("❌ Failed to upload required documents for demo.")
        return
    
    # Wait for processing
    wait_for_processing(15)
    
    # Run evaluations
    print(f"\n🔍 Running evaluations...")
    
    job_id = job_ids[0]  # Use first job description
    
    for i, resume_id in enumerate(resume_ids[:3]):  # Evaluate first 3 resumes
        print(f"   Evaluating resume {resume_id} against job {job_id}")
        result = start_evaluation(job_id, resume_id)
        
        if "message" in result:
            print(f"   ✅ {result['message']}")
        else:
            print(f"   ❌ Failed: {result}")
    
    # Wait for evaluation processing
    wait_for_processing(20)
    
    # Get and display results
    print(f"\n📊 Getting evaluation results...")
    
    try:
        results = get_evaluation_results(job_id)
        
        if results and len(results) > 0:
            print(f"\n🎯 Evaluation Results for Job ID {job_id}:")
            print("-" * 60)
            
            for result in results:
                print(f"Resume ID: {result['resume_id']}")
                print(f"Score: {result['score_percentage']:.1f}%")
                print(f"Suitability: {result['suitability']}")
                print(f"Hard Match: {result['hard_match_score']:.2f}")
                print(f"Semantic Match: {result['semantic_match_score']:.2f}")
                
                if result.get('skill_matches'):
                    print(f"Matching Skills: {', '.join(result['skill_matches'][:3])}")
                
                if result.get('missing_skills'):
                    print(f"Missing Skills: {', '.join(result['missing_skills'][:3])}")
                
                print("-" * 40)
            
            # Show top candidate
            best_candidate = max(results, key=lambda x: x['score_percentage'])
            print(f"\n🏆 Top Candidate:")
            print(f"   Resume ID: {best_candidate['resume_id']}")
            print(f"   Score: {best_candidate['score_percentage']:.1f}%")
            print(f"   Suitability: {best_candidate['suitability']}")
            
        else:
            print("❌ No evaluation results found. Processing may still be in progress.")
    
    except Exception as e:
        print(f"❌ Error getting results: {e}")
    
    print(f"\n🎉 Demo completed!")
    print(f"💡 Next steps:")
    print(f"   1. Open http://localhost:8501 to view the web interface")
    print(f"   2. Explore the analytics and detailed results")
    print(f"   3. Upload your own resumes and job descriptions")

if __name__ == "__main__":
    main()
