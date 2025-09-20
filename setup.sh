#!/bin/bash

# Setup script for Resume Relevance Check System

echo "🚀 Setting up Resume Relevance Check System..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "❌ pip is not installed. Please install pip."
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📚 Installing Python packages..."
pip install -r requirements.txt

# Download spaCy model
echo "🧠 Downloading spaCy language model..."
python -m spacy download en_core_web_sm

# Create environment file
echo "⚙️ Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.template .env
    echo "✅ Created .env file from template"
    echo "⚠️  Please edit .env file and add your API keys:"
    echo "   - OPENAI_API_KEY (for OpenAI integration)"
    echo "   - HUGGINGFACE_API_TOKEN (for HuggingFace integration)"
else
    echo "✅ .env file already exists"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads/resumes
mkdir -p uploads/job_descriptions
mkdir -p vector_store
mkdir -p data

# Copy sample data if exists
if [ -d "sample_data" ]; then
    echo "📄 Copying sample data..."
    cp -r sample_data/* data/ 2>/dev/null || true
fi

# Create startup scripts
echo "📝 Creating startup scripts..."

# Backend startup script
cat > start_backend.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
EOF

# Frontend startup script
cat > start_frontend.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
streamlit run frontend/main.py --server.port 8501 --server.address 0.0.0.0
EOF

# Make scripts executable
chmod +x start_backend.sh
chmod +x start_frontend.sh

echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your API keys"
echo "2. Start the backend: ./start_backend.sh"
echo "3. In another terminal, start the frontend: ./start_frontend.sh"
echo "4. Open your browser to http://localhost:8501"
echo ""
echo "🐳 Alternative: Use Docker"
echo "1. docker-compose up -d"
echo "2. Open your browser to http://localhost:8501"
