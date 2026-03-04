import streamlit as st
import google.generativeai as genai
import pandas as pd

# 1. Хуудасны тохиргоо
st.set_page_config(page_title="Gemini AI Шинжээч", layout="wide", page_icon="🤖")

# 2. Дизайн нэмэх (CSS)
st.markdown("""
    <style>
    .main { background-color: #f0f2f6; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; background-color: #4A90E2; color: white; border: none; }
    .stButton>button:hover { background-color: #357ABD; border: none; }
    .stTextInput>div>div>input { border-radius: 8px; }
    .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar - Тохиргооны хэсэг
with st.sidebar:
    st.title("⚙️ Тохиргоо")
    api_key = st.text_input("AIzaSyAgHPf-9Ldr9h8oVQ1XA99jzIjm7gmCiXI:", type="password", help="aistudio.google.com-оос авсан түлхүүрээ хийнэ үү.")
    
    st.divider()
    st.subheader("🚀 Түргэн үйлдлүүд")
    if st.button("🔄 Апп-ыг шинэчлэх"):
        st.rerun()
    
    if st.button("🧹 Түүх устгах"):
        st.session_state.clear()
        st.success("Цэвэрлэгдлээ!")

# 4. Үндсэн логик
if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Загварыг автоматаар сонгох
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        selected_model_name = available_models[0] if available_models else "models/gemini-1.5-flash"
        model = genai.GenerativeModel(selected_model_name)

        # Дээд хэсэг
        col1, col2 = st.columns([3, 1])
        with col1:
            st.title("🤖 Gemini AI Ухаалаг Шинжээч")
            st.caption(f"Одоо ашиглаж буй загвар: {selected_model_name}")

        # Табууд (Хэсгүүд)
        tab1, tab2, tab3 = st.tabs(["📊 Дата Шинжилгээ", "💬 AI Чат", "📝 Текст Боловсруулах"])

        with tab1:
            st.subheader("Excel/CSV Файл Шинжлэх")
            uploaded_file = st.file_uploader("Шинжлүүлэх файлаа оруулна уу", type=['csv', 'xlsx'])
            
            if uploaded_file:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                st.write("📈 Өгөгдлийн тойм:")
                st.dataframe(df.head(5), use_container_width=True)
                
                # Шинжилгээний товчлуурууд
                c1, c2, c3 = st.columns(3)
                if c1.button("🔍 Ерөнхий дүгнэлт гаргах"):
                    with st.spinner('Шинжлэж байна...'):
                        res = model.generate_content(f"Дараах дата дээр ерөнхий дүгнэлт хийж өг: {df.to_string()}")
                        st.markdown(res.text)
                
                if c2.button("📉 Тренд тодорхойлох"):
                    with st.spinner('Хайж байна...'):
                        res = model.generate_content(f"Энэ дата доторх хамгийн сонирхолтой трендүүдийг олоод өг: {df.to_string()}")
                        st.markdown(res.text)

                if c3.button("⚠️ Алдаа шалгах"):
                    with st.spinner('Шалгаж байна...'):
                        res = model.generate_content(f"Энэ дата дотор ямар нэгэн логик алдаа эсвэл сонин тоо байна уу?: {df.to_string()}")
                        st.markdown(res.text)

        with tab2:
            st.subheader("AI-тай чөлөөтэй ярилцах")
            chat_input = st.text_input("Асуултаа энд бичнэ үү...", placeholder="Жишээ нь: Маркетингийн төлөвлөгөө гаргахад туслаач?")
            if st.button("Илгээх", key="chat_btn"):
                if chat_input:
                    with st.spinner('Бодож байна...'):
                        res = model.generate_content(chat_input)
                        st.info(res.text)

        with tab3:
            st.subheader("Текст дээр ажиллах")
            raw_text = st.text_area("Урт текст энд хуулна уу...", height=200)
            col_a, col_b = st.columns(2)
            if col_a.button("📝 Товчлох (Summarize)"):
                res = model.generate_content(f"Дараах текстийг маш ойлгомжтой товчилж өг: {raw_text}")
                st.success(res.text)
            if col_b.button("🇬🇧 Англи руу орчуулах"):
                res = model.generate_content(f"Дараах текстийг мэргэжлийн түвшинд англи руу орчуулж өг: {raw_text}")
                st.success(res.text)

    except Exception as e:
        st.error(f"Алдаа: {e}")
else:
    st.warning("👈 Хажуу талын цэсэнд API Key-гээ оруулж эхлүүлнэ үү.")
