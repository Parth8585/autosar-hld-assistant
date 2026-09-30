# Contributing

1. Create a feature branch.
2. Keep generated runtime data under `data/` and out of Git.
3. Do not commit `.env`, API keys, proprietary HLDs, OEM documents, or standards text.
4. Add or update tests for ingestion, retrieval and comparison behavior.
5. Run `pytest -q` and `python -m compileall app streamlit_app.py` before opening a pull request.
