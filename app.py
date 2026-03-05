import streamlit as st
from groq import Groq
from google import genai
from google.genai import types
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image
import base64
import io
import requests
from bs4 import BeautifulSoup
from gtts import gTTS
import re

# 1. Тохиргоо
st.set_page_config(
    page_title="Groq AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS
st.markdown("""
<style>
  html, body, [class*="css"] { font-size: 16px !important; }
  .stChatMessage { font-size: 16px !important; line-height: 1.6 !important; }
  .stChatInputContainer textarea { font-size: 16px !important; padding: 12px !important; }
  .stButton > button { font-size: 16px !important; padding: 12px 20px !important; border-radius: 12px !important; width: 100% !important; }
  h1 { font-size: 24px !important; }
  h2 { font-size: 20px !important; }
  h3 { font-size: 18px !important; }
  .stFileUploader label { font-size: 15px !important; }
  .stSelectbox label, .stSelectbox div { font-size: 15px !important; }
  .stTextInput input, .stTextArea textarea { font-size: 16px !important; }
  .stTabs [data-baseweb="tab"] { font-size: 15px !important; padding: 10px 16px !important; }
  .stCaption { font-size: 14px !important; }
  @media (max-width: 768px) {
    .main .block-container { padding: 1rem 0.5rem !important; max-width: 100% !important; }
    h1 { font-size: 22px !important; }
    .stButton > button { font-size: 15px !important; padding: 10px 16px !important; }
  }
</style>
""", unsafe_allow_html=True)

# 2. API Key тохиргоо
client = None
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())

gemini_client = None
if "GEMINI_API_KEY" in st.secrets:
    try:
        gemini_client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"].strip())
    except:
        pass

GEMINI_FLASH = "gemini-2.0-flash"
GEMINI_LITE = "gemini-2.0-flash-lite"

YOUTUBE_API_KEY = st.secrets.get("YOUTUBE_API_KEY", "")
HF_TOKEN = st.secrets.get("HF_TOKEN", "")

SYSTEM_PROMPT = {
    "role": "system",
    "content": """Чи Монгол хэлний туслах юм. Дараах дүрмийг заавал дагах:
1. ЗӨВХӨН цэвэр Монгол хэлээр хариул
2. Өөрийгөө танилцуулахгүй, шууд хариул
3. Мэдэхгүй зүйлийг зохиохгүй, үнэнийг хэл
4. Товч, ойлгомжтой байлга"""
}

def translate_to_mongolian(text):
    # Flash Lite ашиглан хурдан орчуулга
    if gemini_client:
        try:
            response = gemini_client.models.generate_content(
                model=GEMINI_LITE,
                contents=[f"Энэ текстийг зөвхөн Монгол хэл рүү орчуул. Нэмэлт тайлбаргүй:\n\n{text}"]
            )
            return response.text
        except:
            pass
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
    pattern = r'https?://[^\s]+'
    urls = re.findall(pattern, text)
    return urls[0] if urls else None

def get_video_id(url):
    if "youtu.be" in url:
        return url.split("/")[-1].split("?")[0]
    elif "v=" in url:
        return url.split("v=")[-1].split("&")[0]
    return None

def read_youtube(url):
    video_id = get_video_id(url)
    if not video_id:
        return "error", "YouTube видео ID олдсонгүй."
    result = {}
    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
    if YOUTUBE_API_KEY:
        try:
            api_url = f"https://www.googleapis.com/youtube/v3/videos?id={video_id}&key={YOUTUBE_API_KEY}&part=snippet,statistics,contentDetails"
            r = requests.get(api_url, timeout=10)
            data = r.json()
            if data.get("items"):
                item = data["items"][0]
                snippet = item.get("snippet", {})
                stats = item.get("statistics", {})
                content = item.get("contentDetails", {})
                thumbnail_url = snippet.get("thumbnails", {}).get("maxres", {}).get("url", thumbnail_url)
                duration = content.get("duration", "").replace("PT","").replace("H"," цаг ").replace("M"," мин ").replace("S"," сек")
                result = {
                    "🎬 Гарчиг": snippet.get("title", ""),
                    "📺 Канал": snippet.get("channelTitle", ""),
                    "📅 Нийтэлсэн": snippet.get("publishedAt", "")[:10],
                    "🌐 Хэл": snippet.get("defaultAudioLanguage", "Тодорхойгүй"),
                    "⏱️ Үргэлжлэх": duration,
                    "👁️ Үзсэн": f"{int(stats.get('viewCount', 0)):,}",
                    "👍 Like": f"{int(stats.get('likeCount', 0)):,}",
                    "📝 Тайлбар": snippet.get("description", "")[:800],
                }
                channel_id = snippet.get("channelId", "")
                if channel_id:
                    ch_r = requests.get(f"https://www.googleapis.com/youtube/v3/channels?id={channel_id}&key={YOUTUBE_API_KEY}&part=snippet,statistics", timeout=10)
                    ch_data = ch_r.json()
                    if ch_data.get("items"):
                        ch = ch_data["items"][0]
                        result.update({
                            "🌍 Каналын улс": ch["snippet"].get("country", "Тодорхойгүй"),
                            "👥 Дагагчид": f"{int(ch['statistics'].get('subscriberCount', 0)):,}",
                        })
        except Exception as e:
            result["⚠️ Алдаа"] = str(e)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["mn", "en", "ru"])
        result["📜 Транскрипц"] = " ".join([t["text"] for t in transcript_list])[:4000]
    except:
        result["📜 Транскрипц"] = "Транскрипц байхгүй"
    if gemini_client:
        try:
            r = requests.get(thumbnail_url, timeout=10)
            img = PIL.Image.open(io.BytesIO(r.content))
            response = gemini_client.models.generate_content(
                model=GEMINI_FLASH,
                contents=["Энэ YouTube thumbnail зургийг Монгол хэлээр дэлгэрэнгүй тайлбарла.", img])
            result["🖼️ Thumbnail"] = response.text
        except:
            pass
    if not result:
        return "error", "YouTube мэдээлэл авч чадсангүй."
    return "youtube", "\n".join([f"{k}: {v}" for k, v in result.items()])

