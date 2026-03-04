import streamlit as st
import google.generativeai as genai
import pandas as pd # Дата уншихад хэрэгтэй

st.set_page_config(page_title="Gemini AI Шинжээч", layout="wide")
st.title("🤖 Gemini AI Шинжээч")

# API Key хэсэг (Хэрэв чи Secrets тохируулаагүй бол)
api_key = st.text_input("AIzaSyAo2I6X7aUYScHHGA0n_GlNcXpVLo6JXd0", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Эсвэл gemini-pro

    # --- ФАЙЛ ОРУУЛАХ ХЭСЭГ ---
    st.subheader("📊 Өгөгдөл оруулах")
    uploaded_file = st.file_uploader("CSV эсвэл Excel файл сонгоно уу", type=['csv', 'xlsx'])

    if uploaded_file is not None:
        try:
            # Файлын төрлөөс хамаарч унших
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.success("Файл амжилттай ачаалагдлаа!")
            st.dataframe(df.head(10)) # Эхний 10 мөрийг харуулах

            # Шинжлэх товчлуур
            user_question = st.text_input("Энэ дата дээр юу шинжлүүлэх вэ?", "Энэ өгөгдөл дээр ерөнхий дүгнэлт хийж, чухал үзүүлэлтүүдийг хэлж өгөөч.")
            
            if st.button("Датаг шинжлэх"):
                with st.spinner('Gemini датаг уншиж байна...'):
                    # Датаг текст болгож Gemini-д илгээх
                    prompt = f"Дараах өгөгдөл дээр шинжилгээ хийж, '{user_question}' гэсэн асуултад хариулна уу:\n\n{df.to_string()}"
                    response = model.generate_content(prompt)
                    st.markdown("### 📝 Шинжилгээний хариу:")
                    st.write(response.text)
        except Exception as e:
            st.error(f"Файл уншихад алдаа гарлаа: {e}")

    # Текстээр асуух хэсэг (хэвээрээ үлдээв)
    st.write("---")
    st.subheader("💬 Текстээр асуух")
    text_input = st.text_area("Асуултаа энд бичнэ үү:")
    if st.button("Илгээх"):
        if text_input:
            response = model.generate_content(text_input)
            st.write(response.text)
