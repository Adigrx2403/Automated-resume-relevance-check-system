@echo off
echo 🚀 Setting up Resume Relevance Check System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo 📚 Installing Python packages...
pip install -r requirements.txt

REM Download spaCy model
echo 🧠 Downloading spaCy language model...
python -m spacy download en_core_web_sm

REM Create environment file
echo ⚙️ Setting up environment variables...
if not exist .env (
    copy .env.template .env
    echo ✅ Created .env file from template
    echo ⚠️  Please edit .env file and add your API keys:
    echo    - OPENAI_API_KEY (for OpenAI integration)
    echo    - HUGGINGFACE_API_TOKEN (for HuggingFace integration)
) else (
    echo ✅ .env file already exists
)

REM Create necessary directories
echo 📁 Creating directories...
mkdir uploads\resumes 2>nul
mkdir uploads\job_descriptions 2>nul
mkdir vector_store 2>nul
mkdir data 2>nul

REM Create startup scripts
echo 📝 Creating startup scripts...

REM Backend startup script
echo @echo off > start_backend.bat
echo call venv\Scripts\activate.bat >> start_backend.bat
echo cd backend >> start_backend.bat
echo uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload >> start_backend.bat

REM Frontend startup script
echo @echo off > start_frontend.bat
echo call venv\Scripts\activate.bat >> start_frontend.bat
echo streamlit run frontend\main.py --server.port 8501 --server.address 0.0.0.0 >> start_frontend.bat

echo ✅ Setup complete!
echo.
echo 📋 Next steps:
echo 1. Edit .env file and add your API keys
echo 2. Start the backend: start_backend.bat
echo 3. In another terminal, start the frontend: start_frontend.bat
echo 4. Open your browser to http://localhost:8501
echo.
echo 🐳 Alternative: Use Docker
echo 1. docker-compose up -d
echo 2. Open your browser to http://localhost:8501
pause
