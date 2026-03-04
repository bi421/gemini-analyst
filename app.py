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
                prompt = f"Дараах аудионы транскрипцийг товч дүгнэ:\n{transcription}"
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content

            elif file_type == "image":
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image_url",
                             "image_url": {"url": f"data:image/png;base64,{file_data}"}},
                            {"type": "text", "text": "Энэ зургийг дэлгэрэнгүй тайлбарла. Юу харагдаж байна? Онцлог зүйлсийг дурьдаж өг."}
                        ]
                    }],
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content

            elif file_type == "text":
                prompt = f"Дараах өгөгдлийг шинжилж товч дүгнэлт өг. Гол мэдээллийг онцол:\n\n{file_data[:3000]}"
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024,
                )
                answer = response.choices[0].message.content

            elif file_type == "error":
                st.error(file_data)
                return

            # Чат руу нэм
            st.session_state.messages.append({"role": "assistant", "content": f"📊 **Автомат шинжилгээ:**\n\n{answer}"})

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

# Файл оруулангуут автоматаар шинжлэх
if uploaded_file is not None:
    if st.session_state.last_analyzed != uploaded_file.name:
        st.session_state.last_analyzed = uploaded_file.name
        auto_analyze(uploaded_file)
        st.rerun()

# Чат харуулах
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

                full_prompt = prompt
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
                    elif file_type == "text":
                        full_prompt = f"Контекст:\n{file_data[:3000]}\n\nАсуулт: {prompt}"
                        history = [{"role": m["role"], "content": m["content"]}
                                   for m in st.session_state.messages[:-1]]
                        history.append({"role": "user", "content": full_prompt})
                        response = client.chat.completions.create(
                            model="llama-3.3-70b-versatile",
                            messages=history,
                            max_tokens=2048,
                        )
                        answer = response.choices[0].message.content
                    else:
                        answer = "Файлын төрөл дэмжигдэхгүй байна."
                else:
                    history = [{"role": m["role"], "content": m["content"]}
                               for m in st.session_state.messages[:-1]]
                    history.append({"role": "user", "content": prompt})
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=history,
                        max_tokens=2048,
                    )
                    answer = response.choices[0].message.content

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
