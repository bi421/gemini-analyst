import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import docx
import io

# =============================================================================
# ТОХИРГОО – текст input байнга харагдана
# =============================================================================
st.set_page_config(page_title="AI Аналитик", layout="wide", page_icon="🧠")

st.title("AI Аналитик – Файл + Чат")

st.markdown("""
<style>
    .stChatInputContainer {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: white !important;
        padding: 1rem !important;
        border-top: 1px solid #ddd !important;
        z-index: 9999 !important;
        box-shadow: 0 -4px 12px rgba(0,0,0,0.1) !important;
    }
    .main .block-container {
        padding-bottom: 160px !important;
    }
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 17px;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

# =============================================================================
# ФАЙЛ УНШИХ
# =============================================================================
uploaded_file = st.file_uploader("CSV, XLSX, PDF, DOCX оруулна уу", type=['csv', 'xlsx', 'pdf', 'docx'])

if uploaded_file is not None:
    try:
        name = uploaded_file.name.lower()
        if name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
            st.success(f"CSV уншлаа: {len(df)} мөр")
            st.dataframe(df.head(10))
        elif name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
            st.success(f"Excel уншлаа: {len(df)} мөр")
            st.dataframe(df.head(10))
        elif name.endswith('.pdf'):
            reader = PdfReader(uploaded_file)
            text = " ".join(page.extract_text() or "" for page in reader.pages)
            st.markdown("**PDF агуулга (эхний хэсэг):**")
            st.text_area("Текст", text[:3000], height=250)
        elif name.endswith('.docx'):
            doc = docx.Document(uploaded_file)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            st.markdown("**DOCX агуулга (эхний хэсэг):**")
            st.text_area("Текст", text[:3000], height=250)
    except Exception as e:
        st.error(f"Файл уншихад алдаа гарлаа: {str(e)}")

# =============================================================================
# ЧАТ ХЭСЭГ – доод талд байнга харагдана
# =============================================================================
st.markdown("---")
st.subheader("Асуулт асуух")

# Өмнөх мессежүүд
for msg in st.session_state.messages:
    avatar = "👤" if msg["role"] == "user" else "🤖"
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# Текст бичдэг хэсэг (байнга харагдана)
prompt = st.chat_input("Асуулт бичнэ үү... (файл оруулсан бол түүний талаар асууж болно)")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Хариулж байна..."):
            # Логиктой, ухаалаг placeholder (API байхгүй ч гэсэн хэрэглэгчийг тусалж байгаа мэт хариулна)
            if len(prompt.strip()) < 5:
                response = "Асуулт маш товч байна. Илүү тодорхой бичээд үзээрэй."
            elif "файл" in prompt.lower() or "файл" in prompt:
                response = "Файл оруулсан бол түүний талаар асууж үзээрэй. Жишээ: 'Энэ хүснэгтээс ямар тренд харагдаж байна вэ?' эсвэл 'Энэ PDF-ээс гол санааг гаргаж өгөөч'."
            elif "сайн байна уу" in prompt.lower() or "сайн уу" in prompt.lower():
                response = "Сайн байна уу! Ямар тусламж хэрэгтэй вэ? Файл оруулсан уу, эсвэл өөр асуулт байна уу?"
            elif "чи сайжирч" in prompt.lower() or "ухаалаг" in prompt.lower():
                response = "Тийм ээ, би сайжирч чадна. Гэхдээ одоо миний хариулт таны апп доторх AI-ээс хамаарна. Хэрэв Groq эсвэл Gemini key байхгүй бол placeholder хариулт өгч байна. Key оруулаад туршаад үзээрэй."
            else:
                response = f"Таны асуулт: **{prompt}**\n\nХариулт: Одоогоор бүрэн AI холбогдоогүй байгаа тул логиктой placeholder өгч байна. Асуултаа илүү тодорхой болгоод дахин бичвэл илүү сайн хариулж чадна."

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.caption("Текст бичдэг хэсэг доод талд байнга харагдана • Файл + чат дэмжинэ • Алдаа гарвал лог руу орж шалгаарай")
