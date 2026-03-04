import streamlit as st
from groq import Groq
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image
import base64
import io
import requests
from bs4 import BeautifulSoup
import urllib.parse

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Groq Analyst Pro", layout="wide")

# 2. API Key тохиргоо
client = None
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())

# System prompt
SYSTEM_PROMPT = {
    "role": "system",
    "content": """Чи Монгол хэлний туслах юм. Дараах дүрмийг заавал дагах:
1. ЗӨВХӨН цэвэр Монгол хэлээр хариул — англи, орос үг огт хэрэглэхгүй
2. Өөрийгөө танилцуулахгүй, шууд асуултад хариул
3. Техникийн нэр томьёог Монгол хэлээр тайлбарла
4. Товч, ойлгомжтой байлга"""
}

def translate_to_mongolian(text):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Өгсөн текстийг зөвхөн Монгол хэл рүү орчуул. Нэмэлт тайлбаргүй."},
                {"role": "user", "content": f"Монгол хэл рүү орчуул:\n\n{text}"}
            ],
            max_tokens=2048,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except:
        return text

def is_mongolian(text):
    mongolian_chars = set("абвгдеёжзийклмноөпрстуүфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОӨПРСТУҮФХЦЧШЩЪЫЬЭЮЯ")
    count = sum(1 for c in text if c in mongolian_chars)
    return count / max(len(text), 1) > 0.3

def get_answer(messages, max_tokens=2048):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.7,
    )
    answer = response.choices[0].message.content
    if not is_mongolian(answer):
        answer = translate_to_mongolian(answer)
    return answer

# 3. URL унших функц
def read_url_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        
        # YouTube
        if "youtube.com" in url or "youtu.be" in url:
            return ("youtube", f"YouTube холбоос: {url}\nВидеоны гарчиг болон агуулгыг шинжлэнэ үү.")
        
        # PDF URL
        if url.endswith('.pdf'):
            response = requests.get(url, headers=headers, timeout=10)
            from io import BytesIO
            pdf_file = BytesIO(response.content)
            text = " ".join([p.extract_text() or "" for p in PdfReader(pdf_file).pages])
            return ("text", text[:5000])
        
        # Ердийн веб хуудас
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Хэрэггүй tag устгах
        for tag in soup(["script", "style", "nav", "footer", "header", "ads"]):
            tag.decompose()
        
        # Гол текст авах
        title = soup.title.string if soup.title else ""
        text = soup.get_text(separator="\n", strip=True)
        text = "\n".join([line for line in text.split("\n") if len(line.strip()) > 30])
        
        return ("text", f"Гарчиг: {title}\n\n{text[:5000]}")
    
    except Exception as e:
        return ("error", f"URL уншихад алдаа: {e}")

# 4. Файл унших функц
def read_file_content(file):
    try:
        if file.name.endswith('.pdf'):
            return ("text", " ".join([p.extract_text() or "" for p in PdfReader(file).pages]))
        elif file.name.endswith('.docx'):
            return ("text", " ".join([p.text for p in docx.Document(file).paragraphs]))
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
            return ("text", f"Өгөгдлийн хүснэгт:\n{df.to_string()}")
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
            return ("text", f"Өгөгдлийн хүснэгт:\n{df.to_string()}")
        elif file.name.endswith(('.png', '.jpg', '.jpeg')):
            img = PIL.Image.open(file)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
            return ("image", b64)
        elif file.name.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm')):
            return ("audio", file)
    except Exception as e:
        return ("error", f"Файл уншихад алдаа: {e}")
    return ("text", "")

