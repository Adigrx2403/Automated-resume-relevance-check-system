# 🚀 Cloud Deployment Guide

This document provides step-by-step instructions for deploying the Resume Relevance Check System on popular cloud platforms.

## 🌟 Streamlit Cloud Deployment

### Prerequisites
- GitHub repository (already set up)
- Streamlit Cloud account (free at share.streamlit.io)

### Step 1: Prepare Repository
Your repository is already configured with:
- ✅ `streamlit_app.py` - Main application file
- ✅ `requirements_streamlit.txt` - Dependencies
- ✅ `.streamlit/config.toml` - Streamlit configuration

### Step 2: Deploy on Streamlit Cloud
1. **Visit**: https://share.streamlit.io
2. **Sign in** with your GitHub account
3. **Click "New app"**
4. **Select your repository**: `Adigrx2403/Automated-resume-relevance-check-system`
5. **Set configuration**:
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
   - **Requirements file**: `requirements_streamlit.txt`
6. **Click "Deploy"**

### Step 3: Configure Environment (Optional)
In the Streamlit Cloud dashboard:
- Go to "Advanced settings"
- Add any required environment variables
- Save and redeploy

**Your app will be available at**: `https://your-app-name.streamlit.app`

---

## 🤗 HuggingFace Spaces Deployment

### Prerequisites
- HuggingFace account (free at huggingface.co)
- Git with credentials configured

### Step 1: Create HuggingFace Space
1. **Visit**: https://huggingface.co/spaces
2. **Click "Create new Space"**
3. **Configure Space**:
   - **Space name**: `resume-relevance-checker`
   - **License**: `MIT`
   - **SDK**: `Streamlit`
   - **Visibility**: `Public`
4. **Create Space**

### Step 2: Prepare Files for HuggingFace
Your repository includes:
- ✅ `README_HF.md` - HuggingFace Space README
- ✅ `streamlit_app.py` - Application
- ✅ `requirements_hf.txt` - Minimal dependencies

### Step 3: Upload to HuggingFace Space
You can either:

#### Option A: Git Clone and Push
```bash
# Clone your HuggingFace Space
git clone https://huggingface.co/spaces/YOUR_USERNAME/resume-relevance-checker
cd resume-relevance-checker

# Copy files from your project
cp /path/to/your/project/streamlit_app.py .
cp /path/to/your/project/requirements_hf.txt requirements.txt
cp /path/to/your/project/README_HF.md README.md

# Commit and push
git add .
git commit -m "Initial deployment of Resume Relevance Check System"
git push
```

#### Option B: Web Interface Upload
1. Go to your HuggingFace Space
2. Click "Files" tab
3. Upload the following files:
   - `streamlit_app.py`
   - `requirements_hf.txt` (rename to `requirements.txt`)
   - `README_HF.md` (rename to `README.md`)

**Your app will be available at**: `https://huggingface.co/spaces/YOUR_USERNAME/resume-relevance-checker`

---

## 🔧 Alternative Deployment Options

### Railway
1. **Connect GitHub** at railway.app
2. **Select repository**
3. **Add environment variables**
4. **Deploy automatically**

### Render
1. **Connect GitHub** at render.com
2. **Create Web Service**
3. **Set build/start commands**
4. **Deploy**

### Heroku
```bash
heroku create resume-checker-app
heroku config:set SECRET_KEY=$(openssl rand -base64 32)
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main
```

---

## 📊 Features Available in Demo Version

The deployed version includes:
- ✅ **Interactive Dashboard**: Overview of jobs, resumes, and evaluations
- ✅ **Job Upload**: Add job descriptions via file upload or text input
- ✅ **Resume Upload**: Add candidate resumes with metadata
- ✅ **Evaluation Engine**: Mock AI-powered resume analysis
- ✅ **Real-time Results**: Instant scoring and feedback
- ✅ **Analytics**: Visual charts and insights
- ✅ **Batch Processing**: Evaluate multiple resumes
- ✅ **Responsive Design**: Works on desktop and mobile

## 🔮 Production Features (Full Version)

The complete system includes:
- 🧠 **Real AI Processing**: Actual NLP and machine learning
- 🗄️ **Database Storage**: Persistent data with PostgreSQL
- 🔐 **Authentication**: User accounts and security
- 📁 **File Processing**: Real PDF/DOCX text extraction
- 🚀 **Background Jobs**: Async processing for large files
- 📈 **Advanced Analytics**: Deep insights and reporting
- 🔌 **API Access**: RESTful API for integrations

---

## 🛠️ Customization

### Modifying the App
- Edit `streamlit_app.py` for functionality changes
- Update `requirements.txt` for dependencies
- Modify styling in the CSS section

### Adding Features
- Extend the `MockAPI` class for new data types
- Add new pages in the navigation menu
- Include additional analytics visualizations

---

## 📞 Support

- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check the main README.md
- **Community**: Join discussions in the repository

**Happy Deploying! 🚀**
