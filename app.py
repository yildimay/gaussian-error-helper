import pandas as pd
import streamlit as st
from difflib import get_close_matches

st.set_page_config(page_title="Gaussian Error Helper", page_icon="🔬")

st.title("🔬 Gaussian Error Helper")
st.write("Paste your Gaussian error message below to get explanations and possible fixes.")

@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/1L-8Tu7hquBB468Dd7mwdzTQst2fj4syWYWD9-3TMGo0/export?format=csv&gid=0"
    return pd.read_csv(url)

df = load_data()

user_input = st.text_area("📋 Paste your Gaussian error message here:")

if st.button("🔍 Analyze Error") and user_input:
    matches = get_close_matches(user_input, df["Error"], n=1, cutoff=0.4)
    
    if matches:
        row = df[df["Error"] == matches[0]].iloc[0]
        st.success("✅ Match found!")
        st.write(f"### 🧠 Explanation\n{row['Explanation']}")
        st.write(f"### 🛠 Fix\n{row['Fix']}")
        st.write(f"### 🤓 Why\n{row['Why This Works']}")
        st.markdown(f"[📚 Learn more here]({row['Resource']})")
    else:
        st.error("❌ No good match found. Try rephrasing or checking for typos.")
