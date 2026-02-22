import streamlit as st
import pandas as pd
from io import BytesIO
from utils.pdf_extractor import extrair_pdf
from utils.data_cleaner import limpar_dados
from utils.excel_writer import gerar_excel

st.set_page_config(
    page_title="PDF → Excel Converter",
    page_icon="📄",
    layout="wide"
)

# ─── Cabeçalho ────────────────────────────────────────────────
st.title("📄 PDF to Excel Converter")
st.caption("Converta PDFs com tabelas para Excel, alinhados ao seu template.")

# ─── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Configurações")
    decimal_sep  = st.selectbox("Separador decimal", [".", ","])
    encoding     = st.selectbox("Encoding do PDF", ["utf-8", "latin-1"])
    header_row   = st.number_input("Linha de dados no template", min_value=1, value=2)
    modo_extracao = st.radio("Modo de extração", ["Automático", "Forçar pdfplumber", "Forçar OCR"])
    st.divider()
    st.markdown("**ℹ️ Sobre**")
    st.markdown("App open-source. [Ver no GitHub](https://github.com/SEU_USUARIO/pdf-excel-converter)")

# ─── Upload ───────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    template_file = st.file_uploader("📋 Template Excel (.xlsx)", type=["xlsx"])

with col2:
    pdf_files = st.file_uploader(
        "📁 PDFs para converter",
        type=["pdf"],
        accept_multiple_files=True
    )

st.divider()

# ─── Processamento ────────────────────────────────────────────
if st.button("🚀 Processar PDFs", use_container_width=True, type="primary"):

    if not template_file:
        st.error("❌ Faça upload do template Excel antes de processar.")
        st.stop()

    if not pdf_files:
        st.error("❌ Faça upload de pelo menos um PDF.")
        st.stop()

    template_bytes = template_file.read()
    total = len(pdf_files)
    progresso = st.progress(0, text="Iniciando...")

    resultados = []

    for i, pdf in enumerate(pdf_files):
        progresso.progress((i) / total, text=f"Processando {pdf.name}...")

        with st.expander(f"📄 {pdf.name}", expanded=True):
            try:
                # 1. Extração
                df_bruto, log_extracao = extrair_pdf(
                    pdf,
                    modo=modo_extracao,
                    encoding=encoding
                )
                st.info(f"🔍 Extração: {log_extracao}")

                # 2. Limpeza
                df_limpo, anomalias = limpar_dados(
                    df_bruto,
                    template_bytes=template_bytes,
                    decimal_sep=decimal_sep,
                    header_row=int(header_row)
                )

                # Alertas de anomalias
                if anomalias:
                    st.warning(f"⚠️ {len(anomalias)} anomalia(s) encontrada(s):")
                    for a in anomalias:
                        st.markdown(f"- {a}")

                # Preview dos dados
                st.markdown("**Preview dos dados limpos:**")
                st.dataframe(df_limpo.head(10), use_container_width=True)

                # 3. Geração do Excel
                excel_bytes = gerar_excel(
                    df_limpo,
                    template_bytes=template_bytes,
                    header_row=int(header_row)
                )

                nome_saida = pdf.name.replace(".pdf", "_convertido.xlsx")

                st.download_button(
                    label=f"⬇️ Baixar {nome_saida}",
                    data=excel_bytes,
                    file_name=nome_saida,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

                resultados.append({"arquivo": pdf.name, "status": "✅ Sucesso", "anomalias": len(anomalias)})

            except Exception as e:
                st.error(f"❌ Erro ao processar {pdf.name}: {e}")
                resultados.append({"arquivo": pdf.name, "status": f"❌ Erro: {e}", "anomalias": "-"})

        progresso.progress((i + 1) / total, text=f"{i+1}/{total} concluídos")

    # ─── Relatório Final ──────────────────────────────────────
    st.divider()
    st.subheader("📊 Relatório de Processamento")
    df_rel = pd.DataFrame(resultados)
    st.dataframe(df_rel, use_container_width=True, hide_index=True)

    total_ok  = sum(1 for r in resultados if "Sucesso" in r["status"])
    total_err = total - total_ok
    st.success(f"✅ {total_ok} arquivo(s) convertido(s) com sucesso | ❌ {total_err} erro(s)")
