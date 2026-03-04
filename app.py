import streamlit as st
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import docx

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Gemini Ultra Analyst", layout="wide", page_icon="🧠")

# 2. Session State - Түүх болон Тохиргоо хадгалах
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

# 3. CSS - Чат болон Дизайн
st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .sidebar-text { font-size: 12px; color: #666; }
    </style>
    """, unsafe_allow_html=True)

# 4. Sidebar - Admin & File Upload
with st.sidebar:
    st.title("🔒 Admin & Багаж")
    
    with st.expander("🔑 API Тохиргоо (Admin)"):
        input_key = st.text_input("AIzaSyAgHPf-9Ldr9h8oVQ1XA99jzIjm7gmCiXI:", type="password", value=st.session_state.api_key)
        if st.button("Хадгалах"):
            st.session_state.api_key = input_key
            st.success("API Key хадгалагдлаа!")

    st.divider()
    st.subheader("📁 Файл Оруулах")
    uploaded_file = st.file_uploader("PDF, Word, Excel, CSV, Зураг", 
                                   type=['pdf', 'docx', 'csv', 'xlsx', 'png', 'jpg', 'jpeg'])

# 5. Файл унших функц
def process_file(file):
    if file.name.endswith('.pdf'):
        reader = PdfReader(file)
        return " ".join([page.extract_text() for page in reader.pages])
    elif file.name.endswith('.docx'):
        doc = docx.Document(file)
        return " ".join([para.text for para in doc.paragraphs])
    elif file.name.endswith(('.csv', '.xlsx')):
        df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
        return df.to_string()
    elif file.name.endswith(('.png', '.jpg', '.jpeg')):
        import PIL.Image
        return PIL.Image.open(file)
    return None

# 6. Үндсэн Logic
if st.session_state.api_key:
    genai.configure(api_key=st.session_state.api_key)
    # Автомат загвар сонгогч
    model = genai.GenerativeModel('gemini-1.5-flash')

    st.title("🧠 Gemini Ultra Шинжээч")
    
    # Файл боловсруулах
    file_content = None
    if uploaded_file:
        file_content = process_file(uploaded_file)
        st.info(f"📎 {uploaded_file.name} ачаалагдлаа. AI одоо энэ файл дээр ажиллахад бэлэн.")

    # Чат харуулах
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input (Enter дарахад ажиллана)
    if prompt := st.chat_input("Юу шинжлүүлэх вэ?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Бодож байна..."):
                # Хэрэв файл байгаа бол промпттой хольж илгээнэ
                if file_content is not None:
                    if isinstance(file_content, str):
                        full_prompt = f"Контекст (Файл): {file_content}\n\nАсуулт: {prompt}"
                        response = model.generate_content(full_prompt)
                    else: # Зураг бол
                        response = model.generate_content([prompt, file_content])
                else:
                    response = model.generate_content(prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
else:
    st.warning("👈 Эхлээд Sidebar-ын Admin хэсэгт API Key-гээ тохируулна уу.")