# 5. Автомат шинжилгээ
def auto_analyze(file):
    if not client:
        return
    file_type, file_data = read_file_content(file)
    with st.spinner("🔍 Автоматаар шинжилж байна..."):
        try:
            if file_type == "audio":
                transcription = client.audio.transcriptions.create(
                    file=(file.name, file_data.read()),
                    model="whisper-large-v3",
                    response_format="text"
                )
                st.info(f"📝 Транскрипц:\n{transcription}")
                answer = get_answer([SYSTEM_PROMPT, {"role": "user", "content": f"Дараах транскрипцийг товч дүгнэ:\n{transcription}"}])
            elif file_type == "image":
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{file_data}"}},
                        {"type": "text", "text": "Энэ зургийг дэлгэрэнгүй Монгол хэлээр тайлбарла."}
                    ]}],
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content
                if not is_mongolian(answer):
                    answer = translate_to_mongolian(answer)
            elif file_type == "text":
                answer = get_answer([SYSTEM_PROMPT, {"role": "user", "content": f"Дараах өгөгдлийг шинжилж товч дүгнэлт өг:\n\n{file_data[:3000]}"}])
            elif file_type == "error":
                st.error(file_data)
                return
            st.session_state.messages.append({"role": "assistant", "content": f"📊 **Автомат шинжилгээ:**\n\n{answer}"})
        except Exception as e:
            st.error(f"❌ Алдаа: {e}")

# 6. UI - Sidebar
with st.sidebar:
    st.header("📁 Файл Оруулах")
    uploaded_file = st.file_uploader(
        "Файл оруулахад автоматаар шинжилнэ",
        type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg', 'mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm'],
        key="file_uploader"
    )
    
    st.header("🌐 URL Шинжилгээ")
    url_input = st.text_input("Веб хаяг оруулах", placeholder="https://...")
    analyze_url_btn = st.button("🔍 URL Шинжлэх")
    
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.session_state.last_analyzed = None
        st.rerun()

# 7. UI - Үндсэн хэсэг
st.title("🧠 Groq Ухаалаг Аналитик")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_analyzed" not in st.session_state:
    st.session_state.last_analyzed = None
if "url_content" not in st.session_state:
    st.session_state.url_content = None

# Файл автомат шинжлэх
if uploaded_file is not None:
    if st.session_state.last_analyzed != uploaded_file.name:
        st.session_state.last_analyzed = uploaded_file.name
        st.session_state.url_content = None
        auto_analyze(uploaded_file)
        st.rerun()

# URL шинжлэх
if analyze_url_btn and url_input:
    with st.spinner("🌐 URL уншиж байна..."):
        url_type, url_data = read_url_content(url_input)
        if url_type == "error":
            st.error(url_data)
        else:
            st.session_state.url_content = url_data
            answer = get_answer([
                SYSTEM_PROMPT,
                {"role": "user", "content": f"Дараах вэб хуудасны агуулгыг шинжилж товч дүгнэлт өг:\n\n{url_data}"}
            ])
            st.session_state.messages.append({"role": "assistant", "content": f"🌐 **URL шинжилгээ: {url_input}**\n\n{answer}"})
            st.rerun()

# Чат харуулах
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 8. Чат
if prompt := st.chat_input("Асуулт бичнэ үү..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            try:
                if not client:
                    st.error("🔑 GROQ_API_KEY байхгүй!")
                    st.stop()

                # Контекст тодорхойлох
                context = ""
                if st.session_state.url_content:
                    context = f"Вэб хуудасны агуулга:\n{st.session_state.url_content[:3000]}"
                elif uploaded_file is not None:
                    file_type, file_data = read_file_content(uploaded_file)
                    if file_type == "image":
                        response = client.chat.completions.create(
                            model="meta-llama/llama-4-scout-17b-16e-instruct",
                            messages=[{"role": "user", "content": [
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{file_data}"}},
                                {"type": "text", "text": prompt}
                            ]}],
                            max_tokens=1024,
                        )
                        answer = response.choices[0].message.content
                        if not is_mongolian(answer):
                            answer = translate_to_mongolian(answer)
                        st.markdown(answer)
                        st.session_state.messages.append({"role": "assistant", "content": answer})
                        st.stop()
                    elif file_type == "text":
                        context = f"Файлын агуулга:\n{file_data[:3000]}"

                history = [SYSTEM_PROMPT]
                for m in st.session_state.messages[:-1]:
                    history.append({"role": m["role"], "content": m["content"]})
                
                full_prompt = f"{context}\n\nАсуулт: {prompt}" if context else prompt
                history.append({"role": "user", "content": full_prompt})
                
                answer = get_answer(history)
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    st.warning("⏳ Хэт олон хүсэлт. Хэдэн секунд хүлээгээд дахин оролдоно уу.")
                elif "401" in error_msg:
                    st.error("🔑 API түлхүүр буруу байна.")
                else:
                    st.error(f"❌ Алдаа: {e}")
