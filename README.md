<div align="center">
  <h1>📊 Vedzzinsights</h1>
  <p><strong>A Natural Language Data Analysis & BI Platform</strong></p>

  [![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)](#)
  [![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](#)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](#)
  [![Gemini](https://img.shields.io/badge/Gemini_3.1-4285F4?style=for-the-badge&logo=google&logoColor=white)](#)
</div>

<br />

Vedzzinsights completely replaces the need for writing manual SQL queries or clicking through clunky Business Intelligence dashboards. Just ask questions about your data in plain English, and the platform translates it into highly optimized PostgreSQL, executes it safely, and instantly renders the perfect chart (line, bar, pie, or metrics).

### 🚀 Live Demo
- **Frontend App:** [Currently Hosted on Vercel](https://ai-data-analyst-eight-gamma.vercel.app/)
- **Backend API:** [Hosted on Render](https://ai-data-analyst-do3u.onrender.com)
- **Database:** PostgreSQL on Supabase

---

## ✨ Features

- **Split-Screen Workspace:** An IDE-style layout with chat history on the left and a massive dynamic canvas for data visualization on the right.
- **Dynamic Visualization:** Automatically detects the shape of your data and chooses the best Recharts component (Bar, Line, Pie, or raw data tables).
- **Glassmorphism UI:** A custom, premium dark-mode interface built from scratch without bulky CSS frameworks.
- **LLM-Powered SQL Generation:** Uses Google's Gemini Flash-Lite model to generate complex queries based on your exact database schema.
- **CSV Data Ingestion:** Drag and drop CSV files directly into the UI to instantly create tables and populate data in PostgreSQL.

## 🛠️ Architecture / How it Works

1. **Schema Extraction:** The React frontend hits the FastAPI backend to map your Postgres database schema (tables + columns).
2. **Natural Language Processing:** When a question is asked, the backend bundles the schema context + user prompt and sends it to the Gemini API.
3. **Execution:** Gemini returns raw SQL, which the backend safely executes against the PostgreSQL database.
4. **Heuristic Analysis:** The resulting raw data is analyzed by a custom heuristic function to determine the optimal X/Y axes and chart type.
5. **Rendering:** The frontend receives the structured payload and mounts the appropriate `recharts` component.

---

## 💻 Local Development

### 1. Backend (Python)
Requires Python 3.9+

```bash
# Set up virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Environment Variables (.env)
# GEMINI_API_KEY=your_key
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=password
# DB_NAME=your_db

# Run the API
python main.py
```
*API runs on `http://localhost:8000`*

### 2. Frontend (React)
Requires Node.js 18+

```bash
cd frontend
npm install
npm run dev
```
*UI runs on `http://localhost:5173`*

## 📜 License
MIT License - do whatever you want with it!
