import streamlit as st
from groq import Groq
import google.generativeai as genai
import pandas as pd
from PyPDF2 import PdfReader
import docx
import PIL.Image
import base64
import io
import requests
from bs4 import BeautifulSoup
import re

# 1. Тохиргоо
st.set_page_config(
    page_title="Groq AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS
st.markdown("""
<style>
  html, body, [class*="css"] { font-size: 16px !important; }
  .stChatMessage { font-size: 16px !important; line-height: 1.6 !important; }
  .stChatInputContainer textarea { font-size: 16px !important; padding: 12px !important; }
  .stButton > button { font-size: 16px !important; padding: 12px 20px !important; border-radius: 12px !important; width: 100% !important; }
  h1 { font-size: 24px !important; }
  h2 { font-size: 20px !important; }
  h3 { font-size: 18px !important; }
  .stFileUploader label { font-size: 15px !important; }
  .stSelectbox label, .stSelectbox div { font-size: 15px !important; }
  .stTextInput input, .stTextArea textarea { font-size: 16px !important; }
  .stTabs [data-baseweb="tab"] { font-size: 15px !important; padding: 10px 16px !important; }
  .stCaption { font-size: 14px !important; }
  @media (max-width: 768px) {
    .main .block-container { padding: 1rem 0.5rem !important; max-width: 100% !important; }
    h1 { font-size: 22px !important; }
    .stButton > button { font-size: 15px !important; padding: 10px 16px !important; }
  }
</style>
""", unsafe_allow_html=True)
