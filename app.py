# =============================================================================
# Groq AI Аналитик – БҮТЭН КОД (API key шаардахгүй хувилбар)
# 2026 оны 3-р сарын байдлаар
# =============================================================================
# Энэ хувилбарт:
#   - Groq, Gemini, YouTube API, HuggingFace API-г бүгдийг устгасан
#   - Үлдсэн зөвхөн локал ажилладаг, интернет шаардахгүй функцууд
#   - Зураг үүсгэх, TTS, транскрипц, YouTube metadata-г устгасан
#   - Үлдсэн: чат, файл унших + энгийн дүгнэлт, URL текст унших
# =============================================================================

import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image
import base64
import io
import requests
from bs4 import BeautifulSoup
import re

# =============================================================================
# ТОХИРГОО
# =============================================================================
st.set_page_config(
    page_title="AI Аналитик (Offline)",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS – энгийн, мобайлд тохирсон
st.markdown("""
<style>
    .stChatMessage { font-size: 16px; line-height: 1.6; }
    .stChatInputContainer textarea { font-size: 16px; }
    .stButton > button { font-size: 16px; padding: 12px 20px; border-radius: 12px; width: 100%; }
    @media (max-width: 768px) {
        .main .block-container { padding: 1rem 0.5rem; }
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# СИСТЕМ ПРОМПТ (локал симуляци – жинхэнэ LLM байхгүй тул placeholder)
# =============================================================================
SYSTEM_PROMPT = """Чи Монгол хэлний туслах. Дараах дүрмийг дага:
1. Зөвхөн цэвэр Монгол хэлээр хариул
2. Шууд хариул, өөрийгөө танилцуулахгүй
3. Мэдэхгүй зүйлээ зохиохгүй
4. Товч, ойлгомжтой бай"""

# =============================================================================
# ФУНКЦҮҮД – API-гүй хувилбар
# =============================================================================
def is_mongolian(text):
    mongolian_chars = set("абвгдеёжзийклмноөпрстуүфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОӨПРСТУҮФХЦЧШЩЪЫЬЭЮЯ")
    count = sum(1 for c in text if c in mongolian_chars)
    return count / max(len(text), 1) > 0.3

def simple_response(text):
    """Жинхэнэ LLM байхгүй тул placeholder хариу – та эндээс өөрийн логик нэмж болно"""
    if len(text) < 10:
        return "Асуулт маш богино байна. Илүү дэлгэрэнгүй бичнэ үү."
    
    if "сайн байна уу" in text.lower() or "сайн уу" in text.lower():
        return "Сайн байна уу! Ямар тусламж хэрэгтэй вэ?"
    
    if is_mongolian(text):
        return f"Таны асуулт: {text}\n\nХариулт: Энэ бол миний энгийн placeholder хариу. Жинхэнэ LLM-гүй учраас ийм байна."
    else:
        return "Энэ текст Монгол биш байна. Монгол хэл дээр асуулт бичнэ үү."

def extract_url(text):
    pattern = r'https?://[^\s]+'
    urls = re.findall(pattern, text)
    return urls[0] if urls else None

def read_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, timeout=8)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Жижиг цэвэрлэгээ
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        
        title = soup.title.string.strip() if soup.title else "Гарчиг байхгүй"
        text = "\n".join([l.strip() for l in soup.get_text(separator="\n").split("\n") if len(l.strip()) > 20])
        
        return "text", f"Гарчиг: {title}\n\n{text[:4000]}"
    except Exception as e:
        return "error", f"URL уншихад алдаа: {str(e)}"

def read_file_content(file):
    try:
        name = file.name.lower()
        if name.endswith('.pdf'):
            pdf = PdfReader(file)
            text = " ".join([p.extract_text() or "" for p in pdf.pages])
            return "text", text[:5000]
        elif name.endswith('.docx'):
            doc = docx.Document(file)
            text = " ".join([p.text for p in doc.paragraphs])
            return "text", text[:5000]
        elif name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
            return "text", f"Өгөгдлийн хүснэгт (эхний 10 мөр):\n{df.head(10).to_string()}"
        elif name.endswith('.xlsx'):
            df = pd.read_excel(file)
            return "text", f"Өгөгдлийн хүснэгт (эхний 10 мөр):\n{df.head(10).to_string()}"
        elif name.endswith(('.png', '.jpg', '.jpeg')):
            img = PIL.Image.open(file)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return "image", base64.b64encode(buf.getvalue()).decode('utf-8')
        else:
            return "text", "Файлын форматыг дэмждэггүй."
    except Exception as e:
        return "error", f"Файл уншихад алдаа: {str(e)}"

# =============================================================================
# UI – 3 таб болгосон (API-гүй тул дуу, зураг үүсгэх хасаж)
# =============================================================================
st.title("🧠 AI Аналитик (Offline хувилбар)")

tab1, tab2, tab3 = st.tabs(["💬 Чат", "🌐 URL унших", "📁 Файл шинжлэх"])

# Session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================================================================
# ТАБ 1: ЧАТ
# =============================================================================
with tab1:
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.rerun()

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Асуулт бичнэ үү эсвэл URL оруулна уу..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Бодож байна..."):
                # URL илрүүлэх
                url = extract_url(prompt)
                if url:
                    type_, content = read_url(url)
                    if type_ == "error":
                        answer = content
                    else:
                        answer = simple_response(f"URL агуулга:\n{content[:2000]}\n\nАсуулт: {prompt.replace(url, '').strip() or 'Энэ агуулгыг тайлбарла'}")
                else:
                    answer = simple_response(prompt)

                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

# =============================================================================
# ТАБ 2: URL унших
# =============================================================================
with tab2:
    st.subheader("Вэб хуудас эсвэл YouTube холбоос унших")
    url_input = st.text_input("URL оруулна уу", placeholder="https://example.com эсвэл https://youtu.be/...")
    
    if st.button("Унших"):
        if url_input:
            with st.spinner("Уншиж байна..."):
                type_, content = read_url(url_input)
                if type_ == "error":
                    st.error(content)
                else:
                    st.markdown("**Гарчиг ба агуулга (эхний хэсэг):**\n\n" + content)
        else:
            st.warning("URL оруулна уу")

# =============================================================================
# ТАБ 3: ФАЙЛ ШИНЖЛЭХ
# =============================================================================
with tab3:
    st.subheader("PDF, Word, Excel, CSV, Зураг оруулж шинжлэх")
    uploaded = st.file_uploader("Файл сонгоно уу", type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg'])
    
    if uploaded is not None:
        with st.spinner("Уншиж шинжилж байна..."):
            ftype, data = read_file_content(uploaded)
            if ftype == "error":
                st.error(data)
            elif ftype == "image":
                st.image(base64.b64decode(data), caption="Оруулсан зураг")
                st.info("Зураг уншсан. Тайлбар өгөх LLM байхгүй тул энэ хүртэл.")
            else:
                st.markdown("**Файлын агуулга (эхний хэсэг):**\n\n" + data)
                st.info("Энгийн дүгнэлт: " + simple_response(data[:500]))

# =============================================================================
# Footer
# =============================================================================
st.markdown("---")
st.caption("Энэ хувилбар бүрэн локал ажилладаг (API key шаардлагагүй). Жинхэнэ LLM-гүй тул хариулт энгийн. Та өөрийн LLM-г нэмж болно.")
