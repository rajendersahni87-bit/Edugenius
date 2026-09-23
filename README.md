# 🎓 EduGenius — AI-Powered Education Platform

> **Hackathon Track 4: Education** — Enhancing personalized learning with AI

EduGenius combines **AI Tutoring**, **Smart Study Planning**, and **Progress Analytics** into one platform.

## ✨ Features

| Module | Description |
|--------|-------------|
| 🤖 **AI Tutor** | RAG-powered tutor that answers questions from your uploaded study materials. Supports Socratic and Direct modes. |
| 📅 **Study Planner** | AI generates personalized study schedules based on subjects, deadlines, and weak areas. |
| 📊 **Progress Dashboard** | Visual analytics of study hours, quiz scores, task completion, and subject-wise progress. |
| 📝 **Quiz Generator** | AI creates quizzes from your study materials with automatic grading. |
| 📄 **Document Manager** | Upload PDFs — they're chunked, embedded, and stored for RAG retrieval. |

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python)
- **AI/LLM**: Google Gemini 2.0 Flash
- **RAG**: LangChain + ChromaDB + Sentence-Transformers
- **Database**: SQLite (via SQLAlchemy)
- **Frontend**: Streamlit
- **Charts**: Plotly

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd edugenius
pip install -r backend/requirements.txt
```

### 2. Set Your API Key
Edit the `.env` file:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get a free API key at: https://aistudio.google.com/apikey

### 3. Start the Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
API docs available at: http://localhost:8000/docs

### 4. Start the Frontend (new terminal)
```bash
streamlit run streamlit_app.py
```
Opens at: http://localhost:8501

## 📖 Usage Flow

1. **Register** an account
2. **Create a Subject** (e.g., "Machine Learning")
3. **Upload PDFs** of your study materials
4. **Chat with AI Tutor** — ask questions about your materials
5. **Generate a Study Plan** — AI creates a personalized schedule
6. **Take Quizzes** — AI generates questions from your content
7. **Track Progress** — view analytics on the dashboard

## 📁 Project Structure
```
edugenius/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Settings & API keys
│   ├── database.py          # SQLAlchemy ORM models
│   ├── auth.py              # JWT authentication
│   ├── routers/             # API endpoint handlers
│   ├── services/            # Business logic (RAG, Planner, Quiz, Progress)
│   ├── prompts/             # LLM prompt templates
│   └── requirements.txt     # Python dependencies
├── streamlit_app.py         # Streamlit frontend (single file)
├── .env                     # API key configuration
└── README.md
```

## 🔑 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login & get JWT |
| POST | `/api/documents/subjects` | Create subject |
| POST | `/api/documents/upload` | Upload PDF |
| POST | `/api/tutor/chat` | Chat with AI Tutor |
| POST | `/api/planner/generate` | Generate study plan |
| GET | `/api/progress/dashboard` | Get dashboard data |
| POST | `/api/progress/quiz/generate` | Generate quiz |
| POST | `/api/progress/quiz/submit` | Submit quiz |

## 📄 License

MIT — Built for Hackathon 2026