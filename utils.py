import re
import unicodedata
from typing import Any, Iterable

import pandas as pd


class TextUtils:
    VALORES_VAZIOS = {"", "-", "NAN", "N/D", "NA", "NONE", "NULL", "SEM CLASSIFICACAO", "SEM CLASSIFICAÇÃO"}

    @staticmethod
    def normalizar(texto: Any) -> str:
        if pd.isna(texto):
            return ""
        s = str(texto).strip()
        s = unicodedata.normalize("NFD", s)
        s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
        s = re.sub(r"\s+", " ", s)
        return s.upper()

    @staticmethod
    def precisa_preencher(valor: Any) -> bool:
        return TextUtils.normalizar(valor) in TextUtils.VALORES_VAZIOS

    @staticmethod
    def combinar_texto_linha(row: pd.Series, colunas_texto: Iterable[str]) -> str:
        partes = []
        for coluna in colunas_texto:
            valor = row.get(coluna, "")
            if not pd.isna(valor):
                partes.append(str(valor))
        return TextUtils.normalizar(" ".join(partes))

    @staticmethod
    def coluna_case_insensitive(df: pd.DataFrame, nome_coluna: str) -> str | None:
        alvo = TextUtils.normalizar(nome_coluna)
        for coluna in df.columns:
            if TextUtils.normalizar(coluna) == alvo:
                return coluna
        return None
