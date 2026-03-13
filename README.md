# naukri-ai

## Stack

- FastAPI serves the backend APIs under `/api/*`
- React + Vite serves the frontend SPA
- React Router handles browser routes
- TanStack Query manages API state
- Cookie-based auth remains the session mechanism

## Frontend

Source lives in `frontend/app`.

Commands:

```bash
npm install
npm run dev
npm run build
```

Vite dev server runs on `http://127.0.0.1:5173` and proxies `/api/*` to FastAPI.

Build output goes to `frontend/dist`. FastAPI serves that built SPA automatically when present.

The old Jinja template layer and legacy static assets have been removed from the active codebase. The frontend runtime now consists of the React/Vite app and the built files under `frontend/dist`.

## Backend

Run the API server:

```bash
python -m uvicorn main:app --reload
```

New session endpoints for the SPA:

- `GET /api/session`
- `POST /api/session/login`
- `POST /api/session/signup`
- `POST /api/session/logout`
- `POST /api/session/forgot-password`
- `POST /api/session/reset-password/{token}`
