# 🤖 RAG Training Bot

A **self-hosted, portable Retrieval-Augmented Generation (RAG) training bot** for company
employees. Upload your internal documents (PDFs, Word docs, text files), organize them by
**department** and **category**, and let employees ask questions through an AI chatbot that
answers using *only* your company's documents.

Built to be **100% self-hosted** — no third-party SaaS lock-in. The only external dependency
is the **Google Gemini API** (free tier available), for which **you provide your own API key**.

---

## ✨ Features

- **Role-Based Access Control (RBAC)** with three roles:
  - **Admin** — create departments, create/manage all users, manage all documents & categories.
  - **Department Uploader** — upload documents to their department and create categories within it.
  - **Department User** — read-only access: view their department's documents and chat with the bot.
- **JWT authentication** — admin-created credentials only (no public self-signup).
- **Document upload & processing** — PDF, Word (`.docx`/`.doc`), and text (`.txt`/`.md`) files
  with automatic text extraction, chunking, and vector embedding.
- **Multi-category tagging** — assign multiple categories to a single document.
- **Department isolation with a "General Company" override** — documents tagged *General Company*
  are visible to everyone; otherwise documents stay scoped to their department.
- **RAG chatbot** — powered by **LangChain + Google Gemini**, with answers grounded in the
  documents the asking user is permitted to see, including cited sources.
- **Vector search** — **ChromaDB** in embedded mode (no separate vector DB service required).
- **Docker Compose deployment** — one command to run the whole stack.
- **Tailscale-friendly** — designed to run on a private local server reachable over your tailnet.

---

## 🏗️ Architecture

```
                ┌─────────────────────────────────────────────┐
                │              Docker Compose                  │
                │                                              │
  Browser ───►  │  frontend (nginx + React SPA)  :8080         │
                │        │  /api/*  reverse-proxied            │
                │        ▼                                     │
                │  backend (FastAPI + Uvicorn)   :8000         │
                │        │                                     │
                │        ├── SQLite  (users, depts, docs meta) │
                │        ├── ChromaDB (embedded vectors)       │
                │        └── Uploads (original files)          │
                │              all under volume  rag-data:/data│
                └─────────────────────────────────────────────┘
                          │
                          └──►  Google Gemini API (embeddings + chat)
```

| Layer            | Technology                                   |
|------------------|----------------------------------------------|
| Frontend         | React 18 + Vite, served by nginx             |
| Backend / API    | Python 3.11, FastAPI, Uvicorn                |
| RAG / LLM        | LangChain + Google Gemini (`gemini-1.5-flash`)|
| Embeddings       | Gemini `text-embedding-004`                  |
| Vector store     | ChromaDB (embedded / persistent)             |
| Metadata DB      | SQLite (via SQLAlchemy)                       |
| Auth             | JWT (python-jose) + bcrypt password hashing  |
| Deployment       | Docker + Docker Compose                      |

---

## 📁 Repository Structure

```
rag-training-bot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app + router wiring
│   │   ├── config.py            # Env-driven settings
│   │   ├── database.py          # SQLAlchemy engine/session
│   │   ├── models.py            # ORM models (User, Department, Category, Document)
│   │   ├── schemas.py           # Pydantic request/response schemas
│   │   ├── auth.py              # Password hashing + JWT
│   │   ├── deps.py              # Auth & RBAC dependencies
│   │   ├── init_admin.py        # Bootstrap default admin on first launch
│   │   ├── routers/             # auth, users, departments, categories, documents, chat
│   │   └── services/            # document_processor, embeddings, vector_store, rag
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── pages/               # Login, Chat, Documents, Categories, Admin
│   │   ├── components/          # Layout / navigation
│   │   ├── context/             # AuthContext (JWT state)
│   │   └── api/                 # axios client
│   ├── package.json
│   ├── nginx.conf               # SPA + /api reverse proxy
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🚀 Quick Start (Docker Compose)

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- A **Google Gemini API key** — get a free one at <https://aistudio.google.com/app/apikey>

### 1. Clone & configure
```bash
git clone https://github.com/<your-org>/rag-training-bot.git
cd rag-training-bot
cp .env.example .env
```

Edit `.env` and set at least:
```bash
GEMINI_API_KEY=your-real-gemini-key
SECRET_KEY=$(openssl rand -hex 32)   # paste the generated value
ADMIN_PASSWORD=choose-a-strong-password
```

### 2. Build & run
```bash
docker compose up -d --build
```

### 3. Open the app
Visit **http://localhost:8080** (or `http://<server-ip>:8080`).

