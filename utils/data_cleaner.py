import pandas as pd
import numpy as np
import re
import io

def limpar_dados(df: pd.DataFrame, template_bytes: bytes,
                 decimal_sep: str = ".", header_row: int = 2) -> tuple:
    """
    Limpa e valida o DataFrame conforme o template.
    Retorna: (df_limpo, lista_anomalias)
    """
    anomalias = []

    # 1. Carregar colunas do template como referência
    template_df = pd.read_excel(
        io.BytesIO(template_bytes),
        header=header_row - 2,
        nrows=0
    )
    colunas_template = list(template_df.columns)

    # 2. Alinhar colunas ao template
    colunas_pdf = list(df.columns)
    colunas_mapeadas = {}

    for col_tmpl in colunas_template:
        # Busca coluna com nome igual (case-insensitive)
        match = next(
            (c for c in colunas_pdf if str(c).strip().lower() == str(col_tmpl).strip().lower()),
            None
        )
        if match:
            colunas_mapeadas[match] = col_tmpl
        else:
            anomalias.append(f"Coluna '{col_tmpl}' do template não encontrada no PDF.")

    df = df.rename(columns=colunas_mapeadas)

    # Manter apenas colunas do template que foram encontradas
    colunas_presentes = [c for c in colunas_template if c in df.columns]
    df = df[colunas_presentes].copy()

    # 3. Limpeza por coluna
    for col in df.columns:
        df[col] = df[col].astype(str)

        # Remover caracteres de controle e espaços extras
        df[col] = df[col].str.strip()
        df[col] = df[col].str.replace(r"[\x00-\x1f\x7f]", "", regex=True)
        df[col] = df[col].replace({"nan": "", "None": "", "NULL": ""})

        # Tentar converter para numérico
        amostra = df[col].dropna().head(20)
        parece_numero = amostra.str.replace(r"[0-9.,\s\-]", "", regex=True).str.len().mean()

        if parece_numero is not None and parece_numero < 1.5:
            try:
                if decimal_sep == ",":
                    df[col] = df[col].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")
                nulos = df[col].isna().sum()
                if nulos > 0:
                    anomalias.append(f"Coluna '{col}': {nulos} valor(es) não convertido(s) para número.")
            except Exception:
                pass

    # 4. Validar totalizações
    colunas_num = df.select_dtypes(include=[np.number]).columns.tolist()
    for col in colunas_num:
        total_calculado = df[col].iloc[:-1].sum()
        ultima_linha    = df[col].iloc[-1]
        if pd.notna(ultima_linha) and ultima_linha != 0:
            diferenca = abs(total_calculado - ultima_linha)
            if diferenca > 0.01:
                anomalias.append(
                    f"Coluna '{col}': total calculado ({total_calculado:.2f}) "
                    f"≠ última linha ({ultima_linha:.2f}). Diferença: {diferenca:.4f}"
                )

    # 5. Remover linhas completamente vazias
    df = df.dropna(how="all")
    df = df.reset_index(drop=True)

    return df, anomalias
