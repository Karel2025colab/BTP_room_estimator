import streamlit as st
import pandas as pd
import os
import math
from fpdf import FPDF
from datetime import datetime

LOGO_PATH = "BTP_ogo_hands_transparent_small.png"

@st.cache_data
def load_materials():
    file_path = os.path.join(os.path.dirname(__file__), 'materials.csv')
    return pd.read_csv(file_path)

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

def format_currency(val):
    try:
        return f"${float(val):,.2f}"
    except:
        return val

def display_dataframe(df):
    st.dataframe(df.style.format({
        'Material Cost ($)': format_currency,
        'Labor Cost ($)': format_currency,
        'Total Cost ($)': format_currency,
        'Unit Price ($)': format_currency,
        'Labor per Unit ($)': format_currency
    }))

def calculate_quick(materials_df, area, complexity_factor):
    results = []
    total_cost = 0
    total_material_cost = 0
    total_labor_cost = 0

    for _, row in materials_df.iterrows():
        raw_units = (area / row['coverage_sqft']) * (1 + row['waste_factor'] + complexity_factor)
        units_needed = math.ceil(raw_units)
        material_cost = units_needed * row['unit_cost_usd']
        labor_cost = units_needed * row['labor_cost_per_unit']
        total = material_cost + labor_cost

        results.append({
            'Material': row['material'],
            'Units Needed': units_needed,
            'Unit Coverage (sqft)': row['coverage_sqft'],
            'Unit Price ($)': row['unit_cost_usd'],
            'Labor per Unit ($)': row['labor_cost_per_unit'],
            'Material Cost ($)': round(material_cost, 2),
            'Labor Cost ($)': round(labor_cost, 2),
            'Total Cost ($)': round(total, 2)
        })

        total_material_cost += material_cost
        total_labor_cost += labor_cost
        total_cost += total

    df = pd.DataFrame(results)
    totals_row = pd.DataFrame([{
        'Material': 'TOTAL',
        'Units Needed': '',
        'Unit Coverage (sqft)': '',
        'Unit Price ($)': '',
        'Labor per Unit ($)': '',
        'Material Cost ($)': round(total_material_cost, 2),
        'Labor Cost ($)': round(total_labor_cost, 2),
        'Total Cost ($)': round(total_cost, 2)
    }])
    df = pd.concat([df, totals_row], ignore_index=True)
    return df, round(total_cost, 2)

def calculate_detailed(materials_df, rooms):
    all_results = []
    grand_total = 0

    for room in rooms:
        length = room['length']
        width = room['width']
        height = room['height']
        doors = room['doors']
        windows = room['windows']

        wall_area = 2 * height * (length + width)
        ceiling_area = length * width
        door_area = doors * 21
        window_area = windows * 12
        total_area = max(wall_area + ceiling_area - (door_area + window_area), 0)

        room_results, room_cost = calculate_quick(materials_df, total_area, 0.10)
        room_results.insert(0, 'Room', room['name'])
        all_results.append(room_results)
        grand_total += room_cost

    full_df = pd.concat(all_results, ignore_index=True)
    return full_df, round(grand_total, 2)

# --- Streamlit UI ---
st.title("📐 Sheetrock Installation Estimator")
project_name = st.text_input("Project Name", "Untitled Project")

materials = load_materials()
mode = st.radio("Choose estimate type:", ["Quick Estimate (sq ft)", "Detailed Estimate (by room)"])

if mode == "Quick Estimate (sq ft)":
    area = st.number_input("Total area to cover (sq ft)", min_value=0.0, value=200.0, step=10.0)
    complexity = st.slider("Complexity factor (corners, curves)", 0.0, 0.30, 0.05, step=0.01)

    if st.button("Estimate Costs"):
        result_df, total = calculate_quick(materials, area, complexity)

        st.subheader("📊 Material Breakdown")
        display_dataframe(result_df)
        st.success(f"💰 Estimated Total Cost: **${total}**")

        with pd.ExcelWriter("estimate.xlsx", engine="openpyxl") as writer:
            result_df.to_excel(writer, index=False)
        with open("estimate.xlsx", "rb") as f:
            st.download_button("📥 Download Estimate (Excel)", f, "sheetrock_estimate.xlsx")

        generate_pdf(result_df, "estimate.pdf", project_name)
        with open("estimate.pdf", "rb") as f:
            st.download_button("📄 Download Estimate (PDF)", f, "sheetrock_estimate.pdf")

else:
    st.markdown("Add rooms below to calculate estimate:")
    rooms = []
    room_count = st.number_input("How many rooms?", min_value=1, max_value=10, step=1)

    for i in range(int(room_count)):
        st.markdown(f"### 🏠 Room {i+1}")
        name = st.text_input(f"Room {i+1} name", value=f"Room {i+1}", key=f"name_{i}")
        length = st.number_input(f"Length (ft) - Room {i+1}", min_value=1.0, value=12.0, key=f"length_{i}")
        width = st.number_input(f"Width (ft) - Room {i+1}", min_value=1.0, value=10.0, key=f"width_{i}")
        height = st.number_input(f"Height (ft) - Room {i+1}", min_value=1.0, value=8.0, key=f"height_{i}")
        doors = st.number_input(f"# Doors - Room {i+1}", min_value=0, value=1, key=f"doors_{i}")
        windows = st.number_input(f"# Windows - Room {i+1}", min_value=0, value=1, key=f"windows_{i}")

        rooms.append({
            'name': name,
            'length': length,
            'width': width,
            'height': height,
            'doors': doors,
            'windows': windows
        })

    if st.button("Estimate Room-Based Costs"):
        detailed_df, total = calculate_detailed(materials, rooms)

        st.subheader("📊 Room-by-Room Breakdown")
        display_dataframe(detailed_df)
        st.success(f"🧾 Grand Total Estimate: **${total}**")

        with pd.ExcelWriter("detailed_estimate.xlsx", engine="openpyxl") as writer:
            detailed_df.to_excel(writer, index=False)
        with open("detailed_estimate.xlsx", "rb") as f:
            st.download_button("📥 Download Detailed Estimate (Excel)", f, "sheetrock_detailed_estimate.xlsx")

        generate_pdf(detailed_df, "detailed_estimate.pdf", project_name)
        with open("detailed_estimate.pdf", "rb") as f:
            st.download_button("📄 Download Detailed Estimate (PDF)", f, "sheetrock_detailed_estimate.pdf")