def read_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        if "youtube.com" in url or "youtu.be" in url:
            return read_youtube(url)
        if url.lower().endswith('.pdf'):
            r = requests.get(url, headers=headers, timeout=10)
            pdf = PdfReader(io.BytesIO(r.content))
            return "text", " ".join([p.extract_text() or "" for p in pdf.pages])[:6000]
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = r.apparent_encoding
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title else ""
        text = "\n".join([l for l in soup.get_text(separator="\n", strip=True).split("\n") if len(l.strip()) > 20])
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
            return ("text", f"Өгөгдлийн хүснэгт:\n{pd.read_excel(file).to_string()}")
        elif file.name.endswith(('.png', '.jpg', '.jpeg')):
            img = PIL.Image.open(file)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return ("image", base64.b64encode(buf.getvalue()).decode('utf-8'))
        elif file.name.endswith(('.mp3', '.wav', '.m4a', '.ogg', '.flac', '.webm')):
            return ("audio", file)
    except Exception as e:
        return ("error", f"Файл уншихад алдаа: {e}")
    return ("text", "")

# === ШИНЭ ФУНКЦҮҮД ===

def generate_lyrics(prompt):
    """Groq ашиглан дууны үг бичих"""
    if not client:
        return None, "GROQ_API_KEY байхгүй!"
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Чи мэргэжлийн дууны үг бичигч. Монгол хэлээр сэтгэл хөдлөлтэй, уянгалаг дууны үг бич."},
                {"role": "user", "content": f"""Дараах сэдвээр дуу бич:
Сэдэв: {prompt}
Хэлбэр: [Verse 1], [Chorus], [Verse 2], [Chorus], [Bridge], [Outro]
Хэл: Монгол
Уянгалаг, сэтгэл хөдлөлтэй байлга."""}
            ],
            max_tokens=1000, temperature=0.8
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Алдаа: {e}"

def generate_suno_prompt(theme, style, lyrics):
    """Suno-д тохирсон prompt үүсгэх"""
    if not client:
        return f"{style} song about {theme}", None
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Suno AI prompt expert. Create short, effective music prompts in English for Suno AI. Max 200 characters."},
                {"role": "user", "content": f"Create a Suno prompt for: Theme={theme}, Style={style}. Short English prompt only."}
            ],
            max_tokens=100, temperature=0.7
        )
        return response.choices[0].message.content.strip(), None
    except Exception as e:
        return f"{style}, {theme}", None

def generate_image(prompt):
    """Pollinations.AI ашиглан зураг үүсгэх — API key шаардахгүй!"""
    try:
        import urllib.parse
        encoded = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
        r = requests.get(url, timeout=60)
        if r.status_code == 200:
            return PIL.Image.open(io.BytesIO(r.content)), None
        return None, f"Алдаа: {r.status_code}"
    except Exception as e:
        return None, f"Алдаа: {e}"

