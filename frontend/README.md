Frontend Development
====================

This short guide explains how to run the Angular frontend during development and how it connects to the FastAPI backend.

Start the backend
-----------------
- Run the backend API first (see top-level README). By default the backend listens on `http://localhost:8000`.

Start the frontend (dev server)
------------------------------
- Install frontend deps (if needed):

  ```bash
  cd frontend
  npm install
  # or: pnpm install / yarn
  ```

- Run the dev server with the proxy (recommended):

  ```bash
  # From the repo root
  cd frontend
  npm run start
  ```

  The Angular dev server is configured to forward API calls under `/api` to the backend (see `proxy.conf.json`).

API base path
-------------
- The frontend uses `/api` as the base path for backend calls (see `src/app/services/tts-api.service.ts`).
- The proxy configuration (`frontend/proxy.conf.json`) rewrites `/api` -> `http://localhost:8000` during development so CORS is not required.

WebSocket / Streaming
---------------------
- The frontend connects to WebSocket endpoints on the backend using the same host (e.g. `ws://localhost:8000/ws/1.7b`). If you run backend on a different host/port, update the code that opens the WebSocket accordingly.

Changing the backend host
-------------------------
- If your backend is not on `localhost:8000`, update `frontend/proxy.conf.json` -> `target` and restart the dev server.

Build for production
--------------------
- Use the standard Angular build command and host the compiled files behind a webserver. Make sure your production backend accepts requests from the frontend origin or use the same host to avoid CORS issues.

Notes
-----
- The frontend expects the backend to expose API docs at `/docs` (used for manual testing) and the `/voices` CRUD endpoints described in the main README.
