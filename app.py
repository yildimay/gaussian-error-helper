import pandas as pd
import streamlit as st
from difflib import SequenceMatcher
import hashlib
import openai
import os

st.set_page_config(page_title="Gaussian AI Error Assistant")

st.title("Gaussian AI-Based Error Assistant")
st.write("Upload a Gaussian log file or paste an error to get AI-powered analysis. First 5 GPT queries per user are free.")

OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")
CACHE_FILE = "ai_error_memory.csv"

if "query_count" not in st.session_state:
    st.session_state.query_count = 0

MAX_FREE_QUERIES = 5

if not os.path.exists(CACHE_FILE):
    pd.DataFrame(columns=["log_hash", "error_line", "gpt_answer"]).to_csv(CACHE_FILE, index=False)

@st.cache_data
def load_memory():
    return pd.read_csv(CACHE_FILE)

def save_to_memory(log_hash, error_line, gpt_answer):
    new_entry = pd.DataFrame([[log_hash, error_line, gpt_answer]], columns=["log_hash", "error_line", "gpt_answer"])
    existing = pd.read_csv(CACHE_FILE)
    pd.concat([existing, new_entry], ignore_index=True).to_csv(CACHE_FILE, index=False)

def generate_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def query_gpt(error_text):
    if not OPENAI_API_KEY:
        return "OpenAI API key not set. Cannot use fallback analysis."
    openai.api_key = OPENAI_API_KEY
    prompt = f"""You are an expert in computational chemistry.
A Gaussian job failed with this error log or message:
"{error_text}"

Explain what went wrong and suggest a fix in 3-4 sentences.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=350,
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

def extract_log_tail(file, n=30):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    return lines[-n:]

# Load memory
memory_df = load_memory()

# Input
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
    else:
        log_hash = generate_hash(error_text)
        memory_match = memory_df[memory_df["log_hash"] == log_hash]

        if not memory_match.empty:
            st.success("✅ Found in memory (previously solved):")
            st.markdown(memory_match.iloc[0]["gpt_answer"])
        elif st.session_state.query_count >= MAX_FREE_QUERIES:
            st.error("🚫 You've reached the free usage limit. Please subscribe for unlimited access.")
        else:
            st.info("🔍 No match found in memory. Asking AI...")
            gpt_response = query_gpt(error_text)
            save_to_memory(log_hash, error_text.splitlines()[-1], gpt_response)
            st.success("🤖 AI Suggestion:")
            st.markdown(gpt_response)
            st.session_state.query_count += 1
            st.info(f"Remaining free GPT queries: {MAX_FREE_QUERIES - st.session_state.query_count}")
