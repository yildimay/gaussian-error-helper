import streamlit as st
import requests

st.set_page_config(page_title="Gaussian .gjf Fixer (LLaMA3-70B)")

st.title("🛠️ Gaussian Input File Fixer")
st.write("Upload a broken `.gjf` file and the related `.log` or `.out` file. Let AI generate a fixed Gaussian input file using LLaMA3-70B.")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-70b-8192"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

def read_uploaded_file(file):
    return file.read().decode("utf-8", errors="ignore")

def call_llama70b(prompt):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 800,
        "temperature": 0.3
    }
    try:
        res = requests.post(GROQ_API_URL, headers=headers, json=data)
        res.raise_for_status()
        return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error calling LLaMA3-70B: {e}"

gjf_file = st.file_uploader("Upload broken .gjf file", type=["gjf", "com"])
log_file = st.file_uploader("Upload related .log or .out file", type=["log", "out"])

if st.button("🔧 Fix My GJF") and gjf_file and log_file:
    with st.spinner("Analyzing and generating fixed input..."):
        gjf_content = read_uploaded_file(gjf_file)
        log_content = read_uploaded_file(log_file)

        prompt = f"""You are an expert in quantum chemistry input file preparation.

A user has uploaded a broken Gaussian input file (.gjf) and its associated log file (.log).
Your task is to use information from both to reconstruct a corrected Gaussian input file.

Return ONLY the corrected .gjf file (no explanation), formatted as plain text, including route section, title, charge/multiplicity, and fixed atomic coordinates.

--- Broken .gjf file ---
{gjf_content}

--- Gaussian log file ---
{log_content}
"""

        fixed_gjf = call_llama70b(prompt)
        st.success("✅ Fixed .gjf generated!")
        st.code(fixed_gjf, language="text")

        st.download_button("💾 Download Fixed .gjf", fixed_gjf, file_name="fixed_input.gjf", mime="text/plain")
else:
    if st.button("🔧 Fix My GJF"):
        st.warning("Please upload both a .gjf and its corresponding .log or .out file.")
