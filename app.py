import streamlit as st
import pandas as pd
import plotly.express as px
import io
from PyPDF2 import PdfReader
import docx
import re
import datetime

# =============================================================================
# ТОХИРГОО
# =============================================================================
st.set_page_config(
    page_title="AI Аналитик 2026",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🧠 AI Аналитик 2026")

st.markdown("""
<style>
    .stChatInputContainer {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: white !important;
        padding: 1rem !important;
        border-top: 1px solid #ddd !important;
        z-index: 9999 !important;
        box-shadow: 0 -4px 12px rgba(0,0,0,0.1) !important;
    }
    .main .block-container {
        padding-bottom: 160px !important;
    }
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 17px;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

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
            df = pd.read_csv(file)
            return df, "CSV хүснэгт уншлаа"
        elif name.endswith('.xlsx'):
            df = pd.read_excel(file)
            return df, "Excel хүснэгт уншлаа"
        elif name.endswith('.pdf'):
            reader = PdfReader(file)
            text = " ".join(p.extract_text() or "" for p in reader.pages if p.extract_text())
            return text, "PDF текст уншлаа"
        elif name.endswith('.docx'):
            doc = docx.Document(file)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return text, "DOCX текст уншлаа"
        return None, "Формат дэмжигдээгүй"
    except Exception as e:
        return None, f"Алдаа: {str(e)}"

# =============================================================================
# ФАЙЛ UPLOAD
# =============================================================================
uploaded_file = st.file_uploader(
    "CSV, XLSX, PDF, DOCX оруулна уу",
    type=['csv', 'xlsx', 'pdf', 'docx']
)

file_content = None
file_type = None

if uploaded_file:
    file_content, msg = read_file(uploaded_file)
    if file_content is not None:
        st.success(msg)
        if isinstance(file_content, pd.DataFrame):
            st.dataframe(file_content.head(10))
        else:
            st.text_area("Файлын агуулга (эхний хэсэг)", file_content[:3000], height=200)
    else:
        st.error(msg)

# =============================================================================
# ЧАТ ХЭСЭГ – доод талд байнга харагдана
# =============================================================================
st.markdown("---")
st.subheader("Асуулт асуух")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])

prompt = st.chat_input("Асуулт бичнэ үү... (файл оруулсан бол түүний талаар асууж болно)")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Хариулж байна..."):
            response = ""

            # Файлтай холбоотой асуулт уу?
            if file_content is not None and ("файл" in prompt.lower() or "хүснэгт" in prompt.lower() or "pdf" in prompt.lower() or "docx" in prompt.lower()):
                if isinstance(file_content, pd.DataFrame):
                    response = f"Таны хүснэгтээс харахад:\n\n{prompt}\n\nХариулт: Файлын гол мэдээлэл: {len(file_content)} мөр, {len(file_content.columns)} багана. Тодорхой багана эсвэл тренд зааж өгвөл илүү нарийн дүгнэлт өгнө."
                else:
                    response = f"Файлын агуулга:\n\n{file_content[:500]}...\n\n{prompt}\n\nХариулт: Текстээс гол санааг гаргах гэж байна. Илүү тодорхой заавар өгвөл дэлгэрэнгүй дүгнэнэ."

            # Ердийн асуулт
            elif "сайн байна уу" in prompt.lower():
                response = "Сайн байна уу! Ямар тусламж хэрэгтэй вэ? Файл оруулсан уу, эсвэл өөр асуулт байна уу?"
            elif "чи сайжирч" in prompt.lower() or "ухаалаг" in prompt.lower():
                response = "Тийм ээ, би сайжирч чадна. Гэхдээ одоо миний хариулт таны апп доторх логик дээр суурилж байна. Жинхэнэ AI (Groq/Gemini) холбоод туршаад үзээрэй."
            else:
                response = f"Таны асуулт: **{prompt}**\n\nХариулт: Одоогоор бүрэн AI холбогдоогүй тул логиктой хариулт өгч байна. Асуултаа илүү тодорхой болгоод дахин бичвэл илүү сайн тусална."

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# =============================================================================
# FOOTER
# =============================================================================
st.markdown("---")
st.caption("Текст бичдэг хэсэг доод талд байнга харагдана • Файл + чат дэмжинэ • 2026 оны шинэчлэгдсэн хувилбар")
