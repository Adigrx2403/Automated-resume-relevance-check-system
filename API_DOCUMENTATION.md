# API Documentation

## Resume Relevance Check System API

Base URL: `http://localhost:8000`

### Authentication
Currently, no authentication is required. For production, implement OAuth2 or JWT authentication.

## Endpoints

### Health Check

#### GET /health
Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2023-12-01T10:00:00"
}
```

### Job Descriptions

#### POST /api/job-descriptions/upload
Upload and process a job description file.

**Parameters:**
- `file` (FormData): PDF or DOCX file
- `title` (string): Job title
- `company` (string): Company name
- `location` (string): Job location
- `created_by` (string): Name of uploader

**Response:**
```json
{
  "message": "Job description uploaded successfully",
  "job_id": 1,
  "status": "processing"
}
```

#### GET /api/job-descriptions
List all job descriptions.

**Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "title": "Software Engineer",
    "company": "Tech Corp",
    "location": "New York, NY",
    "created_at": "2023-12-01T10:00:00",
    "skills_required": ["Python", "React", "SQL"],
    "is_active": true
  }
]
```

#### GET /api/job-descriptions/{job_id}
Get a specific job description.

**Response:**
```json
{
  "id": 1,
  "title": "Software Engineer",
  "company": "Tech Corp",
  "location": "New York, NY",
  "extracted_text": "We are looking for...",
  "skills_required": ["Python", "React", "SQL"],
  "certifications_required": ["AWS Certified"],
  "keywords": ["python", "software", "development"],
  "created_at": "2023-12-01T10:00:00"
}
```

### Resumes

#### POST /api/resumes/upload
Upload and process a resume file.

**Parameters:**
- `file` (FormData): PDF or DOCX file
- `candidate_name` (string): Candidate's full name
- `candidate_email` (string): Candidate's email
- `candidate_phone` (string): Candidate's phone number
- `uploaded_by` (string): Name of uploader

**Response:**
```json
{
  "message": "Resume uploaded successfully",
  "resume_id": 1,
  "status": "processing"
}
```

#### GET /api/resumes
List all resumes.

**Parameters:**
- `skip` (int): Number of records to skip (default: 0)
- `limit` (int): Maximum records to return (default: 100)
- `search` (string): Search by name or email

**Response:**
```json
[
  {
    "id": 1,
    "candidate_name": "John Doe",
    "candidate_email": "john@example.com",
    "original_filename": "john_resume.pdf",
    "skills": ["Python", "JavaScript", "SQL"],
    "experience_years": 3.5,
    "created_at": "2023-12-01T10:00:00"
  }
]
```

#### GET /api/resumes/{resume_id}
Get a specific resume.

**Response:**
```json
{
  "id": 1,
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "extracted_text": "John Doe Software Engineer...",
  "skills": ["Python", "JavaScript", "SQL"],
  "certifications": ["AWS Certified Developer"],
  "keywords": ["python", "javascript", "web", "development"],
  "created_at": "2023-12-01T10:00:00"
}
```

### Evaluations

#### POST /api/evaluations/evaluate
Evaluate a specific resume against a job description.

**Request Body:**
```json
{
  "job_id": 1,
  "resume_id": 1
}
```

**Response:**
```json
{
  "message": "Evaluation started",
  "status": "processing"
}
```

#### POST /api/evaluations/batch-evaluate
Evaluate all resumes against a specific job description.

**Request Body:**
```json
{
  "job_id": 1
}
```

**Response:**
```json
{
  "message": "Batch evaluation started for 10 resumes",
  "status": "processing"
}
```

#### GET /api/evaluations/job/{job_id}
Get all evaluations for a specific job.

**Parameters:**
- `suitability` (string): Filter by suitability (High, Medium, Low)
- `min_score` (float): Minimum score filter (0.0-1.0)

**Response:**
```json
[
  {
    "id": 1,
    "job_description_id": 1,
    "resume_id": 1,
    "combined_score": 0.75,
    "score_percentage": 75.0,
    "suitability": "High",
    "hard_match_score": 0.70,
    "semantic_match_score": 0.80,
    "skill_matches": ["Python", "SQL"],
    "missing_skills": ["React", "Docker"],
    "improvement_suggestions": [
      "Consider learning React for frontend development",
      "Docker containerization skills would be valuable"
    ],
    "created_at": "2023-12-01T10:00:00"
  }
]
```

#### GET /api/evaluations/resume/{resume_id}
Get all evaluations for a specific resume.

**Response:**
```json
[
  {
    "id": 1,
    "job_description_id": 1,
    "resume_id": 1,
    "combined_score": 0.75,
    "suitability": "High",
    "created_at": "2023-12-01T10:00:00"
  }
]
```

#### GET /api/evaluations/top-candidates/{job_id}
Get top candidates for a job.

**Parameters:**
- `limit` (int): Maximum candidates to return (default: 10)

**Response:**
```json
[
  {
    "evaluation": {
      "id": 1,
      "combined_score": 0.85,
      "suitability": "High",
      "score_percentage": 85.0
    },
    "resume": {
      "id": 1,
      "candidate_name": "John Doe",
      "candidate_email": "john@example.com"
    }
  }
]
```

## Error Responses

All endpoints may return these error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid input data"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 413 Payload Too Large
```json
{
  "detail": "File too large"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## File Upload Constraints

- **Supported formats**: PDF, DOCX
- **Maximum file size**: 10MB
- **Accepted MIME types**: 
  - `application/pdf`
  - `application/vnd.openxmlformats-officedocument.wordprocessingml.document`

## Rate Limiting

Currently no rate limiting is implemented. For production:
- Implement rate limiting per IP/user
- Consider API key-based access
- Add request quotas

## Example Python Client

```python
import requests
import json

class ResumeRelevanceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def upload_job_description(self, file_path, title, company, location):
        url = f"{self.base_url}/api/job-descriptions/upload"
        files = {"file": open(file_path, "rb")}
        data = {
            "title": title,
            "company": company,
            "location": location
        }
        response = requests.post(url, files=files, data=data)
        return response.json()
    
    def upload_resume(self, file_path, name, email):
        url = f"{self.base_url}/api/resumes/upload"
        files = {"file": open(file_path, "rb")}
        data = {
            "candidate_name": name,
            "candidate_email": email
        }
        response = requests.post(url, files=files, data=data)
        return response.json()
    
    def evaluate_resume(self, job_id, resume_id):
        url = f"{self.base_url}/api/evaluations/evaluate"
        data = {"job_id": job_id, "resume_id": resume_id}
        response = requests.post(url, json=data)
        return response.json()
    
    def get_top_candidates(self, job_id, limit=10):
        url = f"{self.base_url}/api/evaluations/top-candidates/{job_id}"
        params = {"limit": limit}
        response = requests.get(url, params=params)
        return response.json()

# Usage example
client = ResumeRelevanceClient()

# Upload job description
job_result = client.upload_job_description(
    "job_description.pdf",
    "Software Engineer",
    "Tech Corp",
    "San Francisco, CA"
)

# Upload resume
resume_result = client.upload_resume(
    "resume.pdf",
    "John Doe",
    "john@example.com"
)

# Evaluate
evaluation = client.evaluate_resume(
    job_result["job_id"],
    resume_result["resume_id"]
)

# Get top candidates
top_candidates = client.get_top_candidates(job_result["job_id"])
```

## WebSocket Support (Future)

For real-time updates during processing:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Processing update:', data);
};
```
