import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from groq import Groq
import json
from datetime import datetime
import io
from PyPDF2 import PdfReader
import docx
import re

# ========================== ТОХИРГОО ==========================
st.set_page_config(
    page_title="Groq AI Аналитик 2026",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Groq AI Аналитик 2026 — Эцсийн Шинэчлэгдсэн Хувилбар")

# CSS
st.markdown("""
<style>
    .main { padding: 2rem; }
    h1 { font-size: 28px; }
    .stButton>button { width: 100%; height: 52px; font-size: 17px; }
</style>
""", unsafe_allow_html=True)

# ========================== API KEYS ==========================
groq_client = Groq(api_key=st.secrets.get("GROQ_API_KEY", ""))
gemini_client = genai.Client(api_key=st.secrets.get("GEMINI_API_KEY", "")) if "GEMINI_API_KEY" in st.secrets else None

# ========================== МОДЕЛЬ СОНГОЛТ ==========================
model_choice = st.sidebar.selectbox(
    "Модель сонгоно уу",
    ["Gemini 2.5 Flash (хурдан)", "Groq Llama 4 (ухаантай)", "Gemini 2.5 Pro (хамгийн хүчтэй)"],
    index=0
)

# ========================== ФАЙЛ UPLOAD ==========================
uploaded_file = st.file_uploader(
    "CSV, Excel, PDF, DOCX файл оруулна уу", 
    type=['csv', 'xlsx', 'pdf', 'docx']
)

if uploaded_file is None:
    st.info("Анализ хийхийн тулд файл оруулна уу")
    st.stop()

# ========================== ФАЙЛ УНШИХ ==========================
def read_file(file):
    name = file.name.lower()
    try:
        if name.endswith('.csv'):
            return pd.read_csv(file)
        elif name.endswith('.xlsx'):
            return pd.read_excel(file)
        elif name.endswith('.pdf'):
            reader = PdfReader(file)
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            return text
        elif name.endswith('.docx'):
            doc = docx.Document(file)
            return "\n".join(p.text for p in doc.paragraphs)
    except:
        return "Файл уншихад алдаа гарлаа"

df_or_text = read_file(uploaded_file)

if isinstance(df_or_text, pd.DataFrame):
    df = df_or_text
    st.success(f"✅ Файл уншлаа: {len(df)} мөр, {len(df.columns)} багана")
else:
    st.info("Текст файл уншлаа. Доор анализ хийнэ.")
    df = None

# ========================== ГРАФИК ==========================
if isinstance(df_or_text, pd.DataFrame) and len(df.columns) >= 2:
    st.subheader("📊 Автомат График")
    col1, col2 = st.columns(2)
    with col1:
        x = st.selectbox("X тэнхлэг", df.columns)
    with col2:
        y = st.selectbox("Y тэнхлэг", df.columns, index=1)
    
    chart_type = st.radio("Графикийн төрөл", ["Бар", "Шугам", "Цэг", "Pie"], horizontal=True)
    
    if chart_type == "Бар":
        fig = px.bar(df, x=x, y=y, title=f"{y} vs {x}")
    elif chart_type == "Шугам":
        fig = px.line(df, x=x, y=y, title=f"{y} vs {x}")
    elif chart_type == "Цэг":
        fig = px.scatter(df, x=x, y=y, title=f"{y} vs {x}")
    else:
        fig = px.pie(df, names=x, values=y, title=f"{y} хуваарилалт")
    
    st.plotly_chart(fig, use_container_width=True)

# ========================== AI АНАЛИЗ ==========================
if st.button("🔥 Бүрэн Гүнзгий Анализ Хийх", type="primary"):
    with st.spinner("AI бодож байна... (Gemini 2.5 + Groq Llama 4)"):
        
        if isinstance(df_or_text, pd.DataFrame):
            data_summary = f"""
            Файл: {uploaded_file.name}
            Мөр: {len(df)}
            Багана: {list(df.columns)}
            Эхний 5 мөр:\n{df.head().to_string()}
            """
        else:
            data_summary = f"Текст файл:\n{df_or_text[:2000]}..."

        prompt = f"""
        Чи мэргэжлийн Data Analyst. Дараах өгөгдлийг маш нарийн шинжил:

        {data_summary}

        Дараахыг Монгол хэл дээр тодорхой, мэргэжлийн түвшинд хариул:
        1. Гол insights (3-5 гол зүйл)
        2. Тренд ба хэв маяг
        3. Статистик дүн (дундаж, хамгийн их/бага, холбоо)
        4. Бизнес/практик зөвлөмж (3-4 зөвлөмж)
        5. Цаашид юуг судлахыг зөвлө
        """

        # Модел сонголт
        if "Gemini" in model_choice and gemini_client:
            response = gemini_client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[prompt]
            )
            result = response.text
        else:
            response = groq_client.chat.completions.create(
                model="llama-4-70b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=4000
            )
            result = response.choices[0].message.content

        st.markdown("### 📋 AI-ийн Бүрэн Дүгнэлт")
        st.markdown(result)

        # Татаж авах
        st.download_button(
            "📥 Дүгнэлтийг татаж авах",
            result,
            file_name=f"AI_Analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

st.caption("© 2026 Эцсийн шинэчлэгдсэн хувилбар • Gemini 2.5 + Groq Llama 4 • Автомат график + гүнзгий анализ")
