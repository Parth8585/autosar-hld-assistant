# 🚗 AUTOSAR HLD Document Analysis Assistant

An evaluation-ready **pilot implementation** for ingesting AUTOSAR High-Level Design (HLD) PDFs, extracting architecture knowledge, performing cited semantic search/Q&A, and comparing document revisions.

> **Evaluation note:** The repository is self-contained and includes only synthetic demonstration documents. No proprietary engineering documents or standards text are included.

## What this project demonstrates

- PDF ingestion with **PyMuPDF**.
- Optional OCR for scanned pages using **Tesseract + Pillow**.
- Context-aware chunking with page metadata.
- Heuristic extraction of components, interfaces, ports, signals and datatypes.
- Candidate relationship mapping from entity co-occurrence.
- Persistent local **ChromaDB** vector retrieval, with an offline fallback if ChromaDB is unavailable.
- Grounded RAG responses with **page citations and retrieved evidence**.
- Pluggable response modes: extractive, Ollama, OpenAI-compatible and Anthropic.
- Revision comparison with candidate additions/removals/common entities.
- Structured JSON export.
- SQLite document/query/audit persistence.
- Streamlit engineering UI + FastAPI backend.
- Docker + Docker Compose.
- Automated tests and GitHub Actions CI.

The implementation focuses on controlled document ingestion, section and metadata extraction, architecture entity recognition, natural-language Q&A with citations, revision comparison, candidate inconsistency reporting and structured export. FastAPI, Streamlit, local embeddings/vector storage and Docker are used to keep the pilot easy to run locally.

## Architecture

```text
                         ┌───────────────────────────────┐
                         │        Streamlit UI           │
                         │ Upload • Search • Compare    │
                         │ Export • Audit               │
                         └──────────────┬────────────────┘
                                        │ REST
                         ┌──────────────▼────────────────┐
                         │          FastAPI               │
                         │ Validation • Workflow • Audit │
                         └───────┬───────────────┬───────┘
                                 │               │
                    ┌────────────▼───────┐   ┌──▼──────────────┐
                    │ PDF / OCR Ingestion │   │ SQLite          │
                    │ PyMuPDF/Tesseract   │   │ docs/entities   │
                    └────────────┬────────┘   │ audit/query log │
                                 │             └─────────────────┘
                         ┌───────▼────────┐
                         │ Embedding/RAG  │
                         │ TF-IDF / ST    │
                         └───────┬────────┘
                                 │
                         ┌───────▼────────┐
                         │ ChromaDB       │
                         │ local vectors  │
                         └───────┬────────┘
                                 │ evidence
                         ┌───────▼────────┐
                         │ Response layer │
                         │ Extractive /   │
                         │ Ollama / API   │
                         └────────────────┘
```

The reference architecture similarly separates UI, application/API services, AI/RAG orchestration, LLM inference, embeddings, local vector storage, structured storage, ingestion and security/operations.

## Repository structure

```text
autosar-hld-assistant/
├── app/
│   ├── main.py              # FastAPI application and endpoints
│   ├── ingestion.py         # PDF/OCR/tables/chunking/entity extraction
│   ├── embeddings.py        # TF-IDF or Sentence Transformers
│   ├── vectorstore.py       # ChromaDB + offline fallback
│   ├── rag.py               # Retrieval + grounded response workflow
│   ├── llm.py               # LLM provider adapters
│   ├── database.py          # SQLite + audit/query persistence
│   ├── compare.py           # Revision comparison
│   └── config.py            # Environment configuration
├── streamlit_app.py         # Engineering UI
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DEMO.md
│   └── EVALUATION.md
├── sample_data/             # Synthetic HLD demo PDFs only
├── tests/
├── .github/workflows/ci.yml
├── .env.example
├── .dockerignore
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE
└── requirements.txt
```

## Quick start — Docker (recommended for evaluation)

### 1. Clone

```bash
git clone https://github.com/<YOUR_USERNAME>/autosar-hld-assistant.git
cd autosar-hld-assistant
```

### 2. Start

