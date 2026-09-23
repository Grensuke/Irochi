# Project Startup Guide

I have partially started the project for you! 

Because your **Docker Desktop daemon is not currently running**, I was unable to start the full backend infrastructure. However, I have completed all the prerequisite setup and started the frontend in **Mock Mode**, so you can begin using the UI immediately.

### 1. Frontend (Currently Running)
The frontend is running in mock mode at **[http://localhost:5173](http://localhost:5173)**. 
I accomplished this by:
1. Navigating to the `frontend/` directory.
2. Running `npm install` and `npm install esbuild --ignore-scripts` to install dependencies.
3. Running `npx vite` to start the development server.

### 2. Backend Environment (Prepared)
I have set up the backend environment so it is ready to go once Docker is running:
1. Created `infrastructure/.env` with secure passwords.
2. Created `backend/.env` with matching passwords, database configurations, and generated a `JWT_SECRET_KEY`.
3. Created a Python virtual environment in `backend/.venv` and installed all dependencies from `requirements.txt`.

### 3. Next Steps: Running the Full Stack
To switch from Mock Mode to the Full Stack, please follow these steps:

1. **Start Docker Desktop** on your machine and wait for the engine to be fully running.
2. Open a terminal and start the infrastructure:
   ```bash
   cd d:\SIH-145\infrastructure
   docker compose up -d
   ```
3. Open a second terminal, run the database migrations, and start the FastAPI backend:
   ```powershell
   cd d:\SIH-145\backend
   .\.venv\Scripts\Activate.ps1
   alembic upgrade head
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Update the frontend to point to the real API by creating a `.env` file in `d:\SIH-145\frontend\` with:
   ```ini
   VITE_MOCK=false
   VITE_API_BASE_URL=http://localhost:8000
   VITE_WS_URL=ws://localhost:8000/ws/alerts
   ```
5. Restart the frontend development server (`npm run dev`).
