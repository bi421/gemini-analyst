import streamlit as st
import google.generativeai as genai

# 1. Шинэ төслөөс авсан API Түлхүүр (New Project-оос авснаа тавиарай)
genai.configure(api_key="AIzaSyD1uOiYeQI63f1mF8fDdKkJGgjBtgtSRaY")

st.title("📈 2026 Smart AI Analyst")

# 2. ЧИНИЙ ЖАГСААЛТАД БАЙСАН ЯГ ТЭР НЭР:
MODEL_NAME = 'models/gemma-3-27b-it' 

reels_view = st.number_input("Reels үзэлт:", value=88)
photo_view = st.number_input("Photo үзэлт:", value=24)

if st.button("Шинжилгээг эхлүүлэх"):
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        prompt = f"""
        Чи бол сошиал медиа аналист. Дараах дата дээр шинжилгээ хийж, 
        монгол хэл дээр 3 тодорхой зөвлөгөө өг:
        - Reels үзэлт: {reels_view}
        - Photo үзэлт: {photo_view}
        """
        
        response = model.generate_content(prompt)
        st.success(f"Амжилттай! Ашигласан модель: {MODEL_NAME}")
        st.markdown("---")
        st.write(response.text)
        
    except Exception as e:
        if "429" in str(e):
            st.error("Google-ийн үнэгүй квот (Quota) түр зуур дүүрсэн байна. 1 минут хүлээгээд дахин 'Шинжилгээ' товчийг дар.")
        else:
            st.error(f"Алдаа гарлаа: {e}")