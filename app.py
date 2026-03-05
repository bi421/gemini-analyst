import streamlit as st
import pandas as pd
import plotly.express as px
import io
import json
import logging
from typing import Optional
import ollama

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Smart AI Data Analyst (FREE)", page_icon="🤖", layout="wide")

if "df" not in st.session_state:
    st.session_state.df = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "model" not in st.session_state:
    st.session_state.model = "neural-chat"

class OllamaDataAnalyst:
    """Free AI Data Analyst with Mongolian support"""
    
    def __init__(self, model: str = "neural-chat"):
        self.model = model
        self.conversation_history = []
    
    def build_system_prompt(self, dataframe: Optional[pd.DataFrame] = None) -> str:
        base_prompt = """You are an expert Data Analyst. Help users analyze their data clearly and simply.

Та мөн монгол хэлэнд хариулж болно. Хэрэв хэрэглэгч монгол хэлээр асуувал монголоор хариулна уу.

You can respond in both Mongolian and English. If user asks in Mongolian, respond in Mongolian."""
        
        if dataframe is not None and not dataframe.empty:
            numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
            text_cols = dataframe.select_dtypes(include=['object', 'category']).columns.tolist()
            
            data_summary = f"""

ӨГӨГДЛИЙН МЭДЭЭЛЭЛ / DATASET INFORMATION:
- Мөр: {dataframe.shape[0]}, Баганa: {dataframe.shape[1]}
- Тоон баганууд: {numeric_cols}
- Текст баганууд: {text_cols}

Өгөгдлийн урьдчилсан үзүүлэлт:
{dataframe.head().to_string()}

Энэ өгөгдлийг анализ хийж ойлголт өгнө үү."""
            return base_prompt + data_summary
        return base_prompt
    
    def chat(self, user_message: str, dataframe: Optional[pd.DataFrame] = None) -> str:
        try:
            system_prompt = self.build_system_prompt(dataframe)
            
            messages = []
            for msg in self.conversation_history[-10:]:
                messages.append(msg)
            messages.append({"role": "user", "content": user_message})
            
            response = ollama.chat(
                model=self.model,
                messages=messages,
                system=system_prompt,
                stream=False
            )
            
            assistant_message = response['message']['content']
            
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"❌ Алдаа: {str(e)}\n\nOllama ажиллаж байгаа эсэх шалгана уу! https://ollama.ai аас татаж `ollama serve` команд ажиллуулна уу."

@st.cache_data
def load_data(file_bytes, file_name: str) -> Optional[pd.DataFrame]:
    try:
        name_lower = file_name.lower()
        if name_lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_bytes))
        elif name_lower.endswith(".xlsx"):
            return pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        elif name_lower.endswith(".json"):
            data = json.loads(file_bytes.decode('utf-8'))
            return pd.DataFrame(data) if isinstance(data, list) else pd.json_normalize(data)
        return None
    except Exception as e:
        logger.error(f"File error: {e}")
        return None

col1, col2 = st.columns([4, 1])
with col1:
    st.title("🤖 Smart AI Data Analyst")
    st.markdown("**Монгол / English - 100% FREE**")
with col2:
    st.markdown("<div style='background:#667eea;color:white;padding:10px;border-radius:5px;text-align:center;font-weight:bold;'>✨ FREE</div>", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Тохиргоо / Settings")
    
    model = st.selectbox(
        "🧠 AI Model сонгох",
        ["neural-chat", "openchat", "orca-mini", "mistral"],
        help="Монгол хэлийг сайн ойлгодог загваруудыг сонгоно уу"
    )
    st.session_state.model = model
    
    st.info("""
    ✅ **100% ҮНЭГҮЙ**
    - API түлхүүр хэрэхгүй
    - Интернет хэрэхгүй
    - Таны компьютерт ажилладаг
    - Таны мэдээлэл нийт байдаггүй
    """)
    
    st.divider()
    
    st.header("📂 Өгөгдөл оруулах")
    uploaded_file = st.file_uploader("CSV, Excel, JSON", type=["csv", "xlsx", "json", "xls"])
    
    if uploaded_file:
        df = load_data(uploaded_file.read(), uploaded_file.name)
        if df is not None:
            st.session_state.df = df
            st.success(f"✅ Ачаалагдсан! {len(df)} мөр × {len(df.columns)} баганa")
            
            with st.expander("📊 Мэдээлэл"):
                st.metric("Мөр", len(df))
                st.metric("Баганa", len(df.columns))
            
            with st.expander("👀 Урьдчилсан үзүүлэлт"):
                st.dataframe(df.head(), use_container_width=True)
            
            with st.expander("📈 Статистик"):
                numeric_df = df.select_dtypes(include=['number'])
                if not numeric_df.empty:
                    st.dataframe(numeric_df.describe().T, use_container_width=True)
        else:
            st.error("❌ Файлыг ачаалах боломжгүй")
    
    st.divider()
    if st.button("🗑️ Чатыг цэвэрлэх", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.subheader("💬 Claude-тай ярилцах")

if not st.session_state.messages and st.session_state.df is None:
    st.info("👋 Файл оруулж AI-тай ярилцах! / Upload a file and chat with AI!", icon="📋")

with st.container():
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            st.markdown(msg["content"])

if prompt := st.chat_input("Асуулт асуух / Ask question..."):
    
    if st.session_state.df is None:
        st.error("❌ Эхлээд файл оруулна уу / Please upload a file first")
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.container():
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
    
    with st.container():
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 Боловсруулж байна..."):
                try:
                    analyst = OllamaDataAnalyst(st.session_state.model)
                    response = analyst.chat(prompt, st.session_state.df)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"❌ Алдаа: {str(e)}")
                    logger.error(str(e))

st.divider()
st.markdown("""
<div style='text-align:center;color:#888;font-size:12px;'>
🤖 Smart AI Data Analyst (ҮНЭГҮЙ) | Монгол хэл дэмжигдэж байна | Таны мэдээлэл хувийн байдаг
</div>
""", unsafe_allow_html=True)
