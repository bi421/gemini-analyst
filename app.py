import streamlit as st
import google.generativeai as genai
import os

# Хуудасны тохиргоо
st.set_page_config(page_title="Gemini AI Analyst", layout="wide")

st.title("🤖 Gemini AI Шинжээч")
st.write("Текст болон дата дээр шинжилгээ хийхэд бэлэн.")

# API Key оруулах хэсэг (Нууцлал талаасаа sidebar-д байрлууллаа)
with st.sidebar:
    api_key = st.text_input("AIzaSyAo2I6X7aUYScHHGA0n_GlNcXpVLo6JXd0", type="password")
    st.info("API Key-ээ https://aistudio.google.com/app/apikey-оос авч болно.")

if api_key:
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Хэрэглэгчийн асуулт авах хэсэг
        user_input = st.text_area("Шинжлүүлэх текст эсвэл асуултаа бичнэ үү:", height=150)
        
        if st.button("Шинжлэх"):
            if user_input:
                with st.spinner('Түр хүлээнэ үү, Gemini бодож байна...'):
                    response = model.generate_content(user_input)
                    st.subheader("💡 Хариу:")
                    st.write(response.text)
            else:
                st.warning("Текстээ оруулна уу.")
                
    except Exception as e:
        st.error(f"Алдаа гарлаа: {e}")
else:
    st.warning("Үргэлжлүүлэхийн тулд API Key-ээ оруулна уу.")
