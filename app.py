import streamlit as st
import google.generativeai as genai
import pandas as pd

# Апп-ын үндсэн тохиргоо
st.set_page_config(page_title="Gemini AI Шинжээч", layout="wide", page_icon="🤖")

# Дизайн (CSS) - Жаахан өнгө нэмье
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stTextInput>div>div>input { border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Хажуу талын цэс (Sidebar)
with st.sidebar:
    st.title("⚙️ Тохиргоо")
    api_key = st.text_input("AIzaSyAo2I6X7aUYScHHGA0n_GlNcXpVLo6JXd0:", type="password")
    st.info("API Key-г aistudio.google.com-оос авна.")
    
    st.divider()
    st.write("🚀 **Боломжууд:**")
    st.write("✅ Текст шинжилгээ")
    st.write("✅ Excel/CSV унших")
    st.write("✅ AI зөвлөгөө")

# Үндсэн хэсэг
st.title("🤖 Gemini AI Шинжээч")
st.write("Текст болон дата дээр суурилсан ухаалаг шинжилгээний платформ.")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # Загваруудыг шалгах
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = 'models/gemini-1.5-flash' if 'models/gemini-1.5-flash' in models else 'models/gemini-pro'
        model = genai.GenerativeModel(target_model)
        
        # Хоёр таб үүсгэх (Дата болон Текст)
        tab1, tab2 = st.tabs(["📊 Дата Шинжилгээ", "💬 AI-тай Чатлах"])

        with tab1:
            st.subheader("Excel эсвэл CSV файл шинжлэх")
            uploaded_file = st.file_uploader("Файлаа сонгоно уу", type=['csv', 'xlsx'])
            
            if uploaded_file:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                st.dataframe(df.head(10), use_container_width=True)
                
                analysis_prompt = st.text_area("Дата дээр юуг анхаарч шинжлэх вэ?", "Энэхүү өгөгдлөөс хамгийн чухал 3 дүгнэлтийг гаргаж, цаашид анхаарах зүйлсийг хэлж өгөөч.")
                
                if st.button("Шинжилгээг эхлүүлэх"):
                    with st.spinner('AI датаг боловсруулж байна...'):
                        full_prompt = f"Дата өгөгдөл: {df.to_string()}\n\nАсуулт: {analysis_prompt}"
                        response = model.generate_content(full_prompt)
                        st.markdown("---")
                        st.markdown("### 📈 Шинжилгээний хариу")
                        st.write(response.text)

        with tab2:
            st.subheader("AI-аас асуулт асуух")
            user_text = st.text_area("Асуулт эсвэл текстээ энд бичнэ үү...", height=150)
            if st.button("Хариу авах"):
                if user_text:
                    with st.spinner('Бодож байна...'):
                        response = model.generate_content(user_text)
                        st.info(response.text)
                else:
                    st.warning("Текст оруулна уу.")

    except Exception as e:
        st.error(f"Алдаа: {e}")
else:
    st.warning("👈 Хажуу талын цэсэнд API Key-гээ оруулж апп-аа идэвхжүүлнэ үү.")
