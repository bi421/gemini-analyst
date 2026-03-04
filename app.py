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
            return " ".join([p.extract_text() or "" for p in PdfReader(file).pages])
        elif file.name.endswith('.docx'):
            return " ".join([p.text for p in docx.Document(file).paragraphs])
        elif file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', on_bad_lines='skip')
            return f"Өгөгдлийн хүснэгт:\n{df.to_string()}"
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file)
            return f"Өгөгдлийн хүснэгт:\n{df.to_string()}"
        elif file.name.endswith(('.png', '.jpg', '.jpeg')):
            img = PIL.Image.open(file)
            buf = io.BytesIO()
            img.save(buf, format='PNG')
            return base64.b64encode(buf.getvalue()).decode('utf-8')
    except Exception as e:
        return f"Файл уншихад алдаа: {e}"
    return ""

# 4. UI - Sidebar
with st.sidebar:
    st.header("📁 Файл Оруулах")
    uploaded_file = st.file_uploader(
        "Шинжлэх файлаа сонго",
        type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg']
    )
    st.caption("🤖 Загвар: llama-3.3-70b-versatile")
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.rerun()

# 5. UI - Үндсэн хэсэг
st.title("🧠 Groq Ухаалаг Аналитик")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Чат ба Логик
if prompt := st.chat_input("Асуултаа энд бичнэ үү..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            try:
                # Файл байвал prompt-д нэм
                full_prompt = prompt
                if uploaded_file is not None:
                    file_data = read_file_content(uploaded_file)
                    if uploaded_file.name.endswith(('.png', '.jpg', '.jpeg')):
                        full_prompt = prompt  # Зураг текст болгон дамжуулахгүй
                        st.info("ℹ️ Groq зураг дэмждэггүй — текст файл ашиглана уу.")
                    else:
                        full_prompt = f"Контекст өгөгдөл:\n{file_data}\n\nАсуулт: {prompt}"

                # Groq API дуудах
                history = [{"role": m["role"], "content": m["content"]}
                           for m in st.session_state.messages[:-1]]
                history.append({"role": "user", "content": full_prompt})

                if client:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=history,
                        max_tokens=2048,
                        temperature=0.7,
                    )
                    answer = response.choices[0].message.content
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    st.error("🔑 GROQ_API_KEY secrets-д байхгүй байна!")

            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    st.warning("⏳ Хэт олон хүсэлт илгээсэн. Хэдэн секунд хүлээгээд дахин оролдоно уу.")
                elif "401" in error_msg:
                    st.error("🔑 API түлхүүр буруу байна.")
                else:
                    st.error(f"❌ Алдаа гарлаа: {e}")
