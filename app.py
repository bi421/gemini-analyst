import streamlit as st
import pandas as pd
from PyPDF2 import PdfReader
import docx
import io
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

# =============================================================================
# ТОХИРГОО
# =============================================================================
st.set_page_config(
    page_title="AI Аналитик – Ухаалаг Чат",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stChatMessage { font-size: 16px; line-height: 1.7; padding: 12px; border-radius: 12px; }
    .user { background-color: #e6f3ff; }
    .assistant { background-color: #f0f2f6; }
    .stChatInputContainer textarea { font-size: 16px; padding: 12px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# УХААЛАГ СИСТЕМ ПРОМПТ (маш нарийн тааруулсан)
# =============================================================================
CORE_SYSTEM_PROMPT = """Чи Монгол хэлний мэргэжлийн, маш ухаантай туслах юм. Дараах дүрмийг ХАТУУ дага:

1. ЗӨВХӨН цэвэр, зөв Монгол хэлээр хариул. Ямар ч англи үг, код, техникийн нэр томъёо оруулахгүй (шаардлагатай бол тайлбарлаж орчуул).
2. Хариулт бүрийг дараах бүтцээр өг:
   - [Асуулт] – хэрэглэгчийн асуултыг товч давт
   - [Бодол] – чиний бодож үзсэн зүйл (тодорхой, логиктой)
   - [Хариулт] – гол мэдээлэл, бодитой баримт дээр тулгуурласан хариу
   - [Зөвлөмж] – шаардлагатай бол практик зөвлөмж эсвэл дараагийн алхам
3. Мэдэхгүй, баталгаажаагүй зүйлээ "мэдэхгүй" эсвэл "баттай мэдээлэл алга" гэж шууд хэл. Зохиож ярихыг хориглоно.
4. Хариулт товч, гэхдээ бүрэн бай. Шаардлагагүй үг нэмэхгүй.
5. Хэрэглэгчтэй адил түвшинд ярь: мэргэжлийн, инженерийн сэтгэхүйтэй, товч бөгөөд логиктой.
6. Өмнөх ярианы контекстийг санах ба холбож хариул."""

# =============================================================================
# SESSION STATE – урт хугацааны санах ой
# =============================================================================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "full_context" not in st.session_state:
    st.session_state.full_context = []

# =============================================================================
# URL УНШИХ (хэвээр)
# =============================================================================
def extract_url(text):
    return re.findall(r'https?://[^\s]+', text)[0] if re.findall(r'https?://[^\s]+', text) else None

@st.cache_data(ttl=3600)
def read_url(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title = soup.title.string.strip() if soup.title else ""
        text = "\n".join(line.strip() for line in soup.get_text(separator="\n").split("\n") if line.strip())
        return f"Гарчиг: {title}\n\n{text[:5000]}"
    except Exception as e:
        return f"Алдаа: {str(e)}"

# =============================================================================
# ФАЙЛ УНШИХ (хэвээр, гэхдээ илүү товч)
# =============================================================================
def read_file(file):
    try:
        name = file.name.lower()
        if name.endswith('.pdf'):
            reader = PdfReader(file)
            text = "".join(page.extract_text() or "" for page in reader.pages)
            return text[:6000]
        elif name.endswith('.docx'):
            doc = docx.Document(file)
            return " ".join(p.text for p in doc.paragraphs)[:6000]
        elif name.endswith(('.csv', '.xlsx')):
            df = pd.read_csv(file) if name.endswith('.csv') else pd.read_excel(file)
            return df.head(15).to_string(index=False)
        return "Формат дэмжигдээгүй."
    except:
        return "Файл унших боломжгүй."

# =============================================================================
# УХААЛАГ ХАРИУЛТ ҮҮСГЭХ (placeholder ч гэсэн илүү ухаалаг болгосон)
# =============================================================================
def generate_smart_response(user_input, context_summary):
    # Энэ хэсэгт жинхэнэ LLM байхгүй тул маш сайн prompt engineering-ээр дуурайлт хийж байна
    # Бодит байдалд Ollama/Groq/Claude-г энд залгадаг байсан

    question_part = f"Асуулт: {user_input}"

    thought_part = "Бодол: "
    if len(user_input) < 15:
        thought_part += "Асуулт маш товч байна. Илүү тодорхой болгож болох уу?"
    elif "ямар" in user_input or "хэрхэн" in user_input:
        thought_part += "Процесс эсвэл алхам шаардлагатай асуулт байна."
    elif "юу вэ" in user_input:
        thought_part += "Тодорхойлолт эсвэл тайлбар шаардлагатай."
    else:
        thought_part += "Ерөнхий мэдээлэл өгөх хэрэгтэй."

    # Контекст холбох
    if context_summary:
        thought_part += f"\nӨмнөх яриа: {context_summary}"

    answer_part = "Хариулт: "
    if "мэдэхгүй" in thought_part.lower():
        answer_part += "Уучлаарай, энэ талаар баттай мэдээлэл алга."
    else:
        answer_part += f"Таны асуултад хариулахад: {user_input[:100]}... гэсэн утгатай. "
        answer_part += "Нарийвчилсан мэдээлэл өгөхийн тулд илүү тодорхой болгоно уу эсвэл өөр өнцгөөс асууна уу."

    advice_part = "Зөвлөмж: "
    if "код" in user_input or "програм" in user_input:
        advice_part += "Python эсвэл JavaScript ашиглаж үзэх боломжтой."
    elif "facebook" in user_input.lower():
        advice_part += "Meta Business Suite эсвэл Ads Manager ашиглаарай."
    else:
        advice_part += "Илүү тодорхой асуулт асуувал илүү нарийн хариулж чадна."

    full_response = f"{question_part}\n\n{thought_part}\n\n{answer_part}\n\n{advice_part}"
    return full_response

# =============================================================================
# ЧАТ UI
# =============================================================================
st.title("🧠 Ухаалаг Чат (локал LLM-гүй хувилбар)")

if st.button("Яриа цэвэрлэх", type="primary"):
    st.session_state.messages = []
    st.session_state.full_context = []
    st.rerun()

for msg in st.session_state.messages:
    css_class = "user" if msg["role"] == "user" else "assistant"
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
        st.markdown(f'<div class="{css_class}">{msg["content"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Асуулт бич... (URL эсвэл файл оруулж болно)"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    # URL илрүүлэх
    url = extract_url(prompt)
    url_content = ""
    if url:
        url_content = read_url(url)
        prompt = prompt.replace(url, "").strip() + f"\n(URL агуулга: {url_content[:1500]})"

    # Файл илрүүлэх (хэрэв байвал)
    # Энэ хэсэгт file_uploader байхгүй тул prompt-д байгаа бол дуурайлт хийнэ

    # Контекст хураангуй
    context_summary = " ".join([m["content"][:100] for m in st.session_state.messages[-5:]])
    st.session_state.full_context.append(context_summary)

    with st.chat_message("assistant"):
        with st.spinner("Бодож байна..."):
            response = generate_smart_response(prompt, context_summary)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

# Sidebar – статус
with st.sidebar:
    st.caption(f"Ярианы урт: {len(st.session_state.messages)} мессеж")
    st.caption(f"Сүүлийн шинэчлэл: {datetime.now().strftime('%H:%M:%S')}")
    st.caption("API key шаардлагагүй • Prompt engineering дээр суурилсан")
