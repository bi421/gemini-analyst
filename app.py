import streamlit as st
import pandas as pd
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
    st.session_state.model = "orca-mini"

class OllamaDataAnalyst:
    def __init__(self, model: str = "orca-mini"):
        self.model = model
        self.conversation_history = []
    
    def build_system_prompt(self, dataframe: Optional[pd.DataFrame] = None) -> str:
        base_prompt = """You are an expert Data Analyst. Help users analyze their data.

Та мөн монгол хэлэнд хариулж болно. Хэрэв хэрэглэгч монгол хэлээр асуувал монголоор хариулна уу."""
        
        if dataframe is not None and not dataframe.empty:
            numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
            text_cols = dataframe.select_dtypes(include=['object', 'category']).columns.tolist()
            
            data_summary = f"""

DATASET:
- Rows: {dataframe.shape[0]}
- Columns: {dataframe.shape[1]}
- Numeric: {numeric_cols}
- Text: {text_cols}

Preview:
{dataframe.head().to_string()}"""
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
            return f"❌ Error: {str(e)}"

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

st.title("🤖 Smart AI Data Analyst")
st.markdown("**Монгол / English - 100% FREE**")

with st.sidebar:
    st.header("⚙️ Тохиргоо")
    
    model = st.selectbox("🧠 Model", ["orca-mini", "neural-chat", "mistral"])
    st.session_state.model = model
    
    st.info("✅ 100% ҮНЭГҮЙ - API хэрэхгүй")
    st.divider()
    
    st.header("📂 Өгөгдөл")
    uploaded_file = st.file_uploader("CSV, Excel, JSON", type=["csv", "xlsx", "json", "xls"])
    
    if uploaded_file:
        df = load_data(uploaded_file.read(), uploaded_file.name)
        if df is not None:
            st.session_state.df = df
            st.success(f"✅ {len(df)} мөр")
            with st.expander("👀 Preview"):
                st.dataframe(df.head())
    
    st.divider()
    if st.button("🗑️ Clear"):
        st.session_state.messages = []
        st.rerun()

st.subheader("💬 AI Chat")

if not st.session_state.messages and st.session_state.df is None:
    st.info("📋 Файл оруулна уу!")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Асуулт асуух..."):
    if st.session_state.df is None:
        st.error("❌ Файл оруулна уу")
        st.stop()
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("⏳"):
            try:
                analyst = OllamaDataAnalyst(st.session_state.model)
                response = analyst.chat(prompt, st.session_state.df)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"❌ {str(e)}")
