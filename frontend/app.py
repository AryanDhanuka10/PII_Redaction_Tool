"""
app.py — Streamlit frontend for the PII Redaction web app.

Run the FastAPI backend first (see README), then:
    streamlit run app.py
"""

import requests
import streamlit as st

BACKEND_URL = "https://pii-redaction-tool-1.onrender.com"

st.set_page_config(page_title="PII Redaction Tool", page_icon="🕶️", layout="centered")

st.title("🕶️ PII Redaction Tool")
st.write(
    "Upload a `.docx` file. Names, emails, phone numbers, company names, addresses, "
    "SSNs, credit card numbers, dates of birth, and IP addresses are detected and "
    "replaced with realistic fake stand-ins — the same real value always maps to the "
    "same fake value throughout the document."
)

# quick backend liveness check
try:
    requests.get(f"{BACKEND_URL}/api/health", timeout=2)
    backend_up = True
except requests.exceptions.RequestException:
    backend_up = False

if not backend_up:
    st.error(
        f"Can't reach the backend at {BACKEND_URL}. Start it first with "
        "`uvicorn main:app --reload` from the `backend/` folder, then refresh this page."
    )
    st.stop()

uploaded = st.file_uploader("Choose a .docx file", type=["docx"])

if uploaded is not None:
    if st.button("Redact this document", type="primary"):
        with st.spinner("Reading the document and redacting PII…"):
            files = {"file": (uploaded.name, uploaded.getvalue(),
                               "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            try:
                resp = requests.post(f"{BACKEND_URL}/api/redact", files=files, timeout=300)
            except requests.exceptions.RequestException as e:
                st.error(f"Request to backend failed: {e}")
                st.stop()

        if resp.status_code != 200:
            st.error(f"Backend error: {resp.json().get('detail', resp.text)}")
            st.stop()

        result = resp.json()
        st.session_state["result"] = result

if "result" in st.session_state:
    result = st.session_state["result"]
    job_id = result["job_id"]

    st.success(f"Done — {result['total_redacted']} PII instances redacted in **{result['original_filename']}**.")

    dl = requests.get(f"{BACKEND_URL}/api/download/{job_id}")
    st.download_button(
        "⬇ Download redacted .docx",
        data=dl.content,
        file_name=f"redacted_{result['original_filename']}",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        type="primary",
    )

    st.divider()
    st.subheader("Summary report")

    cols = st.columns(len(result["by_type"]) or 1)
    for col, (pii_type, count) in zip(cols, sorted(result["by_type"].items(), key=lambda x: -x[1])):
        col.metric(pii_type, count)

    if result["flagged_count"]:
        st.warning(
            f"{result['flagged_count']} match(es) are short/ambiguous and worth a quick human "
            "double-check — see 'Flagged for review' below. This isn't a precision/recall score: "
            "for a document you just uploaded, there's no pre-known answer key to score against, "
            "so this is a heuristic flag, not a measured accuracy number."
        )

    st.subheader("Spot-check samples (original → replacement)")
    for pii_type, examples in result["samples"].items():
        with st.expander(f"{pii_type} ({result['by_type'][pii_type]} found)"):
            for ex in examples:
                st.markdown(f"~~{ex['original']}~~ → **{ex['replacement']}**")

    if result["flagged_for_review"]:
        with st.expander(f"⚠ Flagged for review ({result['flagged_count']})"):
            for entry in result["flagged_for_review"]:
                st.markdown(f"`{entry['type']}` ~~{entry['original']}~~ → **{entry['replacement']}**")

    st.divider()
    st.caption(
        "Want real precision/recall numbers instead of a heuristic flag? That requires a "
        "hand-labeled test document with a known answer key — see the offline evaluation "
        "report in the original project for an example of that methodology."
    )
