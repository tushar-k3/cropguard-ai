# CropGuard AI — Smart Farming Assistant

AI-powered agriculture platform for Indian farmers.
Supports English, Hindi, and Marathi.

## Tech Stack
- **Frontend:** React 18 + Vite + Tailwind CSS + react-i18next
- **Backend:** Django 5.1 + Django REST Framework + SimpleJWT
- **Database:** SQLite (dev) → PostgreSQL (prod)

## Quick Start

### Backend (Git Bash on Windows)
```bash
cd backend
source venv/Scripts/activate
python manage.py runserver
```

### Frontend
```bash
cd frontend
npm run dev
```

## URLs
| URL | Purpose |
|---|---|
| http://localhost:5173 | React frontend |
| http://127.0.0.1:8000/api/health/ | API health check |
| http://127.0.0.1:8000/admin/ | Django admin |

## Switching to PostgreSQL
In `backend/.env`, change `DB_ENGINE=sqlite` to `DB_ENGINE=postgres`
and fill in the DB credentials. No code changes required.