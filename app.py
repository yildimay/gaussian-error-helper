import streamlit as st
import hashlib
import requests

st.set_page_config(page_title="Gaussian AI Assistant (Groq-only)")

st.title("Gaussian AI Error Assistant (Groq LLaMA3 Only)")
st.write("Upload a Gaussian log file or paste an error to get fresh AI-powered analysis. No memory checks. Free via Groq API.")

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

MAX_FREE_QUERIES = 5
if "query_count" not in st.session_state:
    st.session_state.query_count = 0

def generate_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def query_groq(prompt):
    if not GROQ_API_KEY:
        return "Groq API key not set. Cannot use fallback analysis."
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 300,
        "temperature": 0.7
    }
    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error from Groq API: {http_err}\nResponse: {response.text}"
    except Exception as e:
        return f"Other error: {e}"

def extract_log_tail(file, n=30):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    return lines[-n:]

# Inputs
user_input = st.text_area("Paste a Gaussian error message:")
uploaded_file = st.file_uploader("Or upload a Gaussian .log/.out file", type=["log", "out"])

error_text = ""
if uploaded_file:
    log_tail = extract_log_tail(uploaded_file)
    error_text = "\n".join(log_tail)
elif user_input:
    error_text = user_input.strip()

if st.button("Analyze with AI"):
    if not error_text:
        st.warning("Please paste an error message or upload a file.")
    elif st.session_state.query_count >= MAX_FREE_QUERIES:
        st.error("🚫 You've reached the free usage limit. Please subscribe for unlimited access.")
    else:
        prompt = f"""You are an expert in computational chemistry.
A Gaussian job failed with this error log or message:
"{error_text}"

Explain what went wrong and suggest a fix in 3-4 sentences.
"""
        ai_response = query_groq(prompt)
        st.success("🤖 AI Suggestion:")
        st.markdown(ai_response)
        st.session_state.query_count += 1
        st.info(f"Remaining free GPT-style queries: {MAX_FREE_QUERIES - st.session_state.query_count}")
