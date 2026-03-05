import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
import docx
import json
import plotly.express as px
import io
import re
from urllib.parse import urlparse

# ==============================
# CONFIG
# ==============================

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 AI Data Analyst Platform")

st.write("Файл эсвэл линк оруулж AI анализ хийлгэнэ")

# ==============================
# SESSION
# ==============================

if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================
# LINK ANALYZER
# ==============================

def analyze_link(url):

    try:

        r = requests.get(url, timeout=10)

        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string if soup.title else ""

        text = " ".join(p.text for p in soup.find_all("p"))

        words = len(text.split())

        links = len(soup.find_all("a"))

        images = len(soup.find_all("img"))

        return {
            "title": title,
            "words": words,
            "links": links,
            "images": images,
            "text": text[:2000]
        }

    except Exception as e:

        return {"error": str(e)}

# ==============================
# FILE READER
# ==============================

def read_file(file):

    name = file.name.lower()

    try:

        if name.endswith(".csv"):

            df = pd.read_csv(file)

            return df, "dataframe"

        elif name.endswith(".xlsx"):

            df = pd.read_excel(file)

            return df, "dataframe"

        elif name.endswith(".json"):

            data = json.load(file)

            df = pd.json_normalize(data)

            return df, "dataframe"

        elif name.endswith(".txt"):

            text = file.read().decode("utf-8")

            return text, "text"

        elif name.endswith(".pdf"):

            reader = PdfReader(file)

            text = ""

            for p in reader.pages:
                t = p.extract_text()
                if t:
                    text += t

            return text, "text"

        elif name.endswith(".docx"):

            doc = docx.Document(file)

            text = "\n".join(p.text for p in doc.paragraphs)

            return text, "text"

        else:

            return None, "unsupported"

    except Exception as e:

        return str(e), "error"

# ==============================
# LINK INPUT
# ==============================

st.subheader("🌐 Link анализ")

url = st.text_input("Website / Facebook / YouTube link")

if st.button("Link Analyze"):

    if url:

        with st.spinner("Analyzing link..."):

            result = analyze_link(url)

        if "error" in result:

            st.error(result["error"])

        else:

            st.success("Link анализ хийлээ")

            st.write("### Title")

            st.write(result["title"])

            col1, col2, col3 = st.columns(3)

            col1.metric("Words", result["words"])
            col2.metric("Links", result["links"])
            col3.metric("Images", result["images"])

            st.write("### Text Preview")

            st.write(result["text"])

# ==============================
# FILE UPLOAD
# ==============================

st.subheader("📂 File анализ")

uploaded_file = st.file_uploader(
    "Файл оруулна уу",
    type=["csv","xlsx","pdf","docx","txt","json"]
)

file_content = None
file_type = None

if uploaded_file:

    content, file_type = read_file(uploaded_file)

    file_content = content

    if file_type == "dataframe":

        df = content

        st.success("Data file уншлаа")

        st.dataframe(df.head())

        st.write("### Summary")

        st.write(df.describe())

        st.write("### Columns")

        st.write(df.columns)

        # AUTO CHART

        numeric_cols = df.select_dtypes(include="number").columns

        if len(numeric_cols) > 0:

            col = st.selectbox("Chart column", numeric_cols)

            fig = px.histogram(df, x=col)

            st.plotly_chart(fig, use_container_width=True)

    elif file_type == "text":

        st.success("Text file уншлаа")

        st.text_area("Content preview", content[:2000], height=200)

    else:

        st.error("Формат танигдсангүй")

# ==============================
# AI CHAT
# ==============================

st.subheader("💬 AI чат")

for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):

        st.markdown(msg["content"])

prompt = st.chat_input("Асуулт бич")

if prompt:

    st.session_state.messages.append(
        {"role":"user","content":prompt}
    )

    with st.chat_message("user"):

        st.markdown(prompt)

    with st.chat_message("assistant"):

        with st.spinner("AI thinking..."):

            if isinstance(file_content, pd.DataFrame):

                df = file_content

                response = f"""

📊 Data Analysis

Rows: {len(df)}

Columns: {len(df.columns)}

Columns List:
{list(df.columns)}

Numeric columns:
{list(df.select_dtypes(include='number').columns)}

Та тодорхой анализ асууж болно.

Жишээ:
- growth
- trend
- correlation
"""

            elif isinstance(file_content, str):

                response = f"""

📄 Text analysis preview

{file_content[:500]}

Та summary эсвэл keyword анализ асууж болно.
"""

            else:

                response = """
Файл эсвэл линк оруулбал илүү сайн анализ хийнэ.
"""

            st.markdown(response)

            st.session_state.messages.append(
                {"role":"assistant","content":response}
            )

# ==============================
# FOOTER
# ==============================

st.divider()

st.caption("AI Data Analyst Platform • 2026")
