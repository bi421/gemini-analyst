import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Gemini Pro Analyst", layout="wide", page_icon="🧠")

# 2. API Key-г Secrets-ээс автоматаар унших
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["AIzaSyBQrLpgZXWQkSD4rLJ3ASzmFblCXfYgchQ"]
else:
    st.error("Secrets хэсэгт 'GEMINI_API_KEY' тохируулаагүй байна!")
    st.stop()

genai.configure(api_key=api_key)

# 3. Загвар сонгох (Хамгийн тогтвортой арга)
@st.cache_resource
def get_model():
    # Танд байгаа загваруудаас хамгийн тохиромжтойг нь автоматаар олно
    models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    target = next((m for m in models if '1.5-flash' in m), models[0])
    return genai.GenerativeModel(target)

model = get_model()

# 4. Файл боловсруулах функц
def get_file_content(file):
    if file.name.endswith('.pdf'):
        return " ".join([p.extract_text() for p in PdfReader(file).pages])
    elif file.name.endswith('.docx'):
        return " ".join([p.text for p in docx.Document(file).paragraphs])
    elif file.name.endswith(('.csv', '.xlsx')):
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        return f"Хүснэгтэн өгөгдөл:\n{df.to_string()}"
    elif file.name.endswith(('.png', '.jpg', '.jpeg')):
        return PIL.Image.open(file)
    return None

# 5. UI - Чат болон Sidebar
st.title("🚀 Gemini Ultra Analyst v3")
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("📁 Файл Шинжлүүлэх")
    uploaded_file = st.file_uploader("PDF, Word, Excel, Зураг...", 
                                   type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg'])
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.rerun()

# Чат харуулах
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Chat Input & Logic (Enter дарахад ажиллана)
if prompt := st.chat_input("Энд асуултаа бичээд Enter дарна уу..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            try:
                content = []
                if uploaded_file:
                    file_data = get_file_content(uploaded_file)
                    if isinstance(file_data, str):
                        prompt = f"Файлын агуулга: {file_data}\n\nАсуулт: {prompt}"
                    else: # Зураг бол
                        content.append(file_data)
                
                content.append(prompt)
                response = model.generate_content(content)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Алдаа гарлаа: {e}")
