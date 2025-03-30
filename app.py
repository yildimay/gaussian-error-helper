import pandas as pd
import streamlit as st
from difflib import get_close_matches

st.set_page_config(page_title="Gaussian Error Helper", page_icon="🔬")
st.title("🔬 Gaussian Error Helper")
st.write("Paste your Gaussian error message **or upload a .log/.out file** to get explanations and fixes.")

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1L-8Tu7hquBB468Dd7mwdzTQst2fj4syWYWD9-3TMGo0/export?format=csv&gid=0"
    return pd.read_csv(url)

def extract_error_from_log(file):
    lines = file.read().decode("utf-8", errors="ignore").splitlines()
    tail = lines[-30:]  # last 30 lines
    possible_errors = []
    for line in tail:
        for known_error in df["Error"]:
            if known_error.lower() in line.lower():
                possible_errors.append(known_error)
    return list(set(possible_errors)), "\n".join(tail)

df = load_data()

# Input options
user_input = st.text_area("📋 Paste your Gaussian error message here:")
uploaded_file = st.file_uploader("📁 Or upload a Gaussian .log or .out file", type=["log", "out"])

errors_found = []
log_tail = ""

if uploaded_file:
    errors_found, log_tail = extract_error_from_log(uploaded_file)
    if errors_found:
        st.success("✅ Found possible error(s) in uploaded file:")
        for e in errors_found:
            st.write(f"- {e}")
    else:
        st.warning("⚠️ No known error patterns found in the last 30 lines of the log.")

# Choose source of input
final_input = ""
if uploaded_file and errors_found:
    final_input = errors_found[0]
elif user_input:
    final_input = user_input

if st.button("🔍 Analyze Error") and final_input:
    matches = get_close_matches(final_input, df["Error"], n=1, cutoff=0.4)
    
    if matches:
        row = df[df["Error"] == matches[0]].iloc[0]
        st.success("✅ Match found!")
        st.write(f"### 🧠 Explanation\n{row['Explanation']}")
        st.write(f"### 🛠 Fix\n{row['Fix']}")
        st.write(f"### 🤓 Why\n{row['Why This Works']}")
        st.markdown(f"[📚 Learn more here]({row['Resource']})")
        if uploaded_file:
            st.write("---")
            st.write("### 📄 Last 30 lines of your log file:")
            st.code(log_tail)
    else:
        st.error("❌ No good match found. Try rephrasing or checking for typos.")
