# Vedzzinsights

Vedzzinsights is a natural language data analysis tool. Instead of writing complex SQL queries by hand or clicking through clunky BI dashboards, you can just ask questions in plain English. The app translates your questions into highly optimized PostgreSQL queries, runs them, and instantly generates the right chart (line, bar, pie, or just the raw data).

I built this with a "split-screen" IDE-style layout. You get your chat/history on the left, and a massive canvas for your charts and data on the right. 

## Tech Stack
* **Frontend:** React + Vite (Custom glassmorphism UI)
* **Backend:** Python + FastAPI 
* **Database:** PostgreSQL
* **AI:** Google Gemini (Flash-Lite model)

## How it works under the hood
1. The frontend hits the backend to grab your Postgres database schema (tables + columns).
2. When you ask a question, the backend sends the schema and your question to Gemini.
3. Gemini writes the raw SQL.
4. The backend runs the SQL against your Postgres DB safely.
5. The raw data is analyzed by a heuristic function (or LLM) to decide the best way to visualize it.
6. The frontend renders the chart using Recharts.

## Local Setup

### 1. Backend (Python)
You need Python 3.9+ installed.

```bash
# setup venv
python -m venv .venv
source .venv/bin/activate  # on windows: .venv\Scripts\activate

# install dependencies
pip install -r requirements.txt

# create a .env file in the root directory
# add your keys:
# GEMINI_API_KEY=your_key_here
# DB_HOST=localhost
# DB_PORT=5432
# DB_USER=postgres
# DB_PASSWORD=your_password
# DB_NAME=your_db

# run the server
python main.py
```
The API will run on `http://localhost:8000`.

### 2. Frontend (React)
Make sure you have Node.js installed.

```bash
cd frontend
npm install
npm run dev
```
The UI will run on `http://localhost:5173`.

## Deployment
This project is currently deployed and live!
- **Backend:** Hosted on Render (`https://ai-data-analyst-do3u.onrender.com`)
- **Frontend:** Hosted on Vercel
- **Database:** PostgreSQL hosted on Supabase

## License
MIT
