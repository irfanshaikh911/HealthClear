# Health Clear - Backend

This is the Python (FastAPI) backend for the Health Clear application.

## Prerequisites
- Python 3.8 or higher installed on your machine.

## Setup Instructions

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```

4. **Install necessary packages**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Environment Variables**
   Copy the provided example file to create your local `.env` file:
   ```bash
   cp .env.example .env
   ```
   *Make sure to open `.env` and fill in any required database URLs, API keys, etc.*

6. **Start the Development Server**
   ```bash
   
   ```

That's it! The backend will start running locally.
- **API Base URL:** `http://127.0.0.1:8000`
- **Interactive OpenAPI Docs (Swagger):** `http://127.0.0.1:8000/docs`
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload