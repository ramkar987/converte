import streamlit as st
import pdfplumber
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook

st.set_page_config(page_title="PDF → Excel Converter", layout="wide")
st.title("📄 PDF to Excel Converter")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configurações")
    decimal_sep = st.selectbox("Separador decimal", [".", ","])
    header_row = st.number_input("Linha de início dos dados", min_value=1, value=2)

# Upload
template_file = st.file_uploader("📋 Upload do Template Excel", type=["xlsx"])
pdf_files = st.file_uploader("📁 Upload dos PDFs", type=["pdf"],
                              accept_multiple_files=True)

if st.button("🚀 Processar PDFs") and pdf_files and template_file:
    for pdf in pdf_files:
        with st.expander(f"📄 {pdf.name}", expanded=True):
            with pdfplumber.open(pdf) as f:
                table = f.pages[0].extract_table()
                df = pd.DataFrame(table[1:], columns=table[0])

            st.dataframe(df.head(), use_container_width=True)

            # Gerar Excel para download
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Dados")

            st.download_button(
                label=f"⬇️ Baixar {pdf.name.replace('.pdf','.xlsx')}",
                data=output.getvalue(),
                file_name=pdf.name.replace(".pdf", "_convertido.xlsx"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
