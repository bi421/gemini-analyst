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
from collections import Counter
from urllib.parse import urlparse

# ==============================
# CONFIG
# ==============================

st.set_page_config(
    page_title="AI Data Analyst",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stMetric {background-color: #F0F2F6; padding: 15px; border-radius: 10px;}
    .stTabs [data-baseweb="tab-list"] {gap: 24px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap;}
</style>
""", unsafe_allow_html=True)

st.title("🧠 AI Data Analyst Platform")
st.caption("Өгөгдөл, баримт бичиг, вэб хуудаснаAI дүн шинжилгээ хийх систем")

# ==============================
# SESSION STATE INITIALIZATION
# ==============================

if "df_data" not in st.session_state:
    st.session_state.df_data = None
if "text_data" not in st.session_state:
    st.session_state.text_data = None
if "file_type" not in st.session_state:
    st.session_state.file_type = None # "dataframe" or "text"
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================
# FUNCTIONS
# ==============================

def analyze_link(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "No Title"
        text = " ".join(p.text for p in soup.find_all("p"))
        
        return {
            "title": title,
            "words": len(text.split()),
            "links": len(soup.find_all("a")),
            "images": len(soup.find_all("img")),
            "text_preview": text[:1000] + "..." if len(text) > 1000 else text,
            "status": "success"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def read_file(file):
    name = file.name.lower()
    try:
        if name.endswith((".csv", ".xlsx")):
            # Excel engine openpyxl required
            if name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            return df, "dataframe"
            
        elif name.endswith(".json"):
            data = json.load(file)
            df = pd.json_normalize(data)
            return df, "dataframe"
            
        elif name.endswith(".txt"):
            return file.read().decode("utf-8"), "text"
            
        elif name.endswith(".pdf"):
            reader = PdfReader(file)
            text = "".join([p.extract_text() or "" for p in reader.pages])
            return text, "text"
            
        elif name.endswith(".docx"):
            doc = docx.Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
            return text, "text"
            
        else:
            return None, "unsupported"
    except Exception as e:
        st.error(f"Файл уншихад алдаа гарлаа: {e}")
        return None, "error"

def generate_ai_response(prompt, df, text):
    """Simple rule-based AI response logic"""
    response = ""
    
    # Logic for Dataframes
    if df is not None:
        prompt_lower = prompt.lower()
        
        if "row" in prompt_lower or "мөр" in prompt_lower:
            response = f"📊 **Dataframe-д нийт {len(df)} мөр (row) байна.**"
        elif "column" in prompt_lower or "багана" in prompt_lower:
            cols = list(df.columns)
            response = f"📋 **Дараах баганууд байна:**\n`{', '.join(cols)}`"
        elif "describe" in prompt_lower or "тайлбар" in prompt_lower or "статистик" in prompt_lower:
            buf = io.StringIO()
            df.describe().to_csv(buf)
            response = f"📈 **Статистик дүн:**\n```\n{buf.getvalue()}\n```"
        elif "head" in prompt_lower or "эхэн" in prompt_lower:
            buf = io.StringIO()
            df.head().to_csv(buf)
            response = f"🔝 **Эхний 5 мөр:**\n```\n{buf.getvalue()}\n```"
        else:
            response = (
                f"Таны дата {len(df)} мөр, {len(df.columns)} баганатай. "
                "Би түүнээс `статистик`, `баганууд`, `эхний мөрүүд`-ийн талаар дэлгэрэнгүй хэлж өгч болно."
            )
            
    # Logic for Text
    elif text is not None:
        word_count = len(text.split())
        # Simple keyword extraction
        words = re.findall(r'\w+', text.lower())
        common_words = Counter(words).most_common(5)
        
        response = (
            f"📄 Энэ нь текст файл байна. Үгсийн тоо: **{word_count}**.\n"
            f"🔑 **Хамгийн их давтагдах 5 үг:** {', '.join([w[0] for w in common_words])}.\n\n"
            "Та текстээс `summary` эсвэл `тайлбар` гэж асууж болно."
        )
    else:
        response = "👋 Сайн байна уу? Дatasets эсвэл линк оруулвал би дүн шинжилгээ хийхэд тань туслах болно."
        
    return response

# ==============================
# SIDEBAR
# ==============================

with st.sidebar:
    st.header("⚙️ Тохиргоо")
    if st.session_state.df_data is not None:
        st.success("✅ Файл уншигдсан")
        st.write(f"Төрөл: DataFrame ({len(st.session_state.df_data)} rows)")
    elif st.session_state.text_data is not None:
        st.success("✅ Файл уншигдсан")
        st.write(f"Төрөл: Text ({len(st.session_state.text_data)} chars)")
    else:
        st.info("📂 Файл эсвэл линк оруулна уу")

# ==============================
# MAIN TABS
# ==============================

tab1, tab2, tab3 = st.tabs(["🌐 Link анализ", "📂 File унших", "💬 AI чат"])

# --- TAB 1: LINK ANALYZER ---
with tab1:
    st.subheader("Вэб хуудасны шинжилгээ")
    url = st.text_input("URL оруулна уу:", placeholder="https://example.com")
    
    if st.button("Анализ хийх", use_container_width=True):
        if url:
            with st.spinner("Түүвэрлэж байна..."):
                result = analyze_link(url)
            
            if result["status"] == "success":
                col1, col2, col3 = st.columns(3)
                col1.metric("Үгс", result["words"])
                col2.metric("Линкүүд", result["links"])
                col3.metric="Зураг", result["images"]
                
                st.write("### 📌 Title")
                st.info(result["title"])
                
                st.write("### 📝 Content Preview")
                st.text_area("Text content", result["text_preview"], height=200)
            else:
                st.error(f"Алдаа: {result['message']}")
        else:
            st.warning("URL оруулна уу.")

# --- TAB 2: FILE UPLOAD ---
with tab2:
    st.subheader("Файл оруулж унших")
    uploaded_file = st.file_uploader(
        "Файлаа сонгоно уу (CSV, Excel, JSON, PDF, DOCX, TXT)",
        type=["csv", "xlsx", "json", "pdf", "docx", "txt"]
    )
    
    if uploaded_file:
        content, f_type = read_file(uploaded_file)
        
        if f_type == "dataframe":
            st.session_state.df_data = content
            st.session_state.text_data = None
            st.session_state.file_type = "dataframe"
            
            df = content
            st.success(f"Амжилттай уншлаа: {len(df)} мөр, {len(df.columns)} багана.")
            
            # Data Preview
            with st.expander("👁️ Өгөгдөл харах", expanded=True):
                st.dataframe(df, use_container_width=True)
                
            # Analytics Section
            st.write("### 📊 Визуалжлага")
            col_chart, col_col = st.columns([2, 1])
            
            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            all_cols = df.columns.tolist()
            
            if len(numeric_cols) > 0:
                with col_col:
                    chart_type = st.selectbox("Чартын төрөл", ["Histogram", "Scatter", "Line", "Bar"])
                    x_axis = st.selectbox("X тэнхлэг (Нэр/Огноо)", all_cols)
                    y_axis = st.selectbox("Y тэнхлэг (Тоо)", numeric_cols)
                    color_enc = st.selectbox("Өнгөөр ялгах", [None] + all_cols)

                with col_chart:
                    fig = None
                    if chart_type == "Histogram":
                        fig = px.histogram(df, x=y_axis, color=color_enc)
                    elif chart_type == "Scatter":
                        fig = px.scatter(df, x=x_axis, y=y_axis, color=color_enc)
                    elif chart_type == "Line":
                        fig = px.line(df, x=x_axis, y=y_axis, color=color_enc)
                    elif chart_type == "Bar":
                        fig = px.bar(df, x=x_axis, y=y_axis, color=color_enc)
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Тоон багана (numeric column) олдсонгүй, график зурах боломжгүй.")

        elif f_type == "text":
            st.session_state.text_data = content
            st.session_state.df_data = None
            st.session_state.file_type = "text"
            
            st.success("Текст файл уншигдлаа.")
            st.text_area("Агуулга", content[:5000] + "..." if len(content) > 5000 else content, height=300)
            
            # Simple Text Analysis
            words = re.findall(r'\w+', content.lower())
            if words:
                common = Counter(words).most_common(10)
                st.write("### 🔑 Түгээлтийн дүн (Top 10 words)")
                df_words = pd.DataFrame(common, columns=["Word", "Count"])
                st.bar_chart(df_words.set_index("Word"))

        elif f_type == "error":
            pass
        else:
            st.error("Дэмжихгүй файлын формат.")

# --- TAB 3: AI CHAT ---
with tab3:
    st.subheader("Өгөгдөлтэй ярилцах")
    
    # Chat Container
    chat_container = st.container()
    
    # Display chat history
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    
    # Chat Input
    prompt = st.chat_input("Асуултаа бичих...")
    
    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        
        # Generate AI response
        with st.chat_message("assistant"):
            with st.spinner("Боловсруулж байна..."):
                response = generate_ai_response(
                    prompt, 
                    st.session_state.df_data, 
                    st.session_state.text_data
                )
                st.markdown(response)
        
        # Add AI response to history
        st.session_state.messages.append({"role": "assistant", "content": response})

# ==============================
# FOOTER
# ==============================
st.divider()
st.caption("© 2026 AI Data Analyst Platform | Enhanced Version")
