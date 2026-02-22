import pdfplumber
import pandas as pd
import io

def extrair_pdf(pdf_file, modo="Automático", encoding="utf-8"):
    """
    Extrai tabela do PDF e retorna DataFrame bruto + log.
    Suporta PDFs nativos (pdfplumber) e scaneados (OCR via pytesseract).
    """
    pdf_bytes = pdf_file.read() if hasattr(pdf_file, "read") else pdf_file

    # ── Tentar pdfplumber primeiro ──────────────────────────────
    if modo in ("Automático", "Forçar pdfplumber"):
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                todas_tabelas = []
                for page in pdf.pages:
                    tabela = page.extract_table()
                    if tabela:
                        todas_tabelas.extend(tabela)

                if todas_tabelas:
                    headers = todas_tabelas[0]
                    rows    = todas_tabelas[1:]
                    df = pd.DataFrame(rows, columns=headers)
                    df = df.dropna(how="all")  # remove linhas totalmente vazias
                    return df, "pdfplumber (PDF nativo)"
        except Exception as e:
            if modo == "Forçar pdfplumber":
                raise RuntimeError(f"pdfplumber falhou: {e}")

    # ── Fallback: OCR ───────────────────────────────────────────
    if modo in ("Automático", "Forçar OCR"):
        try:
            import pytesseract
            from pdf2image import convert_from_bytes
            from PIL import Image

            images = convert_from_bytes(pdf_bytes, dpi=300)
            texto_total = []

            for img in images:
                texto = pytesseract.image_to_string(img, lang="por+eng")
                texto_total.append(texto)

            # Parsear texto → tabela simples
            linhas = []
            for bloco in texto_total:
                for linha in bloco.strip().split("\n"):
                    if linha.strip():
                        linhas.append(linha.strip().split())

            if linhas:
                max_cols = max(len(l) for l in linhas)
                df = pd.DataFrame(
                    [l + [""] * (max_cols - len(l)) for l in linhas]
                )
                df.columns = [f"col_{i}" for i in range(max_cols)]
                return df, "OCR (pytesseract)"

        except Exception as e:
            raise RuntimeError(f"OCR falhou: {e}")

    raise RuntimeError("Nenhum método de extração disponível.")
