import streamlit as st
from groq import Groq
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image
import base64
import io

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Groq Analyst Pro", layout="wide")

# 2. API Key тохиргоо
client = None
if "GROQ_API_KEY" in st.secrets:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"].strip())

# System prompt — хатуу Монгол хэлээр
SYSTEM_PROMPT = {
    "role": "system",
    "content": """Чи Монгол хэлний туслах юм. Дараах дүрмийг заавал дагах:
1. ЗӨВХӨН цэвэр Монгол хэлээр хариул — англи, орос үг огт хэрэглэхгүй
2. "Би Монгол хэлээр ярих чадвартай" гэх мэт өөрийгөө танилцуулахгүй
3. Шууд асуултад хариул
4. Техникийн нэр томьёог Монгол хэлээр тайлбарла
5. Хариултын эхэнд "Мэдээж!", "Тийм!" гэх зэрэг богино баталгааны үг хэрэглэж болно"""
}

def translate_to_mongolian(text):
    """Хариултыг Монгол руу орчуулах"""
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Та орчуулагч юм. Өгсөн текстийг зөвхөн Монгол хэл рүү орчуул. Нэмэлт тайлбар, тайлбар бичихгүй. Зөвхөн орчуулга."},
                {"role": "user", "content": f"Дараах текстийг Монгол хэл рүү орчуул:\n\n{text}"}
            ],
            max_tokens=2048,
            temperature=0.3,
        )
        return response.choices[0].message.content
    except:
        return text

def is_mongolian(text):
    """Текст Монгол хэлтэй эсэхийг шалгах"""
    mongolian_chars = set("абвгдеёжзийклмноөпрстуүфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОӨПРСТУҮФХЦЧШЩЪЫЬЭЮЯ")
    count = sum(1 for c in text if c in mongolian_chars)
    return count / max(len(text), 1) > 0.3

# 3. Файл унших функц
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

def get_answer(messages, max_tokens=2048):
    """AI-аас хариулт авах + Монгол биш бол орчуулах"""
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

# 4. Автомат шинжилгээ функц
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
                answer = get_answer([
                    SYSTEM_PROMPT,
                    {"role": "user", "content": f"Дараах аудионы транскрипцийг товч дүгнэ:\n{transcription}"}
                ])

            elif file_type == "image":
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/png;base64,{file_data}"}},
                            {"type": "text", "text": "Энэ зургийг дэлгэрэнгүй Монгол хэлээр тайлбарла."}
                        ]
                    }],
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content
                if not is_mongolian(answer):
                    answer = translate_to_mongolian(answer)

            elif file_type == "text":
                answer = get_answer([
                    SYSTEM_PROMPT,
                    {"role": "user", "content": f"Дараах өгөгдлийг шинжилж товч дүгнэлт өг:\n\n{file_data[:3000]}"}
                ])

            elif file_type == "error":
                st.error(file_data)
                return

            st.session_state.messages.append({
                "role": "assistant",
                "content": f"📊 **Автомат шинжилгээ:**\n\n{answer}"
            })

        except Exception as e:
            st.error(f"❌ Алдаа: {e}")

# 5. UI - Sidebar
with st.sidebar:
    st.header("📁 Файл Оруулах")
    uploaded_file = st.file_uploader(
        "Файл оруулахад автоматаар шинжилнэ",
        type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg',
              'mp3', 'wav', 'm4a', 'ogg', 'flac', 'webm'],
        key="file_uploader"
    )
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.session_state.last_analyzed = None
        st.rerun()

# 6. UI - Үндсэн хэсэг
st.title("🧠 Groq Ухаалаг Аналитик")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_analyzed" not in st.session_state:
    st.session_state.last_analyzed = None

if uploaded_file is not None:
    if st.session_state.last_analyzed != uploaded_file.name:
        st.session_state.last_analyzed = uploaded_file.name
        auto_analyze(uploaded_file)
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Чат ба Логик
if prompt := st.chat_input("Нэмэлт асуулт байвал энд бичнэ үү..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            try:
                if not client:
                    st.error("🔑 GROQ_API_KEY байхгүй!")
                    st.stop()

                if uploaded_file is not None:
                    file_type, file_data = read_file_content(uploaded_file)
                    if file_type == "image":
                        response = client.chat.completions.create(
                            model="meta-llama/llama-4-scout-17b-16e-instruct",
                            messages=[{
                                "role": "user",
                                "content": [
                                    {"type": "image_url",
                                     "image_url": {"url": f"data:image/png;base64,{file_data}"}},
                                    {"type": "text", "text": prompt}
                                ]
                            }],
                            max_tokens=1024,
                        )
                        answer = response.choices[0].message.content
                        if not is_mongolian(answer):
                            answer = translate_to_mongolian(answer)
                    elif file_type == "text":
                        history = [SYSTEM_PROMPT] + [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages[:-1]
                        ]
                        history.append({"role": "user", "content": f"Контекст:\n{file_data[:3000]}\n\nАсуулт: {prompt}"})
                        answer = get_answer(history)
                    else:
                        answer = "Файлын төрөл дэмжигдэхгүй байна."
                else:
                    history = [SYSTEM_PROMPT] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages[:-1]
                    ]
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
