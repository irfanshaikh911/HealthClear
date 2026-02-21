# Health Clear

A modern web application featuring a React frontend and Python (FastAPI) backend.

## Project Structure

- `frontend/` — React application built with Vite
- `backend/` — Python FastAPI REST API
- `docs/` — Project Documentation
- `.github/` — GitHub templates & workflows

## Quick Start
To run the full application locally, you'll need to run both the backend and frontend servers in separate terminal windows.

### 1. Backend Setup (FastAPI)

Open a terminal, then run:

```bash
cd backend

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# (Make sure to populate .env with your actual keys)

# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
The API should now be running at `http://127.0.0.1:8000`.
You can view the interactive API docs at `http://127.0.0.1:8000/docs`.

---

### 2. Frontend Setup (React/Vite)

Open a new terminal window, then run:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```
Your frontend should now be accessible locally (usually at `http://localhost:5173`).

## Contributing & Community

- **Contributing**: See `.github/CONTRIBUTING.md` for contribution guidelines.
- **Code of Conduct**: See `.github/CODE_OF_CONDUCT.md`.
- **License**: MIT License.

### Collaborators
- Yash Potdar
- Sahil Pawar
- Utkarsh Pingale
- Irfan Shaikh
