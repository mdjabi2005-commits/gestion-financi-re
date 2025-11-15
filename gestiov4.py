# -*- coding: utf-8 -*-
"""
Created on Tue Nov 11 17:16:10 2025

@author: djabi
"""

from difflib import get_close_matches
import os
import shutil
import sqlite3
import pandas as pd
import pytesseract 
from PIL import Image
import re
import streamlit as st
from datetime import datetime, date, timedelta
from dateutil import parser
from dateutil.relativedelta import relativedelta
from alpha_vantage.timeseries import TimeSeries
import matplotlib.pyplot as plt
import cv2
import numpy as np
from io import BytesIO
from pathlib import Path
from chardet import detect
import logging
import json
import streamlit.components.v1 as components
import plotly.express as px
import plotly.graph_objects as go


# ==============================
# 📄 Configuration Streamlit
# ==============================
st.set_page_config(layout="wide")
st.markdown("""
    <style>
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        font-size: 16px !important;
        padding: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==============================
# 📂 CONFIGURATION DES DOSSIERS
# ==============================
from config import BASE_DIR, DATA_DIR, DB_PATH, TO_SCAN_DIR, SORTED_DIR, REVENUS_A_TRAITER, REVENUS_TRAITES

# Créer les dossiers de logs OCR
OCR_LOGS_DIR = os.path.join(DATA_DIR, "ocr_logs")
os.makedirs(OCR_LOGS_DIR, exist_ok=True)

LOG_PATH = os.path.join(OCR_LOGS_DIR, "pattern_log.json")
OCR_PERFORMANCE_LOG = os.path.join(OCR_LOGS_DIR, "performance_stats.json")
PATTERN_STATS_LOG = os.path.join(OCR_LOGS_DIR, "pattern_stats.json")
OCR_SCAN_LOG = os.path.join(OCR_LOGS_DIR, "scan_history.jsonl")

# === JOURNAL OCR ===
def log_pattern_occurrence(pattern_name: str):
    """Enregistre chaque mot-clé détecté par l'OCR dans un journal JSON."""
    try:
