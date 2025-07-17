import streamlit as st
import pandas as pd
import os
import math
from fpdf import FPDF
from datetime import datetime

LOGO_PATH = "BTP_ogo_hands_transparent_small.png"

# Load material data
@st.cache_data
def load_materials():
    file_path = os.path.join(os.path.dirname(__file__), 'materials.csv')
    return pd.read_csv(file_path)

# Export to PDF with header and logo
def generate_pdf(df, filename, project_name):
    pdf = FPDF()
    pdf.add_page()
    if os.path.exists(LOGO_PATH):
        pdf.image(LOGO_PATH, x=10, y=8, w=25)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, "Build & Trim PRO - Sheetrock Estimate", ln=1, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 8, f"Project: {project_name}", ln=1)
    pdf.cell(200, 8, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=1)
    pdf.ln(4)
    pdf.set_font("Courier", size=9)
    col_widths = [30, 20, 25, 25, 25, 30, 30, 30]
    header = df.columns.tolist()
    for i, col in enumerate(header):
        pdf.cell(col_widths[i % len(col_widths)], 10, str(col), border=1)
    pdf.ln()
    for _, row in df.iterrows():
        for i, col in enumerate(header):
            value = str(row[col])
            pdf.cell(col_widths[i % len(col_widths)], 10, value, border=1)
        pdf.ln()
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(200, 8, "Build & Trim PRO", ln=1, align='C')
    pdf.cell(200, 8, "buildandtrimPR.com | buildandtrimPRO@gmail.com | 913 687 7602", ln=1, align='C')
    pdf.output(filename)

def display_dataframe(df):
    st.dataframe(df.style.format({
        'Material Cost ($)': '${:,.2f}',
        'Labor Cost ($)': '${:,.2f}',
        'Total Cost ($)': '${:,.2f}',
        'Unit Price ($)': '${:,.2f}',
        'Labor per Unit ($)': '${:,.2f}'
    }))