def text_to_speech(text, lang="Монгол"):
    """HuggingFace MMS TTS - Монгол хэл дэмждэг"""
    lang_map = {
        "Монгол": ("facebook/mms-tts-khk", True),
        "Англи": ("facebook/mms-tts-eng", True),
        "Орос": ("facebook/mms-tts-rus", True),
        "Хятад": ("facebook/mms-tts-cmn", True),
    }
    model_id, use_hf = lang_map.get(lang, ("facebook/mms-tts-khk", True))
    
    # HuggingFace Inference API
    if use_hf:
        headers = {}
        if HF_TOKEN:
            headers["Authorization"] = f"Bearer {HF_TOKEN}"
        try:
            response = requests.post(
                f"https://api-inference.huggingface.co/models/{model_id}",
                headers=headers,
                json={"inputs": text},
                timeout=30
            )
            if response.status_code == 200:
                return response.content, None
            elif response.status_code == 503:
                return None, "Загвар ачаалж байна, 20 секунд хүлээгээд дахин оролдоно уу!"
            else:
                # gTTS fallback
                try:
                    fb_lang = {"Монгол": "ru", "Англи": "en", "Орос": "ru", "Хятад": "zh"}.get(lang, "ru")
                    tts = gTTS(text=text, lang=fb_lang, slow=False)
                    buf = io.BytesIO()
                    tts.write_to_fp(buf)
                    buf.seek(0)
                    return buf.getvalue(), None
                except:
                    return None, f"HF алдаа: {response.text}"
        except Exception as e:
            return None, f"Алдаа: {e}"
    return None, "Дэмжигдэхгүй хэл"

def edit_image_with_gemini(image, instruction):
    """Gemini-ээр зураг тайлбарлаж засварлах зааврыг гаргах"""
    if not gemini_client:
        return "GEMINI_API_KEY байхгүй байна!"
    try:
        response = gemini_client.models.generate_content(
            model=GEMINI_FLASH,
            contents=[f"Энэ зургийг дараах байдлаар засварлаж тайлбарла: {instruction}", image])
        return response.text
    except Exception as e:
        return f"Алдаа: {e}"

def auto_analyze(file):
    if not client:
        return
    file_type, file_data = read_file_content(file)
    with st.spinner("🔍 Шинжилж байна..."):
        try:
            if file_type == "audio":
                transcription = client.audio.transcriptions.create(
                    file=(file.name, file_data.read()), model="whisper-large-v3", response_format="text")
                st.info(f"📝 Транскрипц:\n{transcription}")
                answer = get_answer([SYSTEM_PROMPT, {"role": "user", "content": f"Дараах транскрипцийг товч дүгнэ:\n{transcription}"}])
            elif file_type == "image":
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{file_data}"}},
                        {"type": "text", "text": "Энэ зургийг дэлгэрэнгүй Монгол хэлээр тайлбарла."}
                    ]}], max_tokens=1024)
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

# === UI ===
st.title("🧠 Groq AI Аналитик")

# Tab UI
tab1, tab2, tab3, tab4 = st.tabs(["💬 Чат", "🎨 Зураг", "🔊 Дуу", "📁 Файл"])