No API key is required for the default demo mode:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Open:

- **Streamlit:** http://localhost:8501
- **FastAPI:** http://localhost:8000
- **Swagger API docs:** http://localhost:8000/docs

### 3. Demo

Upload:

```text
sample_data/sample_hld_v1.pdf
sample_data/sample_hld_v2.pdf
```

Then:

1. Ask `Which component publishes BrakeStatusSignal?`
2. Inspect source pages/evidence.
3. Download structured JSON.
4. Compare revisions.
5. Open the Audit tab.

## Local setup without Docker

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
$env:PYTHONPATH="."
uvicorn app.main:app --reload --port 8000
```

Open a second terminal:

```powershell
.\.venv\Scripts\Activate.ps1
$env:PYTHONPATH="."
streamlit run streamlit_app.py
```

### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
export PYTHONPATH=.
uvicorn app.main:app --reload --port 8000
```

Second terminal:

```bash
source .venv/bin/activate
export PYTHONPATH=.
streamlit run streamlit_app.py
```

## LLM configuration

The default configuration is deliberately **extractive** so an evaluator can run the complete ingestion → embedding → retrieval → citation workflow without an API key.

For a local generative model, install Ollama separately and set:

```env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

For an OpenAI-compatible endpoint:

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

Never commit `.env` or API keys.

## Embedding configuration

For a zero-download demo:

```env
EMBEDDING_BACKEND=tfidf
```

For semantic embeddings:

```env
EMBEDDING_BACKEND=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

Sentence Transformers and ChromaDB can be enabled for semantic local retrieval when required.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/documents/upload` | Ingest PDF |
| GET | `/documents` | List documents |
| GET | `/documents/{id}` | Document metadata |
| GET | `/documents/{id}/entities` | Extracted entities |
| GET | `/documents/{id}/analysis` | Structured analysis |
| GET | `/documents/{id}/export` | JSON export |
| POST | `/query` | Grounded Q&A |
| POST | `/compare` | Revision comparison |
| GET | `/query-log` | Query audit trail |
| GET | `/audit-log` | Ingestion/query audit trail |

## Evaluation mapping

| Requirement | Where implemented |
|---|---|
| Controlled PDF ingestion | `app/main.py`, `app/ingestion.py` |
| OCR | `app/ingestion.py` |
| Section/chunk extraction | `app/ingestion.py` |
| Architecture entities | `app/ingestion.py` |
| Local vector search | `app/vectorstore.py` |
| Cited Q&A | `app/rag.py`, `app/llm.py` |
| Revision comparison | `app/compare.py` |
| Structured export | `/documents/{id}/export` |
| Audit trail | `app/database.py` |
| Engineering UI | `streamlit_app.py` |
| Docker | `docker/` |
| CI/tests | `tests/`, `.github/workflows/ci.yml` |

Consequential engineering outputs remain advisory and require appropriate human review.

## Important limitations

This repository is a **pilot/student implementation**, not a certified automotive engineering tool.

- Heuristic entity extraction can miss or misclassify entities.
- OCR quality depends on scan quality and Tesseract.
- The default extractive mode is not a generative LLM.
- LLM responses are advisory and must be reviewed.
- The pilot UI is single-user; enterprise RBAC/IAM is not implemented.
- Comparison is an entity-level candidate diff, not proof of a semantic architecture mismatch.
- Neo4j, PostgreSQL, enterprise IAM, monitoring and Kubernetes are intentionally left as scale-stage extensions.

These boundaries keep the pilot focused on evidence, traceability, auditability and human review rather than autonomous engineering approval.

## Testing

```bash
pytest -q
python -m compileall app streamlit_app.py
```

## GitHub publishing checklist

Before pushing:

- [ ] Remove `.env` if it exists.
- [ ] Do not add proprietary HLDs or standards documents.
- [ ] Run tests.
- [ ] Run the Docker build.
- [ ] Check `git status`.
- [ ] Push only source, docs, synthetic sample data and configuration examples.

## License

MIT — see `LICENSE`.
