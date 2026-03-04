import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Gemini Analyst Pro", layout="wide")

# 2. АЮУЛГҮЙ БАЙДАЛ: Шинэ API Key-гээ энд заавал хашилтад хийж бичнэ үү
# ЖИШЭЭ: API_KEY = "AIzaSy..." 
API_KEY = "ЧИНИЙ_ШИНЭ_KEY_ЭНД" 

if API_KEY == "AIzaSyBn8Q3e0Z2TK9jr_RT7taJ80_JyQQtUuak":
    st.error("⚠️ Код доторх 'API_KEY' хэсэгт түлхүүрээ бичнэ үү!")
    st.stop()

genai.configure(api_key=API_KEY)

# 3. Загварыг хамгийн ухаалаг аргаар ачаалах (NotFound алдаанаас сэргийлнэ)
@st.cache_resource
def load_model():
    try:
        # Боломжит бүх загваруудыг шүүж үзнэ
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Хамгийн тогтвортой flash загварыг хайх
        target = next((m for m in available_models if '1.5-flash-latest' in m), 
                 next((m for m in available_models if '1.5-flash' in m), available_models[0]))
        return genai.GenerativeModel(target)
    except Exception as e:
        st.error(f"Загвар ачаалахад алдаа: {e}")
        return None

model = load_model()

# 4. Файл унших функц
def read_file_content(file):
    try:
        if file.name.endswith('.pdf'):
            return " ".join([p.extract_text() for p in PdfReader(file).pages])
        elif file.name.endswith('.docx'):
            return " ".join([p.text for p in docx.Document(file).paragraphs])
        elif file.name.endswith(('.csv', '.xlsx')):
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            return f"Өгөгдлийн хүснэгт:\n{df.to_string()}"
        elif file.name.endswith(('.png', '.jpg', '.jpeg')):
            return PIL.Image.open(file)
    except Exception as e:
        return f"Файл уншихад алдаа: {e}"
    return ""

# 5. UI - Sidebar
with st.sidebar:
    st.header("📁 Файл Оруулах")
    # Энд 'uploaded_file'-ыг хамгийн түрүүнд тодорхойлно (NameError-оос сэргийлнэ)
    uploaded_file = st.file_uploader("Шинжлэх файлаа сонго", type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg'])
    if st.button("🧹 Чат цэвэрлэх"):
        st.session_state.messages = []
        st.rerun()

# 6. UI - Үндсэн хэсэг
st.title("🧠 Gemini Ухаалаг Аналитик")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Чатны түүх харуулах
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Чат ба Логик
if prompt := st.chat_input("Асуултаа энд бичнэ үү..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            try:
                # Файл байгаа эсэхийг шалгаад контекст үүсгэх
                content_list = []
                if uploaded_file is not None:
                    file_data = read_file_content(uploaded_file)
                    if isinstance(file_data, str):
                        prompt = f"Контекст өгөгдөл: {file_data}\n\nАсуулт: {prompt}"
                    else: # Хэрэв зураг бол
                        content_list.append(file_data)
                
                content_list.append(prompt)
                
                response = model.generate_content(content_list)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Анализ хийхэд алдаа гарлаа: {e}")