# Session state
for key in ["messages", "last_analyzed", "url_content"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else None

# === ТАБ 1: ЧАТ ===
with tab1:
    if st.button("🧹 Чат цэвэрлэх", key="clear_chat"):
        st.session_state.messages = []
        st.session_state.url_content = None
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

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
                    detected_url = extract_url(prompt)
                    if detected_url:
                        with st.spinner("🌐 Уншиж байна..."):
                            url_type, url_data = read_url(detected_url)
                        if url_type == "error":
                            answer = f"❌ {url_data}"
                        else:
                            st.session_state.url_content = url_data
                            user_question = prompt.replace(detected_url, "").strip() or "Энэ агуулгыг дэлгэрэнгүй тайлбарла."
                            answer = get_answer([SYSTEM_PROMPT, {"role": "user", "content": f"{url_data}\n\nАсуулт: {user_question}"}], max_tokens=3000)
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
                    if "429" in str(e):
                        st.warning("⏳ Хэт олон хүсэлт. Хэдэн секунд хүлээгээд дахин оролдоно уу.")
                    elif "401" in str(e):
                        st.error("🔑 API түлхүүр буруу.")
                    else:
                        st.error(f"❌ Алдаа: {e}")

# === ТАБ 2: ЗУРАГ ===
with tab2:
    st.subheader("🎨 AI Зураг Бүтээгч")
    img_tab1, img_tab2 = st.tabs(["✨ Зураг үүсгэх", "🖌️ Зураг засварлах"])

    with img_tab1:
        st.caption("Pollinations AI ашиглана — API key шаардахгүй, үнэгүй, хязгааргүй!")
        img_prompt = st.text_area("Зургийн тайлбар бичнэ үү", placeholder="Монгол нутгийн үзэсгэлэнт байгаль, морьтой малчин...", height=100)
        if st.button("🎨 Зураг үүсгэх", key="gen_img"):
            if not img_prompt:
                st.warning("Тайлбар бичнэ үү!")
            else:
                with st.spinner("🎨 Зураг үүсгэж байна..."):
                    img, err = generate_image(img_prompt)
                    if img:
                        st.image(img, caption=img_prompt, use_container_width=True)
                        buf = io.BytesIO()
                        img.save(buf, format='PNG')
                        st.download_button("💾 Татаж авах", buf.getvalue(), "generated_image.png", "image/png")
                    else:
                        st.error(f"❌ {err}")

    with img_tab2:
        st.caption("Зураг оруулаад засварлах зааврыг AI өгнө")
        edit_file = st.file_uploader("Зураг оруулах", type=['png', 'jpg', 'jpeg'], key="edit_img")
        edit_instruction = st.text_input("Засварлах заавар", placeholder="Арын дэвсгэрийг цагаан болго, баруун дээд буланд лого нэм...")
        if st.button("🖌️ Засварлах", key="edit_img_btn"):
            if edit_file and edit_instruction:
                with st.spinner("🖌️ Засварлаж байна..."):
                    img = PIL.Image.open(edit_file)
                    st.image(img, caption="Оруулсан зураг", use_container_width=True)
                    result = edit_image_with_gemini(img, edit_instruction)
                    st.markdown(f"**AI зөвлөмж:**\n\n{result}")
            else:
                st.warning("Зураг болон заавар оруулна уу!")

# === ТАБ 3: ДУУ ===
with tab3:
    st.subheader("🔊 AI Дуу")
    audio_tab1, audio_tab2 = st.tabs(["🎤 Текст → Дуу (TTS)", "📝 Дуу → Текст"])

    with audio_tab1:
        st.caption("Google TTS ашиглан текстийг дуу болгоно — үнэгүй, API key шаардахгүй!")
        tts_text = st.text_area("Текст бичнэ үү", placeholder="Монгол хэлээр дуу болгох текстээ бичнэ үү...", height=150)
        st.caption("HuggingFace MMS AI ашиглана — Монгол хэл бүрэн дэмжигдэнэ!")
        lang_option = st.selectbox("Хэл", ["Монгол", "Англи", "Орос", "Хятад"])
        if st.button("🎤 Дуу үүсгэх", key="tts_btn"):
            if not tts_text:
                st.warning("Текст бичнэ үү!")
            else:
                with st.spinner("🎤 Дуу үүсгэж байна..."):
                    audio, err = text_to_speech(tts_text, lang_option)
                    if audio:
                        st.audio(audio, format='audio/mp3')
                        st.download_button("💾 Татаж авах", audio, "speech.mp3", "audio/mp3")
                    else:
                        st.error(f"❌ {err}")

    with audio_tab2:
        st.caption("Whisper AI ашиглан дуу/аудиог текст болгоно")
        audio_file = st.file_uploader("Аудио файл оруулах", type=['mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm'], key="audio_upload")
        if st.button("📝 Транскрипц хийх", key="transcribe_btn"):
            if not audio_file:
                st.warning("Аудио файл оруулна уу!")
            elif not client:
                st.error("🔑 GROQ_API_KEY байхгүй!")
            else:
                with st.spinner("📝 Транскрипц хийж байна..."):
                    try:
                        transcription = client.audio.transcriptions.create(
                            file=(audio_file.name, audio_file.read()),
                            model="whisper-large-v3", response_format="text")
                        st.text_area("Транскрипц:", transcription, height=200)
                        if st.button("🧠 AI-аар шинжлэх"):
                            answer = get_answer([SYSTEM_PROMPT, {"role": "user", "content": f"Дараах транскрипцийг шинжилж дүгнэлт өг:\n{transcription}"}])
                            st.markdown(answer)
                    except Exception as e:
                        st.error(f"❌ Алдаа: {e}")

# === ТАБ 4: ФАЙЛ ===
with tab4:
    st.subheader("📁 Файл Шинжилгээ")
    uploaded_file = st.file_uploader(
        "Файл оруулахад автоматаар шинжилнэ",
        type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg', 'mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm'],
        key="file_uploader"
    )
    if uploaded_file is not None:
        if st.session_state.last_analyzed != uploaded_file.name:
            st.session_state.last_analyzed = uploaded_file.name
            auto_analyze(uploaded_file)
            st.rerun()
    for message in st.session_state.messages:
        if "Автомат шинжилгээ" in message.get("content", ""):
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
    if uploaded_file and st.session_state.last_analyzed == uploaded_file.name:
        if follow_up := st.chat_input("Файлын талаар нэмэлт асуулт..."):
            st.session_state.messages.append({"role": "user", "content": follow_up})
            file_type, file_data = read_file_content(uploaded_file)
            if file_type == "text":
                answer = get_answer([SYSTEM_PROMPT, {"role": "user", "content": f"Файл:\n{file_data[:3000]}\n\nАсуулт: {follow_up}"}])
            else:
                answer = get_answer([SYSTEM_PROMPT, {"role": "user", "content": follow_up}])
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