Log in with the admin credentials from your `.env`
(`ADMIN_USERNAME` / `ADMIN_PASSWORD`, defaults `admin` / `admin123`).

> ⚠️ **Change the default admin password immediately** after first login by creating a new
> admin user (or updating via the API) if you used the defaults.

### 4. Stop / view logs
```bash
docker compose logs -f          # follow logs
docker compose down             # stop (data persists in the rag-data volume)
docker compose down -v          # stop AND delete all data
```

---

## ⚙️ Environment Variables

All configuration is done through the `.env` file (see `.env.example`).

| Variable                  | Required | Default                          | Description                                            |
|---------------------------|----------|----------------------------------|--------------------------------------------------------|
| `GEMINI_API_KEY`          | ✅ Yes   | —                                | Your Google Gemini API key.                            |
| `SECRET_KEY`              | ✅ Yes   | —                                | JWT signing secret. Use `openssl rand -hex 32`.        |
| `GEMINI_CHAT_MODEL`       | No       | `gemini-1.5-flash`               | Gemini model used for answering.                       |
| `GEMINI_EMBEDDING_MODEL`  | No       | `models/text-embedding-004`      | Gemini embedding model.                                |
| `ADMIN_USERNAME`          | No       | `admin`                          | Username of the auto-created admin.                    |
| `ADMIN_PASSWORD`          | No       | `admin123`                       | Password of the auto-created admin (**change it!**).   |
| `ADMIN_EMAIL`             | No       | `admin@example.com`              | Email of the auto-created admin.                       |
| `APP_PORT`                | No       | `8080`                           | Host port the web UI is exposed on.                    |

Advanced (rarely changed) backend tuning is available in `backend/app/config.py`:
`CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_K`, `ACCESS_TOKEN_EXPIRE_MINUTES`.

---

## 👤 Admin User Creation

The **first admin** is created automatically on first startup from the `ADMIN_*` env vars
(see `init_admin.py`). After that, the admin creates everyone else from the **Admin dashboard**
in the UI:

1. Log in as admin → go to **Admin**.
2. **Create Department** (e.g. *Engineering*, *HR*, *Sales*).
3. **Create User** — pick a role and (for uploaders/users) a department:
   - *Department User* → can chat & view their department + general docs.
   - *Department Uploader* → the above **plus** upload documents and create categories.
   - *Admin* → full control.

There is **no public sign-up** — every credential is issued by an admin. To create an
additional admin programmatically you can also run, inside the backend container:

```bash
docker compose exec backend python -m app.init_admin
```
(That command only seeds the default admin if no admin exists yet.)

---

## 📚 Using the App

### Uploading documents (Admin / Uploader)
1. Go to **Categories** and create one or more categories (optional but recommended).
2. Go to **Documents → Upload Document**:
   - Choose a PDF / Word / text file.
   - Set **Visibility**:
     - *Department only* — visible to that department's users (and admins).
     - *General company* — visible to **all** users regardless of department.
   - (Admins) pick the target **department**. (Uploaders are auto-scoped to their own.)
   - Tick one or more **categories**.
3. The document is processed in the background (text extraction → chunking → embedding).
   Status moves from `processing` → `ready` (or `failed` with an error message).

### Chatting (everyone)
Go to **Chat** and ask a question. The bot retrieves the most relevant chunks **from the
documents you're allowed to see** and answers with cited sources. Admins can optionally
filter by department.

---

## 🔐 Access Control Summary

| Capability                         | Admin | Uploader | User |
|------------------------------------|:-----:|:--------:|:----:|
| Chat with bot                      |  ✅   |    ✅    |  ✅  |
| View department + general docs     |  ✅*  |    ✅    |  ✅  |
| Upload documents                   |  ✅   |    ✅†   |  ❌  |
| Delete documents                   |  ✅   |    ✅†   |  ❌  |
| Create categories                  |  ✅   |    ✅†   |  ❌  |
| Create departments                 |  ✅   |    ❌    |  ❌  |
| Create / manage users              |  ✅   |    ❌    |  ❌  |

\* Admin sees **all** documents.  † Uploader is scoped to **their own department**.

---

## 🌐 Tailscale Access Setup

