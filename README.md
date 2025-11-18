# Agentic Timetable Planner

## 🎯 Project Overview
An AI-powered university timetable planner that uses Google's Gemini LLM and Agent Development Kit to generate optimal timetables with complex constraints.

## ✨ Features
- **Agent-Based Planning**: Uses Google Cloud's Agent Development Kit for intelligent timetable generation
- **Constraint Management**: Handles multiple constraints:
  - Classroom availability
  - Faculty schedules
  - Subject requirements
  - Section assignments
  - Track-based curriculum
  - Open electives
- **Chat Interface**: Natural language interaction for uploading data and requirements
- **File Upload**: Support for faculty lists, subject details, and constraint files
- **Cloud Deployment**: Deployed on Google Cloud Run with GCP database

## 🏗️ Architecture

### Technology Stack
- **Backend**: FastAPI (Python)
- **LLM**: Google Gemini API
- **Agent Framework**: Google Cloud Agent Development Kit
- **Package Manager**: uv
- **Database**: GCP Cloud SQL / Firestore
- **Deployment**: Google Cloud Run
- **Frontend**: Simple HTML/CSS/JavaScript

### System Components
1. **Agent System**: Multi-agent architecture for constraint solving
2. **API Layer**: RESTful endpoints for data upload and timetable generation
3. **Chat Interface**: Natural language processing for user interactions
4. **Database Layer**: Stores faculty, subjects, constraints, and generated timetables

## 📋 Requirements

### Dependencies
- Python 3.11+
- uv package manager
- Google Cloud account with:
  - Gemini API access
  - Cloud Run enabled
  - Cloud SQL or Firestore enabled
- Gemini API Key

### Environment Variables
```bash
GEMINI_API_KEY=your_api_key_here
GCP_PROJECT_ID=your_project_id
DATABASE_URL=your_database_url
```

## 🚀 Getting Started

### Installation

1. **Install uv package manager**:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. **Clone the repository**:
```bash
cd /home/nihal-ubuntu/Desktop/Development/Agentic-timetable-planner
```

3. **Create virtual environment and install dependencies**:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

4. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env with your credentials
```

5. **Run the application**:
```bash
uvicorn main:app --reload
```

### Development

```bash
# Run locally
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Access the application
# API: http://localhost:8000
# UI: http://localhost:8000/static/index.html
# Docs: http://localhost:8000/docs
```

## 📁 Project Structure
```
Agentic-timetable-planner/
├── main.py                 # FastAPI application entry point
├── agents/                 # Agent system modules
│   ├── __init__.py
│   ├── timetable_agent.py # Main timetable generation agent
│   ├── constraint_agent.py # Constraint validation agent
│   └── optimizer_agent.py  # Optimization agent
├── models/                 # Data models
│   ├── __init__.py
│   ├── faculty.py
│   ├── subject.py
│   ├── classroom.py
│   └── timetable.py
├── services/              # Business logic
│   ├── __init__.py
│   ├── gemini_service.py  # Gemini API integration
│   ├── agent_service.py   # Agent coordination
│   └── database_service.py # Database operations
├── static/                # Frontend files
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── config/                # Configuration
│   └── settings.py
├── tests/                 # Test files
├── Dockerfile            # Container configuration
├── cloudbuild.yaml       # Cloud Build configuration
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── README.md             # This file
└── updates.md            # Development log
```

## 🔧 API Endpoints

### Core Endpoints
- `POST /api/upload/faculty` - Upload faculty data
- `POST /api/upload/subjects` - Upload subject data
- `POST /api/upload/constraints` - Upload constraint data
- `POST /api/chat` - Chat interface for natural language requests
- `POST /api/generate-timetable` - Generate timetable
- `GET /api/timetable/{id}` - Retrieve generated timetable

## 🤖 Agent System

### Agent Roles
1. **Planner Agent**: Analyzes requirements and creates initial schedule
2. **Constraint Agent**: Validates and enforces all constraints
3. **Optimizer Agent**: Optimizes timetable for efficiency
4. **Chat Agent**: Handles natural language interactions

## 🌩️ Deployment

### Deploy to Cloud Run
```bash
# Build and deploy
gcloud run deploy timetable-planner \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY
```

## 📝 License
MIT License

## 👥 Contributing
Contributions welcome! Please read our contributing guidelines first.

## 📧 Support
For issues and questions, please open a GitHub issue.
