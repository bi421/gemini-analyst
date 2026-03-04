import streamlit as st
import google.generativeai as genai

st.title("🤖 Gemini AI Шинжээч")

api_key = st.sidebar.text_input("AIzaSyAo2I6X7aUYScHHGA0n_GlNcXpVLo6JXd0:", type="password")

if api_key:
    try:
        genai.configure(api_key=api_key)
        
        # --- ЗАГВАР ОЛОХ АВТОМАТ ХЭСЭГ ---
        # Танд ашиглах боломжтой бүх загваруудыг жагсааж авна
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        if not available_models:
            st.error("Танд ашиглах боломжтой загвар олдсонгүй.")
            st.stop()
            
        # Жагсаалтаас хамгийн сайн загварыг сонгох (Flash эсвэл Pro)
        # Бид гараараа бичихгүй, жагсаалтад байгаа нэрийг шууд авна
        selected_model_name = available_models[0] 
        for m_name in available_models:
            if '1.5-flash' in m_name: # Flash байвал илүү хурдан
                selected_model_name = m_name
                break
        
        st.success(f"Ажиллаж байна: {selected_model_name}")
        model = genai.GenerativeModel(selected_model_name)
        # -------------------------------

        user_input = st.text_area("Асуултаа бичнэ үү:")
        if st.button("Илгээх"):
            if user_input:
                response = model.generate_content(user_input)
                st.write("---")
                st.write(response.text)
                
    except Exception as e:
        # Хэрэв API-аас жагсаалт авч чадахгүй бол
        st.error(f"Алдаа гарлаа: {e}")