This app is ideal for private internal use over [Tailscale](https://tailscale.com/).

1. **Install Tailscale** on the host server:
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   sudo tailscale up
   ```
2. Note the server's tailnet IP (e.g. `100.x.y.z`) or its MagicDNS name
   (e.g. `myserver.tailXXXX.ts.net`):
   ```bash
   tailscale ip -4
   tailscale status
   ```
3. Run the stack (`docker compose up -d --build`). It listens on `0.0.0.0:${APP_PORT}`.
4. From any other device on your tailnet, open:
   ```
   http://<tailscale-ip>:8080      e.g. http://100.x.y.z:8080
   ```
5. **(Optional) HTTPS via Tailscale Serve** — expose it on your tailnet with TLS:
   ```bash
   tailscale serve --bg 8080
   ```
   Your app is then reachable at `https://<machine>.<tailnet>.ts.net`.
6. **(Optional) Firewall** — since access is over Tailscale, you can block the port on the
   public interface and only allow the Tailscale interface (`tailscale0`):
   ```bash
   sudo ufw allow in on tailscale0 to any port 8080
   sudo ufw deny 8080
   ```

> Because everything is self-hosted and only the Gemini API leaves your network, your
> documents never touch any third-party storage.

---

## 🐙 GitHub Repository Setup

```bash
cd rag-training-bot
git init
git add .
git commit -m "Initial commit: self-hosted RAG training bot"
git branch -M main
git remote add origin https://github.com/<your-org>/rag-training-bot.git
git push -u origin main
```

The provided `.gitignore` keeps secrets and runtime data out of version control
(`.env`, `data/`, `node_modules/`, `*.db`, ChromaDB files, uploads, etc.).
**Never commit your real `.env`** — share `.env.example` instead.

---

## 🧑‍💻 Local Development (without Docker)

> Note: when running locally, the localhost URLs refer to *your* machine.

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export GEMINI_API_KEY=your-key SECRET_KEY=dev-secret
export DATA_DIR=./data SQLITE_PATH=./data/app.db CHROMA_DIR=./data/chroma UPLOAD_DIR=./data/uploads
uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
# proxies /api to http://localhost:8000 by default (see vite.config.js)
npm run dev
```
App: http://localhost:5173

---

## 🔌 API Reference (summary)

| Method | Endpoint                       | Role        | Description                       |
|--------|--------------------------------|-------------|-----------------------------------|
| POST   | `/api/auth/login`              | public      | Get JWT (form: username/password) |
| GET    | `/api/auth/me`                 | any         | Current user info                 |
| GET    | `/api/users`                   | admin       | List users                        |
| POST   | `/api/users`                   | admin       | Create user                       |
| PUT    | `/api/users/{id}`              | admin       | Update user                       |
| DELETE | `/api/users/{id}`              | admin       | Delete user                       |
| GET    | `/api/departments`             | any         | List departments                  |
| POST   | `/api/departments`             | admin       | Create department                 |
| DELETE | `/api/departments/{id}`        | admin       | Delete department                 |
| GET    | `/api/categories`              | any         | List categories                   |
| POST   | `/api/categories`              | uploader+   | Create category                   |
| DELETE | `/api/categories/{id}`         | uploader+   | Delete category                   |
| GET    | `/api/documents`               | any         | List visible documents            |
| POST   | `/api/documents`               | uploader+   | Upload a document (multipart)     |
| DELETE | `/api/documents/{id}`          | uploader+   | Delete a document                 |
| POST   | `/api/chat`                    | any         | Ask the RAG bot                   |

Interactive docs are always available at `/docs` (Swagger UI) on the backend.

---

## 🛠️ Troubleshooting

- **Chat returns "GEMINI_API_KEY is not set"** — set `GEMINI_API_KEY` in `.env` and
  `docker compose up -d` again.
- **Document stuck on `failed`** — check the error column in the Documents table; scanned
  PDFs with no embedded text won't extract (no OCR included).
- **Can't log in after changing `.env`** — the admin is only auto-created when *no* admin
  exists. If you changed `ADMIN_PASSWORD` after the DB was created, update the password via
  the Admin UI or delete the volume (`docker compose down -v`) to re-seed (this wipes data).
- **Port already in use** — change `APP_PORT` in `.env`.

---

## 📄 License

Provided as-is for internal company use. Add your preferred license here.
