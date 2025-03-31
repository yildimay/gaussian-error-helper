import streamlit as st
import hashlib
import requests

st.set_page_config(page_title="Gaussian AI Assistant (Groq + Login)")

st.title("Gaussian AI Error Assistant (Membership + Groq)")
st.write("Upload a Gaussian log file to get AI-powered analysis. Each user has 5 free queries.")

# Groq API Config
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama3-8b-8192"
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")

# Simple in-memory usage tracker (per session only for now)
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "usage" not in st.session_state:
    st.session_state.usage = {}

# Login section
st.subheader("🔐 Sign In")
user_email = st.text_input("Enter your email to start", key="email_input")
if st.button("Login"):
    st.session_state.user_email = user_email.strip().lower()
    if st.session_state.user_email not in st.session_state.usage:
        st.session_state.usage[st.session_state.user_email] = 0
    st.success(f"Logged in as {st.session_state.user_email}")

# Require login before use
if not st.session_state.user_email:
    st.stop()

# Show remaining usage
used = st.session_state.usage[st.session_state.user_email]
remaining = max(0, 5 - used)
st.info(f"Remaining AI queries: {remaining}")

# Upload only — chat box removed
uploaded_file = st.file_uploader("Upload a Gaussian .log or .out file", type=["log", "out"])
error_text = ""

def extract_log_tail(file, n=30):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    return lines[-n:]

def query_groq(prompt):
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
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Groq API Error: {e}"

# Analysis logic
if uploaded_file and st.button("Analyze with AI"):
    if remaining <= 0:
        st.error("🚫 You've used all your free queries. Please subscribe to continue.")
    else:
        log_tail = extract_log_tail(uploaded_file)
        error_text = "\n".join(log_tail)
        prompt = f"""You are an expert in computational chemistry.
A Gaussian job failed with this error log or message:
"{error_text}"

Explain what went wrong and suggest a fix in 3-4 sentences.
"""
        result = query_groq(prompt)
        st.session_state.usage[st.session_state.user_email] += 1
        st.success("🤖 AI Suggestion:")
        st.markdown(result)
        new_remaining = 5 - st.session_state.usage[st.session_state.user_email]
        st.info(f"Remaining AI queries: {new_remaining}")
