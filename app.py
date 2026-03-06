git clone https://github.com/bi421/gemini-analyst.git
cd gemini-analyst

# app.py файлыг дээр код-ээр сэлгээ
# (Copy paste дээр app_final.py контент)

git add app.py
git commit -m "Final: Groq-based data analyst with Secrets"
git push origin main
```

---

### **Step 2: Streamlit Cloud - Secrets**

**Энэ БҮГДЭД хамгийн чухал!** 🔑

1. https://share.streamlit.io дээр явна
2. **gemini-analyst** app сонгона
3. **Manage app** (top-right corner)
4. **Secrets** tab дээр дарна
5. Доох оруулна:
```
GROQ_API_KEY = "gsk_xxxxxxxxxxxxx"
```

6. **Save** → App auto reboot

---

### **Step 3: Groq API Key авах (үнэгүй)**

1. https://console.groq.com
2. **Sign up** (free)
3. **API Keys** → Copy
4. Streamlit Secrets дээ paste

---

## ✅ **Requirements.txt**
```
streamlit==1.31.1
pandas==2.1.4
numpy==1.26.3
requests==2.31.0
groq==0.4.2
python-dotenv==1.0.0
openpyxl==3.10.10
```

---

## 🛡️ **Security:**

✅ **GitHub дээ байгаа:**
- app.py
- requirements.txt
- .gitignore

❌ **GitHub дээ БАЙХГҮЙ:**
- API keys
- .env files
- secrets.toml

✅ **Streamlit Cloud дээ:**
- GROQ_API_KEY (Secrets)

---

## 📝 **Features:**

✅ Groq API integration
✅ CSV/Excel/JSON support
✅ Монгол хэл
✅ Chat history
✅ Data preview
✅ Error handling
✅ No hardcoded secrets

---

## 🎯 **Ready?**
```
1. Copy app_final.py content to GitHub app.py
2. Push to GitHub
3. Add GROQ_API_KEY to Streamlit Secrets
4. Reboot app
5. ✅ Done!
