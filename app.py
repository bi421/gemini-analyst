import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Gemini Analyst Pro", layout="wide")

# 2. АЮУЛГҮЙ БАЙДАЛ: API Key-г энд хашилтад хийж бичнэ үү
# Жишээ: API_KEY = "AIzaSy..."
API_KEY = "ЧИНИЙ_ШИНЭ_KEY_ЭНД" 

# API тохиргоог ганц удаа хийх
if API_KEY != "ЧИНИЙ_ШИНЭ_KEY_ЭНД":
    genai.configure(api_key=API_KEY)
else:
    st.error("AIzaSyBn8Q3e0Z2TK9jr_RT7taJ80_JyQQtUuak")
    st.stop()

# 3. Загварыг хамгийн найдвартай аргаар ачаалах
@st.cache_resource
def load_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in models if '1.5-flash' in m), models[0])
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"Загвар ачаалахад алдаа гарлаа: {e}")
        return None

model = load_model()

# 4. Файл унших функц (Бүх төрлийн файл)
def read_file(file):
    try:
        if file.name.endswith('.pdf'):
            return " ".join([p.extract_text() for p in PdfReader(file).pages])
        elif file.name.endswith('.docx'):
            return " ".join([p.text for p in docx.Document(file).paragraphs])
        elif file.name.endswith(('.csv', '.xlsx')):
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            return f"Дата хүснэгт:\n{df.to_string()}"
        elif file.name.endswith(('.png', '.jpg', '.jpeg')):
            return PIL.Image.open(file)
    except Exception as e:
        return f"Файл уншихад алдаа: {e}"
    return None

# 5. UI - Үндсэн хэсэг
st.title("🚀 Gemini Ухаалаг Аналитик")
st.caption("Бүх төрлийн файл (PDF, Word, Excel, Зураг) шинжлэгч")

# Sidebar - Файл оруулах
with st.sidebar:
    st.header("📁 Өгөгдөл оруулах")
    uploaded_file = st.file_uploader("Файлаа сонго", type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg'])
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.rerun()

# Чатны түүх хадгалах
if "messages" not in st.session_state:
    st.session_state.messages = []

# Хуучин чатуудыг харуулах
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Чат ба Анализ (ENTER дарахад ажиллана)
if prompt := st.chat_input("Энд асуултаа бичнэ үү..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            try:
                content_to_send = []
                # Хэрэв файл байгаа бол уншиж промпт руу нэмнэ
                if uploaded_file:
                    data = read_file(uploaded_file)
                    if isinstance(data, str):
                        prompt = f"Файлын агуулга: {data}\n\nАсуулт: {prompt}"
                    else: # Зураг бол
                        content_to_send.append(data)
                
                content_to_send.append(prompt)
                
                # AI-аас хариу авах
                response = model.generate_content(content_to_send)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Алдаа гарлаа: {e}")
