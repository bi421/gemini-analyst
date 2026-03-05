import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import re
import json
from datetime import datetime

# ==============================
# ТОХИРГОО (CONFIG)
# ==============================

st.set_page_config(
    page_title="Smart AI Analyst",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Загварын засварлалт
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4;}
    .chat-bubble {padding: 10px; border-radius: 10px; margin-bottom: 10px;}
    .stAlert {border-radius: 10px;}
</style>
""", unsafe_allow_html=True)

# ==============================
# SESSION STATE
# ==============================

if "df" not in st.session_state:
    st.session_state.df = None
if "file_name" not in st.session_state:
    st.session_state.file_name = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==============================
# УХААЛАГ АГЕНТ (SMART AGENT)
# ==============================

class SmartDataAgent:
    """
    Пандас датафрэйм дээр суурилсан ердийн хэлний ойлголт (NLP-lite).
    Арифметик, Шүүлт, Бүлгэлэлт, График зурах чадвартай.
    """
    def __init__(self, dataframe):
        self.df = dataframe
        self.numeric_cols = dataframe.select_dtypes(include=['number']).columns.tolist()
        self.text_cols = dataframe.select_dtypes(include=['object', 'category']).columns.tolist()
        self.all_cols = dataframe.columns.tolist()

    def process(self, prompt):
        prompt_lower = prompt.lower()
        
        # 1. Багануудыг танин илрүүлэх (Case insensitive)
        mentioned_cols = [c for c in self.all_cols if c.lower() in prompt_lower]
        
        # Хэрэв ямар ч баганын нэр олдохгүй бол ерөнхий танилцуулга өгнө
        if not mentioned_cols:
            return self._general_response(prompt)

        # Эхний олдсон баганыг голчлон ашиглах (Жич: Хэд хэдэн багана олдвол эхнийг нь авч байна)
        target_col = mentioned_cols[0]

        # --- АРИФМЕТИК (МАТЕМАТИК) ---
        if any(k in prompt_lower for k in ["дундаж", "average", "mean", "дундж"]):
            if target_col in self.numeric_cols:
                val = self.df[target_col].mean()
                return ("text", f"📊 **{target_col}** баганын **дундаж утга** нь: **{val:.2f}**", "Дундаж тооцоолол")
            else:
                return ("text", f"⚠️ '{target_col}' нь тоон төрлийн биш тул дундажийг олж болохгүй.", "Алдаа")

        if any(k in prompt_lower for k in ["нийт", "нийлбэр", "total", "sum", "бүгд"]):
            if target_col in self.numeric_cols:
                val = self.df[target_col].sum()
                return ("text", f"💰 **{target_col}** баганын **нийлбэр** нь: **{val:.2f}**", "Нийлбэр тооцоолол")
            else:
                return ("text", f"⚠️ '{target_col}' нь тоон төрлийн биш тул нийлбэрийг олж болохгүй.", "Алдаа")

        if any(k in prompt_lower for k in ["хамгийн их", "max", "дээд", "их"]):
            if target_col in self.numeric_cols:
                val = self.df[target_col].max()
                row = self.df[self.df[target_col] == val].iloc[0]
                return ("text", f"📈 **{target_col}**-ийн хамгийн их утга: **{val}**.\nМөр: `{row.to_dict()}`", "Хамгийн их утга")
            
        if any(k in prompt_lower for k in ["хамгийн бага", "min", "доод", "бага"]):
            if target_col in self.numeric_cols:
                val = self.df[target_col].min()
                row = self.df[self.df[target_col] == val].iloc[0]
                return ("text", f"📉 **{target_col}**-ийн хамгийн бага утга: **{val}**.\nМөр: `{row.to_dict()}`", "Хамгийн бага утга")

        # --- ШҮҮЛТҮҮР (FILTERING) ---
        # Жишээ: "Price > 100", "Sales < 50", "Age == 25"
        
        # Оператор олох
        op_map = {
            '>': ['>', 'их', 'бага биш'],
            '<': ['<', 'бага', 'их биш'],
            '==': ['==', '=', 'тэнцүү', 'байх']
        }
        
        detected_op = None
        for op, keywords in op_map.items():
            if any(k in prompt_lower for k in keywords):
                detected_op = op
                break
        
        # Тоо олох
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", prompt)
        
        if detected_op and numbers:
            val = float(numbers[0])
            
            try:
                filtered_df = None
                desc = ""
                
                if detected_op == '>':
                    if target_col in self.numeric_cols:
                        filtered_df = self.df[self.df[target_col] > val]
                        desc = f"{target_col} > {val}"
                elif detected_op == '<':
                    if target_col in self.numeric_cols:
                        filtered_df = self.df[self.df[target_col] < val]
                        desc = f"{target_col} < {val}"
                elif detected_op == '==':
                    # Текст байж болох тул тусгай шалгах
                    # Хэрэв тоон багана бол тоогоор, текст бол текстээр шалгана
                    if target_col in self.numeric_cols:
                        filtered_df = self.df[self.df[target_col] == val]
                        desc = f"{target_col} == {val}"
                    else:
                        # Текстэн шүүлт: Жишээ "Category == Food" гэж бичсэн байх магадлалтай
                        # Энд энгийн байдлаар prompt доторх утгыг олж чадахгүй тул тусгай заалт шаардлагатай
                        # Гэхдээ хэрэв хэрэглэгч "Name == Bat" гэвэл "Bat" гэдгийг олж чадна гэж үзье
                        # Энэ жишээнд зөвхөн тоон шүүлтүүрт анхаарлаа хандууллаа.
                        pass

                if filtered_df is not None and len(filtered_df) > 0:
                    return ("dataframe", filtered_df, f"🔍 Шүүлт: {desc} ({len(filtered_df)} мөр олдов)")
                elif filtered_df is not None:
                    return ("text", f"🔍 Ийм нөхцөлтэй өгөгдөл олдсонгүй ({desc}).", "Хариулт")
                    
            except Exception as e:
                return ("text", f"❌ Шүүлт хийхэд алдаа гарлаа: {e}", "Алдаа")

        # --- БҮЛГЭЛЭХ (GROUPING) ---
        if any(k in prompt_lower for k in ["бүлгэлэх", "group", "туруулан", "нийлбэрлэх"]):
            if target_col not in self.numeric_cols and len(self.numeric_cols) > 0:
                val_col = self.numeric_cols[0] 
                try:
                    grouped = self.df.groupby(target_col)[val_col].sum().reset_index().sort_values(by=val_col, ascending=False)
                    # График бас харуулъя
                    fig = px.bar(grouped, x=target_col, y=val_col, title=f"{target_col} -ийн {val_col} нийлбэр")
                    return ("chart_and_df", (fig, grouped), f"📊 Бүлгэлэлт: {target_col} -ийн {val_col} нийлбэр")
                except Exception as e:
                     return ("text", f"❌ Бүлгэлэх боломжгүй: {e}", "Алдаа")

        # --- ГРАФИК (CHART) ---
        if any(k in prompt_lower for k in ["график", "чарт", "chart", "граф", "зура", "диаграм"]):
            try:
                fig = None
                title = f"{target_col}"
                if target_col in self.numeric_cols:
                    fig = px.histogram(self.df, x=target_col, title=title + " Distribution")
                    return ("chart", fig, f"📉 {target_col} тархалт")
                else:
                    # Текст багана бол Бар чарт
                    if len(self.numeric_cols) > 0:
                        y_col = self.numeric_cols[0]
                        fig = px.bar(self.df, x=target_col, y=y_col, title=f"{target_col} vs {y_col}")
                        return ("chart", fig, f"📊 {target_col} -ийн дагуух {y_col}")
            except:
                return ("text", "График зурахад алдаа гарлаа.", "Алдаа")

        # --- ХЭРЭВ ЮУ Ч ОЛДООГҮЙ БОЛ (FALLBACK) ---
        return self._general_response(prompt, context_col=target_col)

    def _general_response(self, prompt, context_col=None):
        base_msg = (
            "Би таны өгөгдлийн дараах асуултуудад хариулж чадна:\n\n"
            "🔢 **Тооцоолол:**\n- `Баганын нэр дундаж`\n- `Баганын нэр нийт`\n- `Баганын нэр хамгийн их/бага`\n\n"
            "🔍 **Шүүлт:**\n- `Баганын нэр > тоо`\n- `Баганын нэр < тоо`\n\n"
            "📊 **Визуал:**\n- `Баганын нэр график зура`\n- `Баганын нэр бүлгэлэх`\n\n"
            f"**Таны өгөгдлийн баганууд:** `{', '.join(self.all_cols)}`"
        )
        
        if "мөр" in prompt.lower() or "row" in prompt.lower():
            return ("text", f"📊 Нийт **{len(self.df)}** мөр өгөгдөл байна.", "Мэдээлэл")
        
        if context_col:
            return ("text", f"Та **'{context_col}'** баганыг дурджээ. Түүний талаар дээрх жагсаалтын дагуу асуулт үүсгэж болно.\n\n{base_msg}", "Тусламж")
            
        return ("text", base_msg, "Тусламж")

# ==============================
# ФАЙЛ УНШИХ ФУНКЦ
# ==============================

def load_data(file):
    try:
        name = file.name.lower()
        if name.endswith(".csv"):
            return pd.read_csv(file)
        elif name.endswith(".xlsx"):
            return pd.read_excel(file, engine='openpyxl')
        elif name.endswith(".json"):
            return pd.json_normalize(json.load(file))
        else:
            return None
    except Exception as e:
        st.error(f"Алдаа: {e}")
        return None

# ==============================
# UI DESIGN (LAYOUT)
# ==============================

st.title("🤖 Smart AI Data Analyst")
st.markdown("Файл оруулж, ердийн хэлээр асуулт асууж машин суралцсан аналитикийг хийгээрэй.")

with st.sidebar:
    st.header("📂 Data Source")
    uploaded_file = st.file_uploader("CSV, Excel, JSON файл сонгоно уу", type=["csv", "xlsx", "json"])
    
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.session_state.file_name = uploaded_file.name
            st.success(f"✅ Амжилттай уншлаа!\nRows: {len(df)}\nCols: {len(df.columns)}")
            
            with st.expander("Өгөгдөл харах"):
                st.dataframe(df.head())
                
            # Quick Stats
            st.subheader("Quick Stats")
            numeric_df = df.select_dtypes(include=['number'])
            if not numeric_df.empty:
                st.write(numeric_df.describe().T)
        else:
            st.error("Файлыг унших боломжгүй.")

    if st.button("Чатыг цэвэрлэх"):
        st.session_state.messages = []
        st.rerun()

# ==============================
# CHAT INTERFACE
# ==============================

chat_container = st.container()

# History display
with chat_container:
    if not st.session_state.messages and st.session_state.df is None:
        st.info("👋 Сайн байна уу! Өгөгдөл оруулж эхлэнэ үү.")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            elif msg["type"] == "dataframe":
                st.markdown(f"**{msg['desc']}**")
                st.dataframe(msg["content"])
            elif msg["type"] == "chart":
                st.markdown(f"**{msg['desc']}**")
                st.plotly_chart(msg["content"], use_container_width=True)
            elif msg["type"] == "chart_and_df":
                st.markdown(f"**{msg['desc']}**")
                fig, df_data = msg["content"]
                st.plotly_chart(fig, use_container_width=True)
                with st.expander("Өгөгдөл харах"):
                    st.dataframe(df_data)

# Input
if prompt := st.chat_input("Өгөгдлөөс асуулт асуух..."):
    
    # 1. User Message
    st.session_state.messages.append({"role": "user", "content": prompt, "type": "text"})
    with chat_container:
        with st.chat_message("user"):
            st.markdown(prompt)

    # 2. AI Response Logic
    if st.session_state.df is not None:
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Боловсруулж байна..."):
                    agent = SmartDataAgent(st.session_state.df)
                    r_type, r_content, r_desc = agent.process(prompt)
                    
                    # Render and Save
                    if r_type == "text":
                        st.markdown(r_content)
                        st.session_state.messages.append({"role": "assistant", "content": r_content, "type": "text", "desc": r_desc})
                    
                    elif r_type == "dataframe":
                        st.markdown(f"**{r_desc}**")
                        st.dataframe(r_content)
                        # Хэт их хэмжээтэй дата хадгалахгүйн тулд зөвхөн эхний 10 мөрийг түүхэнд хадгалах
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": r_content.head(10).to_csv(index=False), 
                            "type": "dataframe", 
                            "desc": r_desc,
                            "full_df": r_content # Full df-г чадах бол хадгалах
                        })
                    
                    elif r_type == "chart":
                        st.markdown(f"**{r_desc}**")
                        st.plotly_chart(r_content, use_container_width=True)
                        st.session_state.messages.append({"role": "assistant", "content": None, "type": "chart", "desc": r_desc, "content_obj": r_content})
                        
                    elif r_type == "chart_and_df":
                        fig, df_result = r_content
                        st.markdown(f"**{r_desc}**")
                        st.plotly_chart(fig, use_container_width=True)
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": None, 
                            "type": "chart_and_df", 
                            "desc": r_desc, 
                            "content": (fig, df_result)
                        })
    else:
        with chat_container:
            with st.chat_message("assistant"):
                st.warning("Системд өгөгдөл ороогүй байна. Зүүн талаас файл оруулна уу.")
                st.session_state.messages.append({"role": "assistant", "content": "Файл оруулна уу", "type": "text"})
