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

# ==============================
# LOGGING CONFIGURATION
# ==============================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================
# CONFIGURATION (ТОХИРГОО)
# ==============================

st.set_page_config(
    page_title="Smart AI Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
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
    .stAlert {
        border-radius: 10px;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .error-box {
        background-color: #ffcccc;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #ff0000;
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
if "agent_mode" not in st.session_state:
    st.session_state.agent_mode = "smart"

# ==============================
# UTILITY FUNCTIONS
# ==============================

def validate_dataframe(df: Optional[pd.DataFrame]) -> bool:
    """Validate if dataframe is valid and not empty."""
    if df is None:
        return False
    if df.empty:
        return False
    return True

def safe_numeric_conversion(value: str) -> Optional[float]:
    """Safely convert string to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def extract_numbers(text: str) -> List[float]:
    """Extract all numbers from text."""
    try:
        pattern = r"[-+]?\d*\.?\d+"
        matches = re.findall(pattern, text)
        return [float(m) for m in matches if m]
    except Exception as e:
        logger.error(f"Error extracting numbers: {e}")
        return []

def extract_column_names(text: str, available_cols: List[str]) -> List[str]:
    """Extract column names from text (case-insensitive)."""
    text_lower = text.lower()
    return [col for col in available_cols if col.lower() in text_lower]

# ==============================
# SMART DATA AGENT CLASS
# ==============================

class SmartDataAgent:
    """
    Advanced NLP-lite data analysis agent.
    Supports: arithmetic operations, filtering, grouping, chart generation.
    """
    
    def __init__(self, dataframe: pd.DataFrame):
        """Initialize the agent with a dataframe."""
        if not validate_dataframe(dataframe):
            raise ValueError("Invalid or empty dataframe provided")
        
        self.df = dataframe
        self.numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
        self.text_cols = dataframe.select_dtypes(include=['object', 'category']).columns.tolist()
        self.all_cols = dataframe.columns.tolist()
        self.datetime_cols = dataframe.select_dtypes(include=['datetime']).columns.tolist()

    def process(self, prompt: str) -> Tuple[str, Any, str]:
        """
        Process user prompt and return (type, content, description).
        
        Types: 'text', 'dataframe', 'chart', 'chart_and_df'
        """
        try:
            prompt_lower = prompt.lower()
            
            # Extract column names
            mentioned_cols = extract_column_names(prompt, self.all_cols)
            
            if not mentioned_cols:
                return self._general_response(prompt)
            
            target_col = mentioned_cols[0]
            
            # Route to appropriate handler
            response = self._handle_arithmetic(prompt_lower, target_col)
            if response:
                return response
            
            response = self._handle_filtering(prompt_lower, target_col)
            if response:
                return response
            
            response = self._handle_grouping(prompt_lower, target_col)
            if response:
                return response
            
            response = self._handle_charting(prompt_lower, target_col)
            if response:
                return response
            
            response = self._handle_info_queries(prompt_lower, target_col)
            if response:
                return response
            
            return self._general_response(prompt, context_col=target_col)
            
        except Exception as e:
            logger.error(f"Error processing prompt: {e}")
            return ("text", f"❌ **Алдаа гарлаа:** {str(e)}", "Системийн алдаа")

    def _handle_arithmetic(self, prompt_lower: str, target_col: str) -> Optional[Tuple[str, Any, str]]:
        """Handle arithmetic operations (sum, average, min, max)."""
        if target_col not in self.numeric_cols:
            return None
        
        # Average
        if any(k in prompt_lower for k in ["дундаж", "average", "mean", "дундж"]):
            val = self.df[target_col].mean()
            return ("text", f"📊 **{target_col}** баганын **дундаж утга:** **{val:,.2f}**", "Дундаж")
        
        # Sum
        if any(k in prompt_lower for k in ["нийт", "нийлбэр", "total", "sum", "бүгд"]):
            val = self.df[target_col].sum()
            return ("text", f"💰 **{target_col}** баганын **нийлбэр:** **{val:,.2f}**", "Нийлбэр")
        
        # Maximum
        if any(k in prompt_lower for k in ["хамгийн их", "max", "дээд", "максимум"]):
            val = self.df[target_col].max()
            idx = self.df[target_col].idxmax()
            row_info = self.df.loc[idx].to_dict()
            return ("text", 
                f"📈 **{target_col}** -ийн **максимум утга:** **{val:,.2f}**\n\n"
                f"Мөрийн мэдээлэл:\n```\n{json.dumps(row_info, ensure_ascii=False, indent=2)}\n```",
                "Максимум утга")
        
        # Minimum
        if any(k in prompt_lower for k in ["хамгийн бага", "min", "доод", "минимум"]):
            val = self.df[target_col].min()
            idx = self.df[target_col].idxmin()
            row_info = self.df.loc[idx].to_dict()
            return ("text",
                f"📉 **{target_col}** -ийн **минимум утга:** **{val:,.2f}**\n\n"
                f"Мөрийн мэдээлэл:\n```\n{json.dumps(row_info, ensure_ascii=False, indent=2)}\n```",
                "Минимум утг��")
        
        # Count
        if any(k in prompt_lower for k in ["тоо", "count", "хэд"]):
            val = self.df[target_col].count()
            return ("text", f"🔢 **{target_col}** баганад **{val}** бичлэг байна.", "Бичлэгийн тоо")
        
        # Standard deviation
        if any(k in prompt_lower for k in ["стандарт хазайлт", "std", "deviation"]):
            val = self.df[target_col].std()
            return ("text", f"📊 **{target_col}** баганын **стандарт хазайлт:** **{val:,.2f}**", "Стандарт хазайлт")
        
        return None

    def _handle_filtering(self, prompt_lower: str, target_col: str) -> Optional[Tuple[str, Any, str]]:
        """Handle filtering operations (>, <, ==, !=)."""
        numbers = extract_numbers(prompt_lower)
        
        if not numbers:
            return None
        
        threshold = numbers[0]
        op_map = {
            '>': ['>', 'их', 'бага биш'],
            '<': ['<', 'бага', 'их биш'],
            '==': ['==', '=', 'тэнцүү', 'байх'],
            '!=': ['!=', '≠', 'тэнцүү биш']
        }
        
        detected_op = None
        for op, keywords in op_map.items():
            if any(k in prompt_lower for k in keywords):
                detected_op = op
                break
        
        if not detected_op:
            return None
        
        try:
            filtered_df = None
            desc = ""
            
            if target_col in self.numeric_cols:
                if detected_op == '>':
                    filtered_df = self.df[self.df[target_col] > threshold]
                    desc = f"{target_col} > {threshold}"
                elif detected_op == '<':
                    filtered_df = self.df[self.df[target_col] < threshold]
                    desc = f"{target_col} < {threshold}"
                elif detected_op == '==':
                    filtered_df = self.df[self.df[target_col] == threshold]
                    desc = f"{target_col} == {threshold}"
                elif detected_op == '!=':
                    filtered_df = self.df[self.df[target_col] != threshold]
                    desc = f"{target_col} ≠ {threshold}"
            
            if filtered_df is not None:
                if len(filtered_df) > 0:
                    return ("dataframe", filtered_df, 
                        f"🔍 Шүүлт: {desc} ({len(filtered_df)} мөр)")
                else:
                    return ("text", 
                        f"🔍 Ийм нөхцөлтэй өгөгдөл олдсонгүй ({desc}).",
                        "Хариулт")
        
        except Exception as e:
            logger.error(f"Filtering error: {e}")
            return ("text", f"❌ Шүүлт хийхэд алдаа гарлаа: {str(e)}", "Алдаа")
        
        return None

    def _handle_grouping(self, prompt_lower: str, target_col: str) -> Optional[Tuple[str, Any, str]]:
        """Handle grouping and aggregation operations."""
        if not any(k in prompt_lower for k in ["бүлгэлэх", "group", "туруулан", "нийлбэрлэх"]):
            return None
        
        if target_col in self.numeric_cols:
            return None
        
        if len(self.numeric_cols) == 0:
            return ("text", "⚠️ Тоон баганагүй тул бүлгэлэх боломжгүй.", "Анхааруулга")
        
        try:
            val_col = self.numeric_cols[0]
            grouped = self.df.groupby(target_col)[val_col].sum().reset_index().sort_values(by=val_col, ascending=False)
            
            fig = px.bar(
                grouped, 
                x=target_col, 
                y=val_col,
                title=f"{target_col} -ийн {val_col} нийлбэр",
                labels={target_col: target_col, val_col: f"{val_col} (нийлбэр)"}
            )
            fig.update_layout(hovermode='x unified', height=400)
            
            return ("chart_and_df", (fig, grouped), f"📊 Бүлгэлэлт: {target_col}")
        
        except Exception as e:
            logger.error(f"Grouping error: {e}")
            return ("text", f"❌ Бүлгэлэх боломжгүй: {str(e)}", "Алдаа")

    def _handle_charting(self, prompt_lower: str, target_col: str) -> Optional[Tuple[str, Any, str]]:
        """Handle chart generation."""
        if not any(k in prompt_lower for k in ["график", "чарт", "chart", "граф", "зура", "диаграм"]):
            return None
        
        try:
            if target_col in self.numeric_cols:
                fig = px.histogram(
                    self.df,
                    x=target_col,
                    title=f"{target_col} -ийн тархалт",
                    nbins=30,
                    marginal="box"
                )
                fig.update_layout(height=400, hovermode='x unified')
                return ("chart", fig, f"📉 {target_col} тархалт")
            
            elif target_col in self.text_cols or target_col in self.datetime_cols:
                if len(self.numeric_cols) > 0:
                    y_col = self.numeric_cols[0]
                    count_df = self.df.groupby(target_col)[y_col].sum().reset_index().sort_values(by=y_col, ascending=False).head(10)
                    
                    fig = px.bar(
                        count_df,
                        x=target_col,
                        y=y_col,
                        title=f"{target_col} -ийн {y_col}",
                        labels={target_col: target_col, y_col: f"{y_col} (нийлбэр)"}
                    )
                    fig.update_layout(height=400, hovermode='x unified')
                    return ("chart", fig, f"📊 {target_col} дашборд")
                else:
                    value_counts = self.df[target_col].value_counts().head(10)
                    fig = px.bar(
                        x=value_counts.index,
                        y=value_counts.values,
                        title=f"{target_col} -ийн тоо",
                        labels={'x': target_col, 'y': 'Тоо'}
                    )
                    fig.update_layout(height=400)
                    return ("chart", fig, f"📊 {target_col} давтамж")
        
        except Exception as e:
            logger.error(f"Charting error: {e}")
            return ("text", f"❌ График зурахад алдаа: {str(e)}", "Алдаа")
        
        return None

    def _handle_info_queries(self, prompt_lower: str, target_col: str) -> Optional[Tuple[str, Any, str]]:
        """Handle information queries."""
        if any(k in prompt_lower for k in ["мөр", "row", "бичлэг"]):
            return ("text", 
                f"📊 Нийт **{len(self.df)}** мөр өгөгдөл байна.\n"
                f"🔍 **Баганууд:** {len(self.df.columns)} ширхэг\n"
                f"💾 **Хэмжээ:** {self.df.memory_usage(deep=True).sum() / 1024:.2f} KB",
                "Мэдээлэл")
        
        if any(k in prompt_lower for k in ["баганыг", "column", "шинж", "төрөл"]):
            dtype = str(self.df[target_col].dtype)
            unique = self.df[target_col].nunique()
            missing = self.df[target_col].isnull().sum()
            
            return ("text",
                f"📋 **{target_col}** баганын мэдээлэл:\n"
                f"- **Төрөл:** {dtype}\n"
                f"- **Өөр утга:** {unique}\n"
                f"- **Дутсан утга:** {missing}",
                "Баганын мэдээлэл")
        
        return None

    def _general_response(self, prompt: str, context_col: Optional[str] = None) -> Tuple[str, str, str]:
        """Provide general help response."""
        base_msg = (
            "🤖 **Та дараах дүүргээр асуулт асууж болно:**\n\n"
            "### 🔢 Тооцоолол\n"
            "- `[Баганы нэр] дундаж` - дундаж утгыг олох\n"
            "- `[Баганы нэр] нийт` - нийлбэрийг олох\n"
            "- `[Баганы нэр] хамгийн их/бага` - максимум/минимум\n"
            "- `[Баганы нэр] стандарт хазайлт` - хэлбэлзэл\n\n"
            "### 🔍 Шүүлт\n"
            "- `[Баганы нэр] > 100` - ямар утгаас их\n"
            "- `[Баганы нэр] < 50` - ямар утгаас бага\n"
            "- `[Баганы нэр] = 25` - тэнцүү байх\n\n"
            "### 📊 Визуал\n"
            "- `[Баганы нэр] график` - график зурах\n"
            "- `[Баганы нэр] бүлгэлэх` - бүлгүүдэр хуваах\n\n"
            "### ℹ️ Мэдээлэл\n"
            f"- **Баганууд:** `{', '.join(self.all_cols)}`\n"
            f"- **Тоон баганууд:** `{', '.join(self.numeric_cols) if self.numeric_cols else 'байхгүй'}`"
        )
        
        if context_col:
            return ("text", 
                f"💡 Та **'{context_col}'** баганыг сонгосон байна.\n\n{base_msg}",
                "Тусламж")
        
        return ("text", base_msg, "Тусламж")

# ==============================
# FILE LOADING FUNCTIONS
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
        
        elif name_lower.endswith(".json"):
            data = json.loads(file_bytes.decode('utf-8'))
            if isinstance(data, list):
                return pd.DataFrame(data)
            else:
                return pd.json_normalize(data)
        
        elif name_lower.endswith(".xls"):
            return pd.read_excel(io.BytesIO(file_bytes), engine='xlrd')
        
        else:
            return None
    
    except Exception as e:
        logger.error(f"File loading error: {e}")
        return None

def format_dataframe_display(df: pd.DataFrame) -> str:
    """Format dataframe info for display."""
    info = f"""
    **Өгөгдлийн боловсруулалт:**
    - 📊 **Мөрүүд:** {len(df):,}
    - 📋 **Баганууд:** {len(df.columns)}
    - 💾 **Хэмжээ:** {df.memory_usage(deep=True).sum() / 1024:.2f} KB
    """
    return info

# ==============================
# UI LAYOUT
# ==============================

st.title("🤖 Smart AI Data Analyst")
st.markdown(
    "**Файл оруулж, ердийн хэлээр асуулт асууж өнгөрөөтэй дата анализ хийцгээе.**",
    help="CSV, Excel эсвэл JSON форматын файлыг оруулна уу."
)

# ==============================
# SIDEBAR
# ==============================

with st.sidebar:
    st.header("📂 Өгөгдлийн сорц")
    
    uploaded_file = st.file_uploader(
        "CSV, Excel, JSON файл сонгоно уу",
        type=["csv", "xlsx", "json", "xls"],
        help="Дүүргэж байгаа файл оруулна уу"
    )
    
    if uploaded_file:
        file_bytes = uploaded_file.read()
        df = load_data(file_bytes, uploaded_file.name)
        
        if df is not None:
            st.session_state.df = df
            st.session_state.file_name = uploaded_file.name
            
            st.success("✅ Амжилттай уншлаа!")
            
            with st.expander("📊 Өгөгдлийн нэмэлт мэдээлэл"):
                st.markdown(format_dataframe_display(df))
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Мөр", f"{len(df):,}")
                with col2:
                    st.metric("Баганa", len(df.columns))
                with col3:
                    st.metric("Дутсан", df.isnull().sum().sum())
            
            with st.expander("👀 Өгөгдлийг үзэх"):
                st.dataframe(df.head(10), use_container_width=True)
            
            with st.expander("📈 Статистик мэдээлэл"):
                numeric_df = df.select_dtypes(include=['number'])
                if not numeric_df.empty:
                    st.dataframe(numeric_df.describe().T, use_container_width=True)
                else:
                    st.info("Тоон өгөгдөл байхгүй")
            
            with st.expander("🔧 Баганын төрлүүд"):
                dtype_df = pd.DataFrame({
                    "Баганы нэр": df.columns,
                    "Төрөл": [str(dtype) for dtype in df.dtypes]
                })
                st.dataframe(dtype_df, use_container_width=True)
        
        else:
            st.error("❌ Файлыг унших боломжгүй. Файлын форматыг шалгана уу.")
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Чатыг цэвэрлэх", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    
    with col2:
        if st.button("🔄 Дахин ачаалах", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.divider()
    st.markdown("**ℹ️ Мэдээлэл**")
    st.info(
        "💡 Энэ приложение нь дата анализын хялбар AI туслах үйлчилгээ юм. "
        "Файл оруулж ердийн хэлээр асуулт асуугаараа дата эрэлхийлэй.",
        icon="ℹ️"
    )

# ==============================
# MAIN CHAT INTERFACE
# ==============================

chat_container = st.container()

# Display chat history
with chat_container:
    if not st.session_state.messages and st.session_state.df is None:
        st.info(
            "👋 **Сайн байна уу!**\n\n"
            "Зүүн талын панелээс CSV, Excel эсвэл JSON файл оруулж эхэлнэ үү. "
            "Файл оруулсны дараа та энд дата анализын асуулт асуух боломжтой болно.",
            icon="📋"
        )
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            
            elif msg["type"] == "dataframe":
                st.markdown(f"**{msg.get('desc', '')}**")
                # Recover full dataframe if available
                if "full_df" in msg:
                    st.dataframe(msg["full_df"], use_container_width=True)
                else:
                    st.dataframe(msg["content"], use_container_width=True)
            
            elif msg["type"] == "chart":
                st.markdown(f"**{msg.get('desc', '')}**")
                if "content_obj" in msg:
                    st.plotly_chart(msg["content_obj"], use_container_width=True)
            
            elif msg["type"] == "chart_and_df":
                st.markdown(f"**{msg.get('desc', '')}**")
                if "content" in msg:
                    fig, df_data = msg["content"]
                    st.plotly_chart(fig, use_container_width=True)
                    with st.expander("📊 Өгөгдлийг үзэх"):
                        st.dataframe(df_data, use_container_width=True)

# ==============================
# CHAT INPUT & RESPONSE
# ==============================

if prompt := st.chat_input("Өгөгдлийн талаар асуулт асуух...", key="chat_input"):
    
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "type": "text"
    })
    
    with chat_container:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)
    
    # Process response
    if st.session_state.df is not None and validate_dataframe(st.session_state.df):
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("⏳ Боловсруулж байна..."):
                    try:
                        agent = SmartDataAgent(st.session_state.df)
                        r_type, r_content, r_desc = agent.process(prompt)
                        
                        # Render and store response
                        if r_type == "text":
                            st.markdown(r_content)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": r_content,
                                "type": "text",
                                "desc": r_desc
                            })
                        
                        elif r_type == "dataframe":
                            st.markdown(f"**{r_desc}**")
                            st.dataframe(r_content, use_container_width=True)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": r_content.head(10).to_csv(index=False),
                                "type": "dataframe",
                                "desc": r_desc,
                                "full_df": r_content
                            })
                        
                        elif r_type == "chart":
                            st.markdown(f"**{r_desc}**")
                            st.plotly_chart(r_content, use_container_width=True)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": None,
                                "type": "chart",
                                "desc": r_desc,
                                "content_obj": r_content
                            })
                        
                        elif r_type == "chart_and_df":
                            fig, df_result = r_content
                            st.markdown(f"**{r_desc}**")
                            st.plotly_chart(fig, use_container_width=True)
                            with st.expander("📊 Өгөгдлийг үзэх"):
                                st.dataframe(df_result, use_container_width=True)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": None,
                                "type": "chart_and_df",
                                "desc": r_desc,
                                "content": (fig, df_result)
                            })
                    
                    except Exception as e:
                        error_msg = f"❌ Нэгэнгүүлэх боломжгүй: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"Processing error: {e}")
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg,
                            "type": "text",
                            "desc": "Алдаа"
                        })
    
    else:
        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                warning_msg = (
                    "⚠️ **Файл оруулна уу!**\n\n"
                    "Дата анализ хийхийн тулд эхлээд зүүн талын панелээс CSV, "
                    "Excel эсвэл JSON файл оруулна уу."
                )
                st.warning(warning_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": warning_msg,
                    "type": "text",
                    "desc": "Анхааруулга"
                })

# ==============================
# FOOTER
# ==============================

st.divider()
st.markdown(
    """
    <div style='text-align: center; color: #888; font-size: 12px;'>
    🤖 Smart AI Data Analyst v2.0 | 
    Made with ❤️ using Streamlit & Pandas
    </div>
    """,
    unsafe_allow_html=True
)
