import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image

# --- ТОХИРГОО ---
# Энд өөрийнхөө ШИНЭ АПИ түлхүүрийг ганцхан удаа хадаж байна.
# Анхаар: Хэрэв GitHub чинь Public бол энэ түлхүүр блок болох магадлалтай.
# Тиймээс хамгийн сайн арга бол Secrets-т хийх, гэхдээ одоохондоо ингээд туршъя.
MY_PERMANENT_KEY = "AIzaSy..." # <--- ШИНЭ ТҮЛХҮҮРЭЭ ЭНД ХУУЛЖ ТАВЬ

# API холболтыг шалгах
if "configured" not in st.session_state:
    genai.configure(api_key="AIzaSyBn8Q3e0Z2TK9jr_RT7taJ80_JyQQtUuak")
    st.session_state.configured = True

# Загвар сонгох
@st.cache_resource
def load_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = load_model()

st.title("🧠 Gemini Аналитик (Auto-Login)")

# Файл оруулах
uploaded_file = st.file_uploader("Шинжлэх файлаа оруулна уу", type=['pdf', 'docx', 'csv', 'xlsx'])

# Чатны түүх
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Асуулт асуух (Enter дарахад шууд ажиллана)
if prompt := st.chat_input("Датагаа шинжлүүлэх үү?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            context = ""
            if uploaded_file:
                # Файл унших хэсэг
                if uploaded_file.name.endswith('.pdf'):
                    context = " ".join([p.extract_text() for p in PdfReader(uploaded_file).pages])
                elif uploaded_file.name.endswith(('.csv', '.xlsx')):
                    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                    context = f"Дата: {df.to_string()}"
            
            response = model.generate_content(f"{context}\n\nАсуулт: {prompt}")
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})
