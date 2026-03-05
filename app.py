import streamlit as st
import pandas as pd
import plotly.express as px
from groq import Groq
import google.generativeai as genai
from datetime import datetime
from PyPDF2 import PdfReader
import docx
import io

# =============================================================================
# ТОХИРГОО
# =============================================================================
st.set_page_config(
    page_title="Groq AI Аналитик 2026",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Groq AI Аналитик 2026")

# CSS — текст бичдэг хэсгийг доод талд байнга харагдуулах
st.markdown("""
<style>
    .stChatInputContainer {
        position: fixed !important;
        bottom: 0 !important;
        width: 100% !important;
        background: white !important;
        padding: 1rem !important;
        border-top: 1px solid #ddd !important;
        z-index: 999 !important;
    }
    .main .block-container {
        padding-bottom: 140px !important;
    }
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 17px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# API CLIENTS
# =============================================================================
groq_client = None
if "GROQ_API_KEY" in st.secrets:
    try:
        groq_client = Groq(api_key=st.secrets["GROQ_API_KEY"])
    except Exception as e:
        st.error(f"Groq холболт амжилтгүй: {e}")

gemini_client = None
if "GEMINI_API_KEY" in st.secrets:
    try:
        genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
        gemini_client = genai.GenerativeModel("gemini-2.5-flash")
    except Exception as e:
        st.error(f"Gemini холболт амжилтгүй: {e}")

# =============================================================================
# SESSION STATE
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================================================================
# ФАЙЛ УНШИХ ФУНКЦ
# =============================================================================
def read_file(file):
    name = file.name.lower()
    try:
        if name.endswith('.csv'):
            return pd.read_csv(file)
        elif name.endswith('.xlsx'):
            return pd.read_excel(file)
        elif name.endswith('.pdf'):
            reader = PdfReader(file)
            return " ".join(page.extract_text() or "" for page in reader.pages)
        elif name.endswith('.docx'):
            doc = docx.Document(file)
            return "\n".join(p.text for p in doc.paragraphs)
        return "Формат дэмжигдээгүй"
    except Exception as e:
        return f"Алдаа: {str(e)}"

# =============================================================================
# ФАЙЛ UPLOAD
# =============================================================================
uploaded_file = st.file_uploader(
    "CSV, Excel, PDF, DOCX файл оруулна уу",
    type=['csv', 'xlsx', 'pdf', 'docx']
)

if uploaded_file:
    content = read_file(uploaded_file)
    if isinstance(content, pd.DataFrame):
        st.success(f"Файл уншлаа: {len(content)} мөр, {len(content.columns)} багана")
        st.dataframe(content.head(10))
    else:
        st.markdown("**Файлын агуулга:**")
        st.text_area("Текст", content[:3000], height=200)

# =============================================================================
# ЧАТ ХЭСЭГ — байнга доод талд харагдана
# =============================================================================
st.markdown("---")
st.subheader("💬 Чат ба асуулт асуух хэсэг")

# Өмнөх мессежүүд
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Текст бичдэг хэсэг (байнга харагдана)
prompt = st.chat_input("Асуулт бичнэ үү... (файл оруулсан бол түүний талаар асууж болно)")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Хариулж байна..."):
            if not groq_client and not gemini_client:
                response = "API key байхгүй байна. secrets.toml-д GROQ_API_KEY эсвэл GEMINI_API_KEY оруулна уу."
            else:
                # Жинхэнэ LLM дуудна (Groq приоритет)
                try:
                    if groq_client:
                        resp = groq_client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=[
                                {"role": "system", "content": "Чи Монгол хэлний мэргэжлийн туслах. Товч, ухаантай, бодитой хариул."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.7,
                            max_tokens=1500
                        )
                        response = resp.choices[0].message.content
                    elif gemini_client:
                        resp = gemini_client.generate_content(prompt)
                        response = resp.text
                except Exception as e:
                    response = f"AI холболтод алдаа гарлаа: {str(e)}"

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption("2026 оны эцсийн хувилбар • Текст бичдэг хэсэг доод талд байнга харагдана • Файл + чат дэмжинэ")
