import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re
import json
from datetime import datetime
import logging
from typing import Tuple, Any, Optional, Dict, List
import anthropic

# ==============================
# LOGGING CONFIGURATION
# ==============================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================
# PAGE CONFIGURATION
# ==============================

st.set_page_config(
    page_title="Smart AI Data Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem; 
        font-weight: bold; 
        color: #1f77b4;
    }
    .chat-bubble {
        padding: 10px; 
        border-radius: 10px; 
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .claude-message {
        background-color: #f5f5f5;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE INITIALIZATION
# ==============================

if "df" not in st.session_state:
    st.session_state.df = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "data_context" not in st.session_state:
    st.session_state.data_context = ""

# ==============================
# CLAUDE AI INTEGRATION
# ==============================

class ClaudeDataAnalyst:
    """
    Advanced AI Data Analyst using Claude API.
    Provides natural language understanding and data analysis.
    """
    
    def __init__(self, api_key: str):
        """Initialize Claude client."""
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"
        self.conversation_history = []
    
    def build_system_prompt(self, dataframe: Optional[pd.DataFrame] = None) -> str:
        """Build context-aware system prompt."""
        base_prompt = """You are an expert AI Data Analyst assistant with deep expertise in:
- Statistical analysis and data science
- Data visualization recommendations
- SQL and pandas operations
- Business intelligence insights
- Python and data manipulation

You help users analyze their data through natural conversation. You:
1. Ask clarifying questions when needed
2. Provide actionable insights
3. Suggest visualizations and analysis approaches
4. Explain findings in simple language
5. Offer step-by-step guidance

Always be helpful, accurate, and professional."""

        if dataframe is not None and not dataframe.empty:
            data_summary = f"""

CURRENT DATASET INFORMATION:
- Shape: {dataframe.shape[0]} rows × {dataframe.shape[1]} columns
- Columns: {', '.join(dataframe.columns.tolist())}
- Data types: {dict(dataframe.dtypes).items()}
- Missing values: {dataframe.isnull().sum().to_dict()}
- Numeric columns: {dataframe.select_dtypes(include=['number']).columns.tolist()}
- Text columns: {dataframe.select_dtypes(include=['object', 'category']).columns.tolist()}

Dataset Preview:
{dataframe.head().to_string()}

Provide analysis, insights, and recommendations based on this data."""
            return base_prompt + data_summary
        
        return base_prompt
    
    def chat(self, user_message: str, dataframe: Optional[pd.DataFrame] = None) -> str:
        """
        Send message to Claude and get response.
        
        Args:
            user_message: User's question/request
            dataframe: Current dataframe for context
        
        Returns:
            Claude's response
        """
        try:
            # Add user message to history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Get response from Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.build_system_prompt(dataframe),
                messages=self.conversation_history
            )
            
            # Extract response text
            assistant_message = response.content[0].text
            
            # Add to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return f"❌ Error communicating with Claude: {str(e)}"
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []

# ==============================
# SMART DATA AGENT (HELPER)
# ==============================

class SmartDataAgent:
    """
    NLP-lite data analysis helper.
    Handles quick operations like filtering, grouping, and charting.
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        """Initialize the agent with a dataframe."""
        if dataframe is None or dataframe.empty:
            raise ValueError("Invalid or empty dataframe provided")
        
        self.df = dataframe
        self.numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
        self.text_cols = dataframe.select_dtypes(include=['object', 'category']).columns.tolist()
        self.all_cols = dataframe.columns.tolist()

    def process(self, prompt: str) -> Optional[Tuple[str, Any, str]]:
        """
        Try to process prompt with simple NLP.
        Returns None if Claude should handle it instead.
        """
        try:
            prompt_lower = prompt.lower()
            mentioned_cols = [c for c in self.all_cols if c.lower() in prompt_lower]
            
            if not mentioned_cols:
                return None
            
            target_col = mentioned_cols[0]
            
            # Quick operations
            if any(k in prompt_lower for k in ["дундаж", "average", "mean"]):
                if target_col in self.numeric_cols:
                    val = self.df[target_col].mean()
                    return ("text", f"📊 **{target_col}** average: **{val:,.2f}**", "Average")
            
            if any(k in prompt_lower for k in ["нийт", "sum", "total"]):
                if target_col in self.numeric_cols:
                    val = self.df[target_col].sum()
                    return ("text", f"💰 **{target_col}** sum: **{val:,.2f}**", "Sum")
            
            if any(k in prompt_lower for k in ["максимум", "max", "maximum"]):
                if target_col in self.numeric_cols:
                    val = self.df[target_col].max()
                    return ("text", f"📈 **{target_col}** max: **{val:,.2f}**", "Maximum")
            
            if any(k in prompt_lower for k in ["минимум", "min", "minimum"]):
                if target_col in self.numeric_cols:
                    val = self.df[target_col].min()
                    return ("text", f"📉 **{target_col}** min: **{val:,.2f}**", "Minimum")
            
            # Filtering
            numbers = re.findall(r"[-+]?\d*\.?\d+", prompt_lower)
            if numbers:
                threshold = float(numbers[0])
                
                if ">" in prompt_lower and target_col in self.numeric_cols:
                    filtered_df = self.df[self.df[target_col] > threshold]
                    if len(filtered_df) > 0:
                        return ("dataframe", filtered_df, f"🔍 Filtered: {target_col} > {threshold}")
                
                if "<" in prompt_lower and target_col in self.numeric_cols:
                    filtered_df = self.df[self.df[target_col] < threshold]
                    if len(filtered_df) > 0:
                        return ("dataframe", filtered_df, f"🔍 Filtered: {target_col} < {threshold}")
            
            # Charting
            if any(k in prompt_lower for k in ["график", "chart", "graph", "plot"]):
                if target_col in self.numeric_cols:
                    fig = px.histogram(self.df, x=target_col, title=f"{target_col} Distribution")
                    fig.update_layout(height=400)
                    return ("chart", fig, f"📉 {target_col} Distribution")
                elif target_col in self.text_cols and len(self.numeric_cols) > 0:
                    y_col = self.numeric_cols[0]
                    grouped = self.df.groupby(target_col)[y_col].sum().reset_index().head(10)
                    fig = px.bar(grouped, x=target_col, y=y_col, title=f"{target_col} Analysis")
                    fig.update_layout(height=400)
                    return ("chart", fig, f"📊 {target_col} Analysis")
        
        except Exception as e:
            logger.error(f"Agent error: {e}")
        
        return None

# ==============================
# UTILITY FUNCTIONS
# ==============================

@st.cache_data
def load_data(file_bytes, file_name: str) -> Optional[pd.DataFrame]:
    """Load data from various file formats."""
    try:
        name_lower = file_name.lower()
        
        if name_lower.endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_bytes))
        elif name_lower.endswith(".xlsx"):
            return pd.read_excel(io.BytesIO(file_bytes), engine='openpyxl')
        elif name_lower.endswith(".xls"):
            return pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
        elif name_lower.endswith(".json"):
            data = json.loads(file_bytes.decode('utf-8'))
            if isinstance(data, list):
                return pd.DataFrame(data)
            else:
                return pd.json_normalize(data)
        
        return None
    
    except Exception as e:
        logger.error(f"File loading error: {e}")
        return None

# ==============================
# UI LAYOUT
# ==============================

st.title("🤖 Smart AI Data Analyst with Claude")
st.markdown(
    "**Upload your data and chat with Claude AI for intelligent data analysis!**",
    help="Powered by Claude AI - Ask anything about your data"
)

# ==============================
# SIDEBAR - API KEY & FILE UPLOAD
# ==============================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key Input
    api_key = st.text_input(
        "🔑 Anthropic API Key",
        type="password",
        help="Get your API key from https://console.anthropic.com"
    )
    
    if api_key:
        st.session_state.api_key = api_key
        st.success("✅ API Key configured")
    else:
        st.warning("⚠️ Please enter your Anthropic API Key to use Claude AI")
    
    st.divider()
    
    st.header("📂 Data Source")
    
    uploaded_file = st.file_uploader(
        "Upload CSV, Excel, or JSON file",
        type=["csv", "xlsx", "json", "xls"]
    )
    
    if uploaded_file:
        file_bytes = uploaded_file.read()
        df = load_data(file_bytes, uploaded_file.name)
        
        if df is not None:
            st.session_state.df = df
            st.session_state.file_name = uploaded_file.name
            
            st.success("✅ File loaded successfully!")
            
            with st.expander("📊 Data Info"):
                st.write(f"**Rows:** {len(df):,}")
                st.write(f"**Columns:** {len(df.columns)}")
                st.write(f"**Memory:** {df.memory_usage(deep=True).sum() / 1024:.2f} KB")
            
            with st.expander("👀 Preview"):
                st.dataframe(df.head(10), use_container_width=True)
            
            with st.expander("📈 Statistics"):
                numeric_df = df.select_dtypes(include=['number'])
                if not numeric_df.empty:
                    st.dataframe(numeric_df.describe().T, use_container_width=True)
        
        else:
            st.error("❌ Failed to load file")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset All", use_container_width=True):
            st.session_state.messages = []
            st.session_state.df = None
            st.session_state.file_name = None
            st.rerun()
    
    st.divider()
    st.markdown("""
    ### 💡 Tips
    - Chat naturally with Claude about your data
    - Ask for analysis, insights, or visualizations
    - Use natural language - no special syntax needed
    - Claude understands context from previous messages
    
    ### 🎯 Example Queries
    - "What are the key insights in this data?"
    - "Create a visualization showing sales by region"
    - "Give me a summary of the data"
    - "What patterns do you see?"
    - "How can I improve my sales?"
    """)

# ==============================
# MAIN CHAT INTERFACE
# ==============================

st.subheader("💬 Chat with Claude AI")

# Chat history display
chat_container = st.container()

if not st.session_state.messages and st.session_state.df is None:
    st.info(
        "👋 **Welcome!**\n\n"
        "1. Enter your Anthropic API Key\n"
        "2. Upload a CSV, Excel, or JSON file\n"
        "3. Chat naturally with Claude about your data",
        icon="📋"
    )

with chat_container:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            
            elif msg["type"] == "dataframe":
                st.markdown(f"**{msg.get('desc', '')}**")
                if "full_df" in msg:
                    st.dataframe(msg["full_df"], use_container_width=True)
            
            elif msg["type"] == "chart":
                st.markdown(f"**{msg.get('desc', '')}**")
                if "content_obj" in msg:
                    st.plotly_chart(msg["content_obj"], use_container_width=True)

# Chat input
if prompt := st.chat_input("Ask Claude about your data..."):
    
    # Check requirements
    if not st.session_state.api_key:
        st.error("❌ Please enter your API Key in the sidebar first")
        st.stop()
    
    if st.session_state.df is None:
        st.error("❌ Please upload a data file first")
        st.stop()
    
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "type": "text"
    })
    
    with chat_container:
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
    
    # Process response
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("🤔 Claude is thinking..."):
                try:
                    # First try quick operations with SmartDataAgent
                    agent = SmartDataAgent(st.session_state.df)
                    quick_response = agent.process(prompt)
                    
                    if quick_response:
                        r_type, r_content, r_desc = quick_response
                        
                        if r_type == "text":
                            st.markdown(r_content)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": r_content,
                                "type": "text"
                            })
                        
                        elif r_type == "dataframe":
                            st.markdown(f"**{r_desc}**")
                            st.dataframe(r_content, use_container_width=True)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": r_desc,
                                "type": "dataframe",
                                "full_df": r_content
                            })
                        
                        elif r_type == "chart":
                            st.markdown(f"**{r_desc}**")
                            st.plotly_chart(r_content, use_container_width=True)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": r_desc,
                                "type": "chart",
                                "content_obj": r_content
                            })
                    
                    else:
                        # Use Claude AI for complex queries
                        claude = ClaudeDataAnalyst(st.session_state.api_key)
                        response = claude.chat(prompt, st.session_state.df)
                        
                        st.markdown(response)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response,
                            "type": "text"
                        })
                
                except Exception as e:
                    error_msg = f"❌ Error: {str(e)}"
                    st.error(error_msg)
                    logger.error(f"Chat error: {e}")

# ==============================
# FOOTER
# ==============================

st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px;'>
    🤖 Smart AI Data Analyst v3.0 with Claude | Powered by Anthropic
    </div>
    """,
    unsafe_allow_html=True
)
