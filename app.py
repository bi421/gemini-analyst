import streamlit as st
import pandas as pd
import io
import json
import logging
from typing import Optional
from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Smart AI Data Analyst (FREE)", page_icon="🤖", layout="wide")

if "df" not in st.session_state:
    st.session_state.df = None
if "messages" not in st.session_state:
    st.session_state.messages = []

class GroqDataAnalyst:
    def __init__(self, api_key: str):
        self.client = Groq(api_key=api_key)
        self.conversation_history = []
    
    def build_system_prompt(self, dataframe: Optional[pd.DataFrame] = None) -> str:
        base_prompt = """You are an expert Data Analyst. Help users analyze their data deeply and provide insights.
        
Та мөн монгол хэлэнд хариулж болно. Хэрэв хэрэглэгч монгол хэлээр асуувал монголоор хариулна уу.

When analyzing data, provide:
1. Clear summary of findings
2. Key insights
3. Recommendations if applicable
4. Use simple language"""
        
        if dataframe is not None and not dataframe.empty:
            numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
            text_cols = dataframe.select_dtypes(include=['object', 'category']).columns.tolist()
            
            data_summary = f"""

DATASET INFORMATION:
- Total Rows: {dataframe.shape[0]}
- Total Columns: {dataframe.shape[1]}
- Numeric Columns: {numeric_cols}
- Text/Category Columns: {text_cols}
- Missing Values: {dataframe.isnull().sum().sum()}

DATA PREVIEW:
{dataframe.head(10).to_string()}

DATA STATISTICS:
{dataframe.describe().to_string()}"""
            return base_prompt + data_summary
        return base_prompt
    
    def chat(self, user_message: str, dataframe: Optional[pd.DataFrame] = None) -> str:
        try:
            system_prompt = self.build_system_prompt(dataframe)
            
            # Build messages for API
            messages = []
            
            # Add conversation history (last 5 messages to save tokens)
            for msg in self.conversation_history[-5:]:
                messages.append(msg)
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            # Call Groq API
            response = self.client.chat.completions.create(
                model="mixtral-8x7b-32768",  # Fast and powerful
                messages=messages,
                system=system_prompt,
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stop=None,
                stream=False
            )
            
            assistant_message = response.choices[0].message.content
            
            # Store in history
            self.conversation_history.append({"role": "user", "content": user_message})
            self.conversation_history.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
        except Exception as e:
            logger.error(f"Error: {e}")
            return f"❌ Error: {str(e)}\n\nPlease check:\n1. GROQ_API_KEY is set in Streamlit secrets\n2. Your API key is valid\n3. Your request is reasonable"

@st.cache_data
def load_data(file_bytes, file_name: str) -> Optional[pd.DataFrame]:
    try:
        name_lower = file_name.lower()
        if name_lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_bytes))
        elif name_lower.endswith(".xlsx") or name_lower.endswith(".xls"):
            return pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        elif name_lower.endswith(".json"):
            data = json.loads(file_bytes.decode('utf-8'))
            return pd.DataFrame(data) if isinstance(data, list) else pd.json_normalize(data)
        return None
    except Exception as e:
        logger.error(f"File error: {e}")
        st.error(f"Failed to load file: {str(e)}")
        return None

# Main UI
st.title("🤖 Smart AI Data Analyst")
st.markdown("**Монгол / English - Powered by Groq (100% FREE)**")

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Check for API key
    api_key = st.secrets.get("GROQ_API_KEY", None)
    
    if not api_key:
        st.error("❌ GROQ_API_KEY not found in secrets!")
        st.info("""
        **Setup Instructions:**
        1. Get free API key: https://console.groq.com
        2. Go to Streamlit Cloud → Manage App → Secrets
        3. Add: `GROQ_API_KEY = "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"`
        4. Reboot app
        """)
        st.stop()
    
    st.success("✅ Groq API Connected")
    
    st.divider()
    st.header("📂 Data Upload")
    uploaded_file = st.file_uploader("Upload CSV, Excel, or JSON", type=["csv", "xlsx", "json", "xls"])
    
    if uploaded_file:
        df = load_data(uploaded_file.read(), uploaded_file.name)
        if df is not None:
            st.session_state.df = df
            st.success(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns")
            with st.expander("👀 Data Preview"):
                st.dataframe(df.head(10))
                st.metric("Rows", len(df))
                st.metric("Columns", len(df.columns))
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("↻ New Session"):
            st.session_state.df = None
            st.session_state.messages = []
            st.rerun()

# Main content
st.subheader("💬 Chat with Your Data")

if st.session_state.df is None:
    st.info("📋 Upload a file to start analyzing!")
    st.markdown("""
    ### How to use:
    1. Upload a CSV, Excel, or JSON file
    2. Ask questions about your data
    3. Get instant AI insights
    
    ### Example questions:
    - "What are the trends in this data?"
    - "Which columns have the most missing values?"
    - "What's the correlation between columns?"
    - "Can you summarize the key findings?"
    """)
else:
    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("🤔 Analyzing..."):
                try:
                    analyst = GroqDataAnalyst(api_key)
                    response = analyst.chat(prompt, st.session_state.df)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    logger.error(f"Chat error: {e}")

st.divider()
st.markdown("---")
st.markdown("""
**About:** Smart AI Data Analyst using Groq API  
**Status:** ✅ 100% FREE (within Groq free tier)  
**Language:** Монгол / English
""")
