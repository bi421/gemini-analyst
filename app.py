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
import re

# 1. Тохиргоо
st.set_page_config(page_title="Groq Analyst Pro", layout="wide")

client = None
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())

SYSTEM_PROMPT = {
    "role": "system",
    "content": """Чи Монгол хэлний туслах юм. Дараах дүрмийг заавал дагах:
1. ЗӨВХӨН цэвэр Монгол хэлээр хариул
2. Өөрийгөө танилцуулахгүй, шууд хариул
3. Мэдэхгүй зүйлийг зохиохгүй, үнэнийг хэл
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
            max_tokens=2048, temperature=0.3,
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

def extract_url(text):
    """Текстээс URL олох"""
    pattern = r'https?://[^\s]+'
    urls = re.findall(pattern, text)
    return urls[0] if urls else None

def read_youtube(url):
    """YouTube видеоны мэдээлэл авах"""
    try:
        # Video ID авах
        if "youtu.be" in url:
            video_id = url.split("/")[-1].split("?")[0]
        elif "v=" in url:
            video_id = url.split("v=")[-1].split("&")[0]
        else:
            return None, "YouTube видео ID олдсонгүй."

        # 1. Transcript авахыг оролдох
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["mn", "en", "ru"])
            transcript_text = " ".join([t["text"] for t in transcript_list])
            return "transcript", transcript_text[:6000]
        except:
            pass

        # 2. oEmbed API-аар гарчиг, тайлбар авах
        oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        r = requests.get(oembed_url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            title = data.get("title", "")
            author = data.get("author_name", "")
            return "meta", f"Видеоны гарчиг: {title}\nКанал: {author}\n\nТранскрипц байхгүй тул зөвхөн гарчиг болон каналын мэдээллээр хариулна."

        return None, "YouTube видеоны мэдээлэл авч чадсангүй."
    except Exception as e:
        return None, f"YouTube алдаа: {e}"

def read_url(url):
    """URL-ийн агуулга унших"""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

        # YouTube
        if "youtube.com" in url or "youtu.be" in url:
            dtype, data = read_youtube(url)
            if dtype:
                return dtype, data
            return "error", data

        # PDF
        if url.lower().endswith('.pdf'):
            r = requests.get(url, headers=headers, timeout=10)
            pdf = PdfReader(io.BytesIO(r.content))
            text = " ".join([p.extract_text() or "" for p in pdf.pages])
            return "text", text[:6000]

        # Веб хуудас
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title else ""
        text = soup.get_text(separator="\n", strip=True)
        text = "\n".join([l for l in text.split("\n") if len(l.strip()) > 20])
        return "text", f"Гарчиг: {title}\n\n{text[:5000]}"

    except Exception as e:
        return "error", f"URL уншихад алдаа: {e}"

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

def auto_analyze(file):
    if not client:
        return
    file_type, file_data = read_file_content(file)
    with st.spinner("🔍 Шинжилж байна..."):
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

# UI - Sidebar
with st.sidebar:
    st.header("📁 Файл Оруулах")
    uploaded_file = st.file_uploader(
        "Файл оруулахад автоматаар шинжилнэ",
        type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg', 'mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm'],
        key="file_uploader"
    )
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.session_state.last_analyzed = None
        st.session_state.url_content = None
        st.rerun()

# Үндсэн хэсэг
st.title("🧠 Groq Ухаалаг Аналитик")
st.caption("💡 URL шинжлэхийн тулд чат дотор шууд холбоосоо бичнэ үү")

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

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Чат
if prompt := st.chat_input("Асуулт бичнэ үү эсвэл URL оруулна уу..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            try:
                if not client:
                    st.error("🔑 GROQ_API_KEY байхгүй!")
                    st.stop()

                # URL илэрсэн эсэх шалгах
                detected_url = extract_url(prompt)
                
                if detected_url:
                    with st.spinner(f"🌐 URL уншиж байна: {detected_url}"):
                        url_type, url_data = read_url(detected_url)
                    
                    if url_type == "error":
                        answer = f"❌ {url_data}"
                    else:
                        st.session_state.url_content = url_data
                        # URL агуулгыг шинжлэх
                        user_question = prompt.replace(detected_url, "").strip()
                        if not user_question:
                            user_question = "Энэ агуулгыг дэлгэрэнгүй шинжилж дүгнэлт өг."
                        
                        if url_type == "transcript":
                            context = f"YouTube видеоны транскрипц:\n{url_data}"
                        elif url_type == "meta":
                            context = url_data
                        else:
                            context = f"Вэб хуудасны агуулга:\n{url_data}"
                        
                        answer = get_answer([
                            SYSTEM_PROMPT,
                            {"role": "user", "content": f"{context}\n\nАсуулт: {user_question}"}
                        ])

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
                    elif file_type == "text":
                        history = [SYSTEM_PROMPT] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                        history.append({"role": "user", "content": f"Файлын агуулга:\n{file_data[:3000]}\n\nАсуулт: {prompt}"})
                        answer = get_answer(history)
                    else:
                        answer = "Файлын төрөл дэмжигдэхгүй байна."

                elif st.session_state.url_content:
                    history = [SYSTEM_PROMPT] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                    history.append({"role": "user", "content": f"Агуулга:\n{st.session_state.url_content[:3000]}\n\nАсуулт: {prompt}"})
                    answer = get_answer(history)

                else:
                    history = [SYSTEM_PROMPT] + [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
                    history.append({"role": "user", "content": prompt})
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
