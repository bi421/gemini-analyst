import streamlit as st
import google.generativeai as genai
import pandas as pd

st.set_page_config(page_title="Gemini AI Шинжээч", layout="wide")
st.title("🤖 Gemini AI Шинжээч")

api_key = st.text_input("AIzaSyAo2I6X7aUYScHHGA0n_GlNcXpVLo6JXd0", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # --- ЗАГВАР СОНГОХ УХААЛАГ ХЭСЭГ ---
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Хамгийн шилдэг загваруудыг дарааллаар нь хайх
        preferred_models = ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']
        selected_model_name = None
        
        for p in preferred_models:
            if p in available_models:
                selected_model_name = p
                break
        
        if not selected_model_name and available_models:
            selected_model_name = available_models[0]
            
        if selected_model_name:
            st.info(f"Ажиллаж байгаа загвар: {selected_model_name}")
            model = genai.GenerativeModel(selected_model_name)
        else:
            st.error("Танд тохирох Gemini загвар олдсонгүй.")
            st.stop()
        # ----------------------------------

        st.subheader("📊 Өгөгдөл оруулах")
        uploaded_file = st.file_uploader("CSV эсвэл Excel файл сонгоно уу", type=['csv', 'xlsx'])

        if uploaded_file is not None:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success("Файл амжилттай ачаалагдлаа!")
            st.dataframe(df.head(5))

            user_question = st.text_input("Дата дээр юу шинжлүүлэх вэ?", "Энэ өгөгдөл дээр ерөнхий дүгнэлт хийж өг.")
            
            if st.button("Датаг шинжлэх"):
                with st.spinner('Gemini шинжилж байна...'):
                    prompt = f"Өгөгдөл:\n{df.to_string()}\n\nАсуулт: {user_question}"
                    response = model.generate_content(prompt)
                    st.markdown(response.text)

        st.write("---")
        st.subheader("💬 Текстээр асуух")
        text_input = st.text_area("Асуултаа энд бичнэ үү:")
        if st.button("Илгээх"):
            if text_input:
                with st.spinner('Хариу бэлдэж байна...'):
                    response = model.generate_content(text_input)
                    st.write(response.text)

    except Exception as e:
        st.error(f"Алдаа гарлаа: {str(e)}")
