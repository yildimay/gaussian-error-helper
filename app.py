import pandas as pd
import streamlit as st
from difflib import get_close_matches
import openai

st.set_page_config(page_title="Gaussian Error Helper")

st.title("Gaussian Error Helper")
st.write("Paste a Gaussian error message or upload a .log/.out file to get structured analysis and suggestions.")

# --- SETTINGS ---
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", "")  # Optional: add your API key in Streamlit Cloud Secrets

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1L-8Tu7hquBB468Dd7mwdzTQst2fj4syWYWD9-3TMGo0/export?format=csv&gid=0"
    return pd.read_csv(url)

def extract_known_errors(log_lines, known_errors):
    found = []
    for line in log_lines:
        for error in known_errors:
            if error.lower() in line.lower():
                found.append(error)
    return list(set(found))

def extract_log_tail(file, n=30):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    return lines, lines[-n:]

def query_gpt_fallback(error_text):
    if not OPENAI_API_KEY:
        return "OpenAI API key not set. Cannot use fallback analysis."
    openai.api_key = OPENAI_API_KEY
    prompt = f"""A Gaussian job failed with this error message:
"{error_text}"
Explain what it means and suggest a fix in 3–4 sentences."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}],
            max_tokens=300, temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

# Load error data
df = load_data()
known_errors = df["Error"].tolist()

# Inputs
user_input = st.text_area("Paste a Gaussian error message:")
uploaded_file = st.file_uploader("Or upload a Gaussian .log or .out file", type=["log", "out"])

found_errors = []
log_tail = []

if uploaded_file:
    all_lines, log_tail = extract_log_tail(uploaded_file)
    found_errors = extract_known_errors(log_tail, known_errors)

final_input = ""
if uploaded_file and found_errors:
    final_input = found_errors[0]
elif user_input:
    final_input = user_input

if st.button("Analyze Error") and final_input:
    matches = get_close_matches(final_input, df["Error"], n=1, cutoff=0.4)

    if matches:
        row = df[df["Error"] == matches[0]].iloc[0]
        st.markdown("### Match Found")
        st.markdown(f"**Error:** {row['Error']}")
        st.markdown(f"**Explanation:** {row['Explanation']}")
        st.markdown(f"**Fix:** {row['Fix']}")
        st.markdown(f"**Why:** {row['Why This Works']}")
        st.markdown(f"[Resource Link]({row['Resource']})")
        st.divider()
        feedback = st.radio("Was this helpful?", ["Yes", "No"], horizontal=True)
    else:
        st.markdown("### No Known Match Found")
        st.markdown("Trying AI fallback...")
        gpt_response = query_gpt_fallback(final_input)
        st.markdown(f"**AI Analysis:**

{gpt_response}")
        st.divider()
        feedback = st.radio("Was this AI-generated info helpful?", ["Yes", "No"], horizontal=True)

    if uploaded_file:
        st.markdown("### Last 30 Lines of Your Log File")
        st.code("\n".join(log_tail))

elif st.button("Analyze Error") and not final_input:
    st.warning("Please paste an error or upload a file.")

if uploaded_file and not found_errors:
    st.info("No known errors were found in the last 30 lines of the uploaded file.")
