import re
from dataclasses import dataclass
from typing import Any

import pandas as pd

from utils import TextUtils


@dataclass
class RegraClassificacao:
    coluna_alvo: str
    regex: str
    classificacao: str
    prioridade: int


class SKUClassifier:
    COLUNAS_OBRIGATORIAS = {
        "coluna alvo": "Coluna Alvo",
        "regex": "Regex",
        "classificacao": "Classificacao",
    }

    def __init__(self, df_dicionario: pd.DataFrame, colunas_alvo: list[str]):
        self.df_dicionario = self._padronizar_dicionario(df_dicionario)
        self.colunas_alvo = [TextUtils.normalizar(c) for c in colunas_alvo]
        self.regras, self.fallbacks = self._construir_regras()

    @staticmethod
    def _nome_canonico_coluna(nome: Any) -> str:
        nome_norm = TextUtils.normalizar(nome).lower().replace("ç", "c")
        nome_norm = re.sub(r"[^a-z0-9]+", " ", nome_norm).strip()
        aliases = {
            "coluna alvo": "Coluna Alvo",
            "coluna": "Coluna Alvo",
            "alvo": "Coluna Alvo",
            "campo": "Coluna Alvo",
            "regex": "Regex",
            "regra": "Regex",
            "valor regra": "Regex",
            "padrao": "Regex",
            "classificacao": "Classificacao",
            "classificao": "Classificacao",
            "interpretacao": "Classificacao",
            "resultado": "Classificacao",
            "valor final": "Classificacao",
            "prioridade": "Prioridade",
            "ordem": "Prioridade",
            "ativo": "Ativo",
            "observacao": "Observacao",
            "observacoes": "Observacao",
        }
        return aliases.get(nome_norm, str(nome).strip())

    def _padronizar_dicionario(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            raise ValueError("O dicionário está vazio.")

        df = df.copy()
        df.columns = [self._nome_canonico_coluna(c) for c in df.columns]

        faltantes = [col for col in self.COLUNAS_OBRIGATORIAS.values() if col not in df.columns]
        if faltantes:
            raise ValueError(
                "O dicionário precisa ter as colunas: Coluna Alvo, Regex e Classificacao. "
                f"Colunas faltantes: {', '.join(faltantes)}"
            )

        if "Prioridade" not in df.columns:
            df["Prioridade"] = range(1, len(df) + 1)
        if "Ativo" not in df.columns:
            df["Ativo"] = "SIM"

        df["Coluna Alvo"] = df["Coluna Alvo"].map(TextUtils.normalizar)
        df["Regex"] = df["Regex"].fillna("").astype(str).str.strip()
        df["Classificacao"] = df["Classificacao"].map(TextUtils.normalizar)
        df["Ativo"] = df["Ativo"].map(TextUtils.normalizar)
        df["Prioridade"] = pd.to_numeric(df["Prioridade"], errors="coerce").fillna(999999).astype(int)

        df = df[
            (df["Ativo"].isin(["SIM", "S", "TRUE", "1", "ATIVO", "YES"]))
            & (df["Coluna Alvo"] != "")
            & (df["Regex"] != "")
            & (df["Classificacao"] != "")
        ].copy()

        df.sort_values(["Coluna Alvo", "Prioridade"], inplace=True, kind="stable")
        return df

    def _construir_regras(self) -> tuple[dict[str, list[RegraClassificacao]], dict[str, str]]:
        regras: dict[str, list[RegraClassificacao]] = {}
        fallbacks: dict[str, str] = {}

        for _, row in self.df_dicionario.iterrows():
            coluna = TextUtils.normalizar(row["Coluna Alvo"])
            if coluna not in self.colunas_alvo:
                continue

            regex = str(row["Regex"]).strip()
            classificacao = TextUtils.normalizar(row["Classificacao"])
            prioridade = int(row["Prioridade"])

            if regex == ".*":
                fallbacks[coluna] = classificacao
                continue

            regras.setdefault(coluna, []).append(
                RegraClassificacao(
                    coluna_alvo=coluna,
                    regex=regex,
                    classificacao=classificacao,
                    prioridade=prioridade,
                )
            )

        return regras, fallbacks

    def _classificar_coluna(self, texto: str, coluna_alvo: str) -> tuple[str, str, str]:
        coluna_alvo = TextUtils.normalizar(coluna_alvo)

        for regra in self.regras.get(coluna_alvo, []):
            try:
                if re.search(regra.regex, texto, flags=re.IGNORECASE):
                    return regra.classificacao, "CLASSIFICADO", regra.regex
            except re.error as erro:
                return "-", f"REGEX_INVALIDA: {erro}", regra.regex

        if coluna_alvo in self.fallbacks:
            return self.fallbacks[coluna_alvo], "FALLBACK", ".*"

        return "-", "NAO_CLASSIFICADO", ""

    @staticmethod
    def _montar_descricao_auditoria(row: pd.Series, colunas_texto: list[str]) -> str:
        partes = []

        for coluna in colunas_texto:
            valor = row.get(coluna, "")
            if pd.isna(valor):
                continue

            valor_texto = str(valor).strip()
            if valor_texto:
                partes.append(f"{coluna}: {valor_texto}")

        return " | ".join(partes)

    def processar_dataframe(
        self,
        df_base: pd.DataFrame,
        colunas_texto: list[str],
        colunas_sobrescrever: list[str] | None = None,
        callback_progresso=None,
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        if not colunas_texto:
            raise ValueError("Selecione pelo menos uma coluna da base para servir como texto de classificação.")

        colunas_sobrescrever = [TextUtils.normalizar(c) for c in (colunas_sobrescrever or [])]
        df_resultado = df_base.copy()

        mapa_saida: dict[str, str] = {}
        for coluna_alvo in self.colunas_alvo:
            coluna_alvo = TextUtils.normalizar(coluna_alvo)
            existente = TextUtils.coluna_case_insensitive(df_resultado, coluna_alvo)
            coluna_saida = existente or coluna_alvo

            if coluna_saida not in df_resultado.columns:
                df_resultado[coluna_saida] = ""

            df_resultado[coluna_saida] = df_resultado[coluna_saida].astype(object)
            mapa_saida[coluna_alvo] = coluna_saida

        auditoria: list[dict[str, Any]] = []
        total = len(df_resultado)

        for posicao, (idx, row) in enumerate(df_resultado.iterrows(), start=1):
            descricao_sku_usada = self._montar_descricao_auditoria(row, colunas_texto)
            texto_base = TextUtils.combinar_texto_linha(row, colunas_texto)

            for coluna_alvo in self.colunas_alvo:
                coluna_alvo = TextUtils.normalizar(coluna_alvo)
                coluna_saida = mapa_saida[coluna_alvo]
                valor_atual = row.get(coluna_saida, "")
                deve_classificar = coluna_alvo in colunas_sobrescrever or TextUtils.precisa_preencher(valor_atual)

                if deve_classificar:
                    classificacao, status, regex_usada = self._classificar_coluna(texto_base, coluna_alvo)
                    df_resultado.at[idx, coluna_saida] = classificacao
                else:
                    classificacao = TextUtils.normalizar(valor_atual)
                    status = "PRESERVADO"
                    regex_usada = ""

                auditoria.append(
                    {
                        "linha_base": idx + 2 if isinstance(idx, int) else idx,
                        "coluna_alvo": coluna_alvo,
                        "coluna_saida": coluna_saida,
                        "status": status,
                        "classificacao": classificacao,
                        "descricao_sku_usada": descricao_sku_usada,
                        "texto_normalizado_usado": texto_base,
                        "regex_usada": regex_usada,
                    }
                )

            if callback_progresso:
                callback_progresso(posicao, total)

        df_auditoria = pd.DataFrame(auditoria)
        return df_resultado, df_auditoria

    @staticmethod
    def montar_resumo(df_auditoria: pd.DataFrame) -> pd.DataFrame:
        if df_auditoria.empty:
            return pd.DataFrame()

        resumo = (
            df_auditoria.groupby("coluna_alvo")
            .agg(
                total_linhas=("linha_base", "count"),
                classificados=("status", lambda s: int((s == "CLASSIFICADO").sum())),
                fallback=("status", lambda s: int((s == "FALLBACK").sum())),
                preservados=("status", lambda s: int((s == "PRESERVADO").sum())),
                nao_classificados=("status", lambda s: int((s == "NAO_CLASSIFICADO").sum())),
                regex_invalidas=("status", lambda s: int(s.astype(str).str.startswith("REGEX_INVALIDA").sum())),
            )
            .reset_index()
        )
        resumo["preenchidos_total"] = resumo["classificados"] + resumo["fallback"] + resumo["preservados"]
        resumo["taxa_preenchimento_%"] = (resumo["preenchidos_total"] / resumo["total_linhas"] * 100).round(2)
        resumo["taxa_match_regex_%"] = (resumo["classificados"] / resumo["total_linhas"] * 100).round(2)
        return resumo
