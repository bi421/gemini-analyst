import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Gemini Analyst", layout="wide")

# 2. Дэлгэц дээр API Key нэхэх (Энэ хамгийн амархан нь)
with st.sidebar:
    st.title("⚙️ Тохиргоо")
    api_key = st.text_input("AIzaSyBQrLpgZXWQkSD4rLJ3ASzmFblCXfYgchQ:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Загварыг автоматаар сонгох
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in available_models if '1.5-flash' in m), available_models[0])
        model = genai.GenerativeModel(target)

        st.title("🚀 Gemini Ухаалаг Шинжээч")
        
        # Файл оруулах хэсэг
        uploaded_file = st.file_uploader("Файлаа сонго (PDF, Word, Excel, Зураг)", 
                                       type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg'])

        # Чатлах хэсэг
        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Юу шинжлүүлэх вэ? (Enter дар)"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                # Файл унших логик
                context = ""
                if uploaded_file:
                    if uploaded_file.name.endswith('.pdf'):
                        context = " ".join([p.extract_text() for p in PdfReader(uploaded_file).pages])
                    elif uploaded_file.name.endswith('.docx'):
                        context = " ".join([p.text for p in docx.Document(uploaded_file).paragraphs])
                    elif uploaded_file.name.endswith(('.csv', '.xlsx')):
                        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                        context = df.to_string()
                
                full_prompt = f"Контекст: {context}\n\nАсуулт: {prompt}" if context else prompt
                response = model.generate_content(full_prompt)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Алдаа: {e}")
else:
    st.warning("👈 Эхлээд хажуу талын цэсэнд API Key-гээ хийгээрэй.")
