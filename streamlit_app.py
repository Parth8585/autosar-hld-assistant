from __future__ import annotations

import json
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="AUTOSAR HLD Assistant", page_icon="🚗", layout="wide")


def api(method: str, path: str, **kwargs):
    try:
        response = requests.request(method, f"{API_URL}{path}", timeout=180, **kwargs)
        if response.ok:
            return response.json(), None
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text
        return None, f"HTTP {response.status_code}: {detail}"
    except requests.RequestException as exc:
        return None, f"Cannot reach backend at {API_URL}: {exc}"


def get_docs():
    data, err = api("GET", "/documents")
    return data or [], err


st.title("🚗 AUTOSAR HLD Document Analysis Assistant")
st.caption("RAG pilot • PDF ingestion • architecture entity extraction • cited Q&A • revision comparison")

health, health_err = api("GET", "/health")
if health_err:
    st.warning(f"Backend unavailable: {health_err}")
else:
    st.success("Backend connected", icon="✅")

upload_tab, ask_tab, compare_tab, docs_tab, audit_tab = st.tabs(
    ["📄 Upload & Analyze", "🔎 Ask / Search", "🔁 Compare Revisions", "📦 Documents & Export", "🧾 Audit"]
)

with upload_tab:
    st.subheader("Upload an HLD document")
    st.write("The pilot extracts page text, attempts OCR for scanned pages, identifies architecture entities, indexes chunks, and stores metadata locally.")
    uploaded = st.file_uploader("PDF only", type=["pdf"], help="Recommended maximum size: 25 MB.")
    if uploaded and st.button("Ingest document", type="primary"):
        with st.spinner("Extracting, analyzing and indexing…"):
            data, err = api("POST", "/documents/upload", files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")})
        if err:
            st.error(err)
        else:
            st.success(f"Ingested **{data['filename']}** — {data['num_pages']} pages, {data['num_chunks']} chunks, {data['num_entities']} entities.")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Pages", data["num_pages"])
            c2.metric("Chunks", data["num_chunks"])
            c3.metric("Entities", data["num_entities"])
            c4.metric("Tables", data["num_tables"])
            if data["ocr_pages"]:
                st.info(f"OCR was used on pages: {data['ocr_pages']}")

with ask_tab:
    st.subheader("Evidence-grounded Q&A")
    docs, err = get_docs()
    if err:
        st.error(err)
    else:
        options = {"All documents": None}
        options.update({f"{d['filename']} (ID {d['id']})": d["id"] for d in docs})
        selected = st.selectbox("Document scope", list(options), key="ask_scope")
        question = st.text_area("Question", placeholder="e.g. Which component publishes BrakeStatusSignal?", height=90)
        if st.button("Ask", type="primary") and question.strip():
            with st.spinner("Retrieving evidence…"):
                result, err = api("POST", "/query", json={"question": question, "document_id": options[selected]})
            if err:
                st.error(err)
            else:
                st.markdown("### Answer")
                st.markdown(result["answer"])
                st.caption(f"Source pages: {', '.join(map(str, result['citations'])) if result['citations'] else 'none'}")
                with st.expander("Retrieved evidence", expanded=True):
                    for evidence in result["evidence"]:
                        st.markdown(f"**Page {evidence['page']} · relevance {evidence['score']:.3f}**")
                        st.code(evidence["text"], language="text")

with compare_tab:
    st.subheader("Compare two revisions")
    docs, err = get_docs()
    if err:
        st.error(err)
    elif len(docs) < 2:
        st.info("Upload at least two HLD revisions to compare them.")
    else:
        options = {f"{d['filename']} (ID {d['id']})": d["id"] for d in docs}
        c1, c2 = st.columns(2)
        with c1:
            a = st.selectbox("Revision A", list(options), key="rev_a")
        with c2:
            b = st.selectbox("Revision B", list(options), index=min(1, len(options)-1), key="rev_b")
        if st.button("Compare revisions", type="primary"):
            if options[a] == options[b]:
                st.warning("Choose two different documents.")
            else:
                result, err = api("POST", "/compare", json={"document_id_a": options[a], "document_id_b": options[b]})
                if err:
                    st.error(err)
                else:
                    st.info(result["summary"])
                    if result["potential_issues"]:
                        st.warning("Potential review issues detected")
                        st.dataframe(result["potential_issues"], use_container_width=True)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Only in A", len(result["only_in_document_a"]))
                    c2.metric("Only in B", len(result["only_in_document_b"]))
                    c3.metric("Common", len(result["common"]))
                    with st.expander("Added candidates (only in B)", expanded=True):
                        st.dataframe(result["only_in_document_b"], use_container_width=True)
                    with st.expander("Removed candidates (only in A)"):
                        st.dataframe(result["only_in_document_a"], use_container_width=True)

with docs_tab:
    st.subheader("Ingested documents")
    docs, err = get_docs()
    if err:
        st.error(err)
    elif not docs:
        st.info("No documents have been ingested yet.")
    else:
        for doc in docs:
            with st.expander(f"{doc['filename']} · {doc['num_pages']} pages · ID {doc['id']}"):
                st.json(doc)
                analysis, analysis_err = api("GET", f"/documents/{doc['id']}/analysis")
                if analysis_err:
                    st.error(analysis_err)
                else:
                    st.write("Entity counts")
                    st.json(analysis["entity_counts"])
                    st.dataframe(analysis["entities"], use_container_width=True)
                    export, export_err = api("GET", f"/documents/{doc['id']}/export")
                    if not export_err:
                        st.download_button(
                            "Download structured JSON",
                            data=json.dumps(export, indent=2),
                            file_name=f"{doc['filename'].rsplit('.', 1)[0]}_export.json",
                            mime="application/json",
                        )

with audit_tab:
    st.subheader("Audit trail")
    audit, err = api("GET", "/audit-log")
    if err:
        st.error(err)
    else:
        st.dataframe(audit, use_container_width=True)
