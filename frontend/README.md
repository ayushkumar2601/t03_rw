# Company Knowledge Base Chatbot — Frontend

A modern, responsive Next.js web interface for querying the Company Knowledge Base RAG system with verifiable citations, interactive source inspection, and fluid micro-animations.

---

## Features

- **Conversational Chat Interface**: Real-time Q&A interface with query suggestions and loading animations.
- **Verifiable Citations**: Answers display badges for retrieved source documents, page numbers, and unique chunk IDs.
- **Source Inspector**: Clicking any citation displays the exact text excerpt extracted from the knowledge base PDF.
- **Abstention Indicators**: Clearly flags when context is insufficient rather than presenting hallucinations.
- **GSAP Fluid Transitions**: Smooth message slide-in and spring animations for incoming responses.
- **Fast Local Proxy**: Rewrites and routes `/api/chat` calls directly to the FastAPI backend.

---

## Architecture Decisions

1. **Next.js App Router (React 19)**:
   - Utilizes Next.js 16 with React 19 for fast client rendering and built-in edge/node route handlers.
   - Clean component boundaries keeping state management lightweight without external heavy state stores.

2. **Backend Proxy & Conversational Short-Circuit**:
   - `frontend/src/app/api/chat/route.js` handles requests from the client.
   - Handles standard conversational greetings (e.g., *"hello"*, *"who are you"*, *"thanks"*) with zero latency while routing factual questions directly to the FastAPI backend (`http://127.0.0.1:8000/chat`).
   - Configured with `next.config.mjs` path rewrites for optional direct `/api/backend` proxying.

3. **Pure Modern CSS + GSAP**:
   - Styled with custom CSS variables (`globals.css`) ensuring high contrast, clean typography, and zero heavy CSS library overhead.
   - GSAP powers fluid spring transitions for chat message rendering.

---

## Prerequisites

- **Node.js**: v18.17+ (tested on Node 20 / 24)
- **FastAPI Backend**: Running on `http://127.0.0.1:8000`

---

## Getting Started

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Run Development Server**:
   ```bash
   npm run dev
   ```

3. **Access the App**:
   Open [http://localhost:3000](http://localhost:3000) in your web browser.

---

## Configuration & Environment Variables

The frontend connects to the FastAPI backend by default at:
- **Backend URL**: `http://127.0.0.1:8000`

If deploying to a custom host or port, configure an environment variable in `.env.local` (or your deployment dashboard):
```env
# Optional: defaults to http://127.0.0.1:8000
BACKEND_URL=http://127.0.0.1:8000
```

---

## Production Build

To build and start the production-optimized Next.js bundle:

```bash
npm run build
npm run start
```
