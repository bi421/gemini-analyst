import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from groq import Groq
from datetime import datetime
import io
from PyPDF2 import PdfReader
import docx

# =============================================================================
# ТОХИРГОО
# =============================================================================
st.set_page_config(page_title="Groq AI Аналитик 2026", layout="wide", page_icon="🧠")

st.title("🧠 Groq AI Аналитик 2026 — Эцсийн Хувилбар")

# CSS (input харагдах байдлыг баталгаажуулах)
st.markdown("""
<style>
    .stChatInputContainer { position: fixed; bottom: 0; width: 100%; background: white; padding: 1rem; border-top: 1px solid #ddd; z-index: 999; }
    .main { padding-bottom: 120px !important; }  /* input-тай давхцахгүй байлгах */
</style>
""", unsafe_allow_html=True)

# API clients
groq_client = Groq(api_key=st.secrets.get("GROQ_API_KEY", "")) if "GROQ_API_KEY" in st.secrets else None
gemini_client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY", "")) if "GEMINI_API_KEY" in st.secrets else None

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================================================================
# ФАЙЛ UPLOAD
# =============================================================================
uploaded_file = st.file_uploader("CSV, Excel, PDF, DOCX оруулна уу", type=['csv', 'xlsx', 'pdf', 'docx'])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(('.csv', '.xlsx')):
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.success(f"Файл уншлаа: {len(df)} мөр, {len(df.columns)} багана")
            st.dataframe(df.head(10))
        else:
            text = ""
            if uploaded_file.name.endswith('.pdf'):
                reader = PdfReader(uploaded_file)
                text = " ".join(page.extract_text() or "" for page in reader.pages)
            elif uploaded_file.name.endswith('.docx'):
                doc = docx.Document(uploaded_file)
                text = "\n".join(p.text for p in doc.paragraphs)
            st.markdown("**Файлын агуулга:**")
            st.text_area("Текст", text[:2000], height=200)
    except Exception as e:
        st.error(f"Файл уншихад алдаа: {e}")

# =============================================================================
# ЧАТ ХЭСЭГ (байнга доод талд харагдана)
# =============================================================================
st.markdown("---")
st.subheader("💬 Чат & Асуулт асуух")

# Өмнөх мессежүүд
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Текст бичдэг хэсэг (байнга доод талд)
prompt = st.chat_input("Асуулт бичнэ үү... (файл оруулсан бол түүний талаар асууж болно)")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Хариулж байна..."):
            # Эндээс жинхэнэ LLM дуудах ёстой, гэхдээ одоогоор placeholder
            response = f"Таны асуулт: **{prompt}**\n\nХариулт: Одоогоор бүрэн LLM холбогдоогүй байгаа тул placeholder хариулт өгч байна. Файл оруулсан бол түүний талаар асууж үзээрэй."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption("2026 оны эцсийн хувилбар • Файл анализ + чат • Текст бичдэг хэсэг доод талд байнга харагдана")
