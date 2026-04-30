import io
from typing import Iterable

import pandas as pd
import streamlit as st

from classifier import SKUClassifier
from utils import TextUtils


st.set_page_config(
    page_title="Classificador Local de SKUs",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)


CSS = """
<style>
    /* =========================================================
       BASE
    ========================================================= */
    :root {
        --bg-main: #0b1020;
        --bg-card: #ffffff;
        --bg-card-soft: #f8fafc;
        --text-main: #0f172a;
        --text-muted: #64748b;
        --brand: #ef4444;
        --brand-dark: #dc2626;
        --brand-blue: #2563eb;
        --border: #e2e8f0;
        --shadow: 0 18px 45px rgba(15, 23, 42, .14);
        --radius: 22px;
    }

    .main .block-container {
        padding-top: 1.4rem;
        padding-bottom: 3rem;
        max-width: 1320px;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(148, 163, 184, .20);
    }

    section[data-testid="stSidebar"] > div {
        padding-top: 1.2rem;
    }

    /* Corrige textos selecionados/contraste em tema escuro */
    ::selection {
        background: rgba(37, 99, 235, .35);
        color: #ffffff;
    }

    /* =========================================================
       HERO
    ========================================================= */
    .hero {
        position: relative;
        overflow: hidden;
        padding: 2rem 2.1rem;
        border-radius: 28px;
        background:
            radial-gradient(circle at top right, rgba(96, 165, 250, .35), transparent 34%),
            linear-gradient(135deg, #111827 0%, #1e293b 55%, #334155 100%);
        color: white;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255,255,255,.12);
        box-shadow: 0 24px 70px rgba(2, 6, 23, .32);
    }

    .hero::after {
        content: "";
        position: absolute;
        inset: auto -80px -120px auto;
        width: 300px;
        height: 300px;
        background: rgba(239, 68, 68, .23);
        filter: blur(18px);
        border-radius: 999px;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: .45rem;
        padding: .35rem .7rem;
        border-radius: 999px;
        background: rgba(255,255,255,.10);
        border: 1px solid rgba(255,255,255,.16);
        color: #e0f2fe;
        font-weight: 700;
        font-size: .84rem;
        margin-bottom: .85rem;
    }

    .hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.05rem);
        line-height: 1.03;
        letter-spacing: -.045em;
        color: #ffffff !important;
    }

    .hero p {
        margin: .75rem 0 0;
        color: #dbeafe !important;
        font-size: 1.06rem;
        max-width: 880px;
    }

    .hero-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: .75rem;
        margin-top: 1.2rem;
        max-width: 930px;
    }

    .hero-mini {
        padding: .75rem .85rem;
        border-radius: 16px;
        background: rgba(255,255,255,.09);
        border: 1px solid rgba(255,255,255,.14);
        color: #eff6ff !important;
        font-size: .92rem;
    }

    .hero-mini b {
        color: #ffffff !important;
    }

    /* =========================================================
       CARDS DE ETAPAS
    ========================================================= */
    .steps-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }

    .step-card {
        position: relative;
        padding: 1.1rem 1.1rem 1.15rem;
        border-radius: 22px;
        border: 1px solid var(--border);
        background: #ffffff;
        color: var(--text-main) !important;
        box-shadow: var(--shadow);
        min-height: 140px;
    }

    .step-card * {
        color: var(--text-main) !important;
    }

    .step-number {
        width: 34px;
        height: 34px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border-radius: 12px;
        background: #eff6ff;
        color: #1d4ed8 !important;
        font-weight: 900;
        margin-bottom: .65rem;
    }

    .step-card h3 {
        margin: 0 0 .35rem;
        font-size: 1.05rem;
        letter-spacing: -.01em;
    }

    .step-card p {
        margin: 0;
        color: #475569 !important;
        line-height: 1.45;
        font-size: .95rem;
    }

    /* =========================================================
       MÉTRICAS
    ========================================================= */
    .metric-card {
        padding: 1rem 1rem 1.05rem;
        border: 1px solid var(--border);
        background:
            linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
        border-radius: 20px;
        min-height: 118px;
        box-shadow: 0 12px 30px rgba(15, 23, 42, .09);
    }

    .metric-card .label {
        font-size: .82rem;
        color: #64748b !important;
        margin-bottom: .4rem;
        font-weight: 700;
    }

    .metric-card .value {
        font-size: 1.85rem;
        line-height: 1;
        font-weight: 900;
        color: #0f172a !important;
        letter-spacing: -.035em;
    }

    .metric-card .hint {
        font-size: .80rem;
        color: #64748b !important;
        margin-top: .55rem;
    }

    .metric-card .bar {
        height: 6px;
        border-radius: 999px;
        background: #e2e8f0;
        margin-top: .8rem;
        overflow: hidden;
    }

    .metric-card .bar span {
        display: block;
        height: 100%;
        border-radius: 999px;
        background: linear-gradient(90deg, #2563eb, #22c55e);
    }

    /* =========================================================
       PAINEL / SEÇÕES
    ========================================================= */
    .section-title {
        display: flex;
        align-items: center;
        gap: .55rem;
        margin: 1.25rem 0 .65rem;
    }

    .section-title h2 {
        margin: 0;
        font-size: 1.45rem;
        letter-spacing: -.03em;
    }

    .soft-panel {
        padding: 1.15rem;
        border-radius: 22px;
        border: 1px solid rgba(148, 163, 184, .22);
        background: rgba(15, 23, 42, .035);
        margin: .75rem 0 1rem;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(148, 163, 184, .35);
        border-radius: 16px;
        overflow: hidden;
    }

    div[data-testid="stProgress"] > div > div > div > div {
        background: linear-gradient(90deg, #ef4444, #f97316, #22c55e);
    }

    /* Botão principal */
    div.stButton > button[kind="primary"],
    div.stDownloadButton > button[kind="primary"] {
        border-radius: 14px !important;
        border: 0 !important;
        background: linear-gradient(135deg, #ef4444, #f97316) !important;
        color: white !important;
        font-weight: 900 !important;
        min-height: 48px;
        box-shadow: 0 12px 28px rgba(239, 68, 68, .25);
    }

    div.stButton > button[kind="primary"]:hover,
    div.stDownloadButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 16px 34px rgba(239, 68, 68, .33);
    }

    /* =========================================================
       UPLOADER EM PORTUGUÊS
       Observação: o texto original do Streamlit continua existindo,
       mas fica visualmente substituído por pseudo-elementos.
    ========================================================= */
    div[data-testid="stFileUploaderDropzone"] {
        border-radius: 16px !important;
        border: 1px dashed rgba(148, 163, 184, .45) !important;
        background: rgba(15, 23, 42, .20) !important;
    }

    div[data-testid="stFileUploaderDropzone"] button {
        border-radius: 12px !important;
        font-weight: 800 !important;
    }

    div[data-testid="stFileUploaderDropzone"] small {
        visibility: hidden;
        position: relative;
    }

    div[data-testid="stFileUploaderDropzone"] small::after {
        content: "Limite de 200 MB por arquivo • XLSX, CSV";
        visibility: visible;
        position: absolute;
        left: 0;
        top: 0;
        white-space: nowrap;
        color: #cbd5e1;
    }

    div[data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p {
        visibility: hidden;
        position: relative;
    }

    div[data-testid="stFileUploaderDropzone"] [data-testid="stMarkdownContainer"] p::after {
        content: "Arraste e solte o arquivo aqui";
        visibility: visible;
        position: absolute;
        left: 0;
        top: 0;
        white-space: normal;
        color: #ffffff;
        font-weight: 800;
    }

    /* =========================================================
       RESPONSIVO
    ========================================================= */
    @media (max-width: 900px) {
        .hero-grid,
        .steps-grid {
            grid-template-columns: 1fr;
        }

        .hero {
            padding: 1.5rem;
        }
    }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


COLUNAS_DESCRICAO_SUGERIDAS = [
    "DESCRICAO",
    "DESCRIÇÃO",
    "DESCRIPCION",
    "SKU",
    "NOME",
    "NOME SKU",
    "NOME_SKU",
    "PRODUTO",
    "DESCRIÇÃO PRODUTO",
    "CONCATENADO_SKU",
]


def carregar_planilha(uploaded_file) -> pd.DataFrame:
    """
    Lê XLSX/CSV direto do upload, sem salvar em disco.
    Para CSV, tenta encodings comuns do Excel/Windows.
    """
    nome = uploaded_file.name.lower()
    conteudo = uploaded_file.getvalue()

    if nome.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(conteudo))

    encodings = ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin1"]
    ultimo_erro = None

    for encoding in encodings:
        try:
            return pd.read_csv(io.BytesIO(conteudo), sep=None, engine="python", encoding=encoding)
        except Exception as erro:
            ultimo_erro = erro

    raise ValueError(f"Não foi possível ler o CSV. Último erro: {ultimo_erro}")


def gerar_dicionario_exemplo() -> bytes:
    dados = [
        ["CATEGORIA", r"\b(REFRIGERANTE|REFRI|SODA)\b", "REFRIGERANTE", 10, "SIM", "Categoria por termos principais"],
        ["CATEGORIA", r"\b(SUCO|NECTAR|NÉCTAR)\b", "SUCO", 20, "SIM", ""],
        ["CATEGORIA", r"\b(BISCOITO|COOKIE|BOLACHA)\b", "BISCOITO", 30, "SIM", ""],
        ["CATEGORIA", r"\b(CHOCOLATE|BOMBOM|CACAU)\b", "CHOCOLATE", 40, "SIM", ""],
        ["CATEGORIA", r".*", "OUTROS", 999, "SIM", "Fallback: usado quando nada casar"],
        ["MARCA", r"\b(COCA[- ]?COLA|COCA)\b", "COCA-COLA", 10, "SIM", ""],
        ["MARCA", r"\b(PEPSI)\b", "PEPSI", 20, "SIM", ""],
        ["MARCA", r"\b(NESTLE|NESTL[EÉ])\b", "NESTLE", 30, "SIM", ""],
        ["MARCA", r"\b(GAROTO)\b", "GAROTO", 40, "SIM", ""],
        ["MARCA", r".*", "NAO IDENTIFICADA", 999, "SIM", ""],
        ["SABOR", r"\b(LARANJA|ORANGE)\b", "LARANJA", 10, "SIM", ""],
        ["SABOR", r"\b(UVA|GRAPE)\b", "UVA", 20, "SIM", ""],
        ["SABOR", r"\b(LIMAO|LIMÃO|LEMON)\b", "LIMAO", 30, "SIM", ""],
        ["SABOR", r"\b(MORANGO|STRAWBERRY)\b", "MORANGO", 40, "SIM", ""],
        ["SABOR", r"\b(CHOCOLATE|CACAU)\b", "CHOCOLATE", 50, "SIM", ""],
        ["SABOR", r".*", "NAO APLICAVEL", 999, "SIM", ""],
        ["EMBALAGEM", r"\b(LATA|LT)\b", "LATA", 10, "SIM", ""],
        ["EMBALAGEM", r"\b(GARRAFA|PET)\b", "GARRAFA", 20, "SIM", ""],
        ["EMBALAGEM", r"\b(CAIXA|CX)\b", "CAIXA", 30, "SIM", ""],
        ["EMBALAGEM", r"\b(PACOTE|PCT|SACHET|SACHE)\b", "PACOTE", 40, "SIM", ""],
        ["EMBALAGEM", r".*", "NAO IDENTIFICADA", 999, "SIM", ""],
        ["VOLUME", r"\b(350)\s*(ML|M\.L\.)?\b", "350ML", 10, "SIM", ""],
        ["VOLUME", r"\b(500)\s*(ML|M\.L\.)?\b", "500ML", 20, "SIM", ""],
        ["VOLUME", r"\b(1)\s*(L|LT|LITRO)\b", "1L", 30, "SIM", ""],
        ["VOLUME", r"\b(2)\s*(L|LT|LITROS)\b", "2L", 40, "SIM", ""],
        ["VOLUME", r".*", "NAO IDENTIFICADO", 999, "SIM", ""],
        ["LINHA", r"\b(ZERO|SEM ACUCAR|SEM AÇUCAR|DIET)\b", "ZERO/DIET", 10, "SIM", ""],
        ["LINHA", r"\b(LIGHT)\b", "LIGHT", 20, "SIM", ""],
        ["LINHA", r".*", "REGULAR", 999, "SIM", ""],
    ]

    df = pd.DataFrame(
        dados,
        columns=["Coluna Alvo", "Regex", "Classificacao", "Prioridade", "Ativo", "Observacao"],
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Dicionario")
        instrucoes = pd.DataFrame(
            {
                "Campo": ["Coluna Alvo", "Regex", "Classificacao", "Prioridade", "Ativo", "Observacao"],
                "Como usar": [
                    "Nome da coluna que será criada/preenchida na base. Ex.: CATEGORIA, MARCA, SABOR.",
                    "Expressão regular procurada no texto das colunas escolhidas da base.",
                    "Valor final preenchido quando a regex casar.",
                    "Ordem de execução dentro da mesma coluna alvo. Menor número roda primeiro.",
                    "Use SIM para ativar a regra. Use NAO para ignorar temporariamente.",
                    "Campo livre para explicar a regra.",
                ],
            }
        )
        instrucoes.to_excel(writer, index=False, sheet_name="Como usar")

    return buffer.getvalue()


def preparar_download_excel(df_resultado: pd.DataFrame, df_resumo: pd.DataFrame, df_auditoria: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_resultado.to_excel(writer, index=False, sheet_name="Base_Classificada")
        df_resumo.to_excel(writer, index=False, sheet_name="Resumo")
        df_auditoria.to_excel(writer, index=False, sheet_name="Auditoria")
    return buffer.getvalue()


def sugerir_colunas_texto(colunas: Iterable[str]) -> list[str]:
    sugestoes = []

    for coluna in colunas:
        coluna_norm = TextUtils.normalizar(coluna)
        if any(token in coluna_norm for token in COLUNAS_DESCRICAO_SUGERIDAS):
            sugestoes.append(coluna)

    if sugestoes:
        return sugestoes[:3]

    return [list(colunas)[0]] if colunas else []


def listar_colunas_dicionario(df_dict: pd.DataFrame) -> list[str]:
    df_tmp = df_dict.copy()
    df_tmp.columns = [SKUClassifier._nome_canonico_coluna(c) for c in df_tmp.columns]

    if "Coluna Alvo" not in df_tmp.columns:
        return []

    return sorted(df_tmp["Coluna Alvo"].dropna().map(TextUtils.normalizar).unique().tolist())


def desenhar_metric_card(label: str, value: str, hint: str = "", progress: float | None = None):
    progress_html = ""

    if progress is not None:
        largura = max(0, min(progress, 100))
        progress_html = f"""
        <div class="bar">
            <span style="width: {largura}%"></span>
        </div>
        """

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="hint">{hint}</div>
            {progress_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def abrir_secao(titulo: str, icone: str):
    st.markdown(
        f"""
        <div class="section-title">
            <span style="font-size:1.55rem;">{icone}</span>
            <h2>{titulo}</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )


def desenhar_dashboard(df_resultado: pd.DataFrame, df_resumo: pd.DataFrame, df_auditoria: pd.DataFrame, colunas_alvo: list[str]):
    abrir_secao("Estatísticas da classificação", "📊")

    total_linhas = len(df_resultado)
    total_colunas = len(colunas_alvo)
    total_celulas = int(total_linhas * total_colunas)

    classificados = int(df_resumo["classificados"].sum()) if not df_resumo.empty else 0
    fallback = int(df_resumo["fallback"].sum()) if not df_resumo.empty else 0
    preservados = int(df_resumo["preservados"].sum()) if not df_resumo.empty else 0
    nao_classificados = int(df_resumo["nao_classificados"].sum()) if not df_resumo.empty else 0

    preenchidos = classificados + fallback + preservados
    taxa = round((preenchidos / total_celulas * 100), 2) if total_celulas else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        desenhar_metric_card("Linhas da base", f"{total_linhas:,}".replace(",", "."), "SKUs processados")
    with c2:
        desenhar_metric_card("Colunas alvo", str(total_colunas), "campos classificados")
    with c3:
        desenhar_metric_card("Matches por regex", f"{classificados:,}".replace(",", "."), "regras que casaram")
    with c4:
        desenhar_metric_card("Fallbacks", f"{fallback:,}".replace(",", "."), "regra .* aplicada")
    with c5:
        desenhar_metric_card("Taxa preenchida", f"{taxa}%", "inclui preservados", progress=taxa)

    st.markdown("#### Resumo por coluna")
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    col_graf1, col_graf2 = st.columns([1.1, 1])

    with col_graf1:
        st.markdown("#### Quantidade por status")

        if not df_auditoria.empty and "status" in df_auditoria.columns:
            status_chart = df_auditoria["status"].value_counts().rename_axis("status").reset_index(name="quantidade")
            st.bar_chart(status_chart, x="status", y="quantidade", use_container_width=True)
        else:
            st.info("Sem dados de auditoria para montar o gráfico.")

    with col_graf2:
        st.markdown("#### Colunas com maior não classificação")

        if not df_resumo.empty and "nao_classificados" in df_resumo.columns:
            nao_chart = df_resumo[["coluna_alvo", "nao_classificados"]].sort_values("nao_classificados", ascending=False)
            st.bar_chart(nao_chart, x="coluna_alvo", y="nao_classificados", use_container_width=True)
        else:
            st.info("Sem dados para montar o gráfico.")

    st.markdown("#### Distribuição de valores por coluna classificada")

    if not colunas_alvo:
        st.info("Nenhuma coluna alvo selecionada.")
        return

    abas = st.tabs(colunas_alvo)

    for aba, coluna_alvo in zip(abas, colunas_alvo):
        with aba:
            coluna_saida = None

            if not df_auditoria.empty and "coluna_saida" in df_auditoria.columns:
                matches = df_auditoria.loc[
                    df_auditoria["coluna_alvo"] == coluna_alvo,
                    "coluna_saida",
                ].dropna().unique()

                if len(matches):
                    coluna_saida = matches[0]

            if coluna_saida and coluna_saida in df_resultado.columns:
                dist = (
                    df_resultado[coluna_saida]
                    .fillna("-")
                    .astype(str)
                    .str.strip()
                    .replace("", "-")
                    .value_counts()
                    .rename_axis(coluna_alvo)
                    .reset_index(name="quantidade")
                )

                st.bar_chart(dist.head(25), x=coluna_alvo, y="quantidade", use_container_width=True)
                st.dataframe(dist, use_container_width=True, hide_index=True)
            else:
                st.info("Sem dados para esta coluna.")




def montar_descricao_linha_auditoria(row: pd.Series, colunas_texto: list[str]) -> str:
    partes = []

    for coluna in colunas_texto:
        valor = row.get(coluna, "")

        if pd.isna(valor):
            continue

        valor_texto = str(valor).strip()

        if valor_texto and valor_texto.lower() not in ["none", "nan"]:
            partes.append(f"{coluna}: {valor_texto}")

    return " | ".join(partes)


def garantir_descricao_na_auditoria(
    df_base: pd.DataFrame,
    df_auditoria: pd.DataFrame,
    colunas_texto: list[str],
) -> pd.DataFrame:
    """
    Garante que a aba Auditoria tenha:
    - descricao_sku_usada: texto original das colunas selecionadas
    - texto_normalizado_usado: texto normalizado usado pelo regex
    """
    if df_auditoria is None or df_auditoria.empty:
        return df_auditoria

    df_auditoria = df_auditoria.copy()

    mapa_descricao = {}
    mapa_texto_normalizado = {}

    for idx, row in df_base.iterrows():
        linha_base = idx + 2 if isinstance(idx, int) else idx
        mapa_descricao[linha_base] = montar_descricao_linha_auditoria(row, colunas_texto)
        mapa_texto_normalizado[linha_base] = TextUtils.combinar_texto_linha(row, colunas_texto)

    if "descricao_sku_usada" not in df_auditoria.columns:
        df_auditoria["descricao_sku_usada"] = df_auditoria["linha_base"].map(mapa_descricao).fillna("")

    if "texto_normalizado_usado" not in df_auditoria.columns:
        df_auditoria["texto_normalizado_usado"] = df_auditoria["linha_base"].map(mapa_texto_normalizado).fillna("")

    # Reordena para a descrição ficar antes da regex
    ordem_preferida = [
        "linha_base",
        "coluna_alvo",
        "coluna_saida",
        "status",
        "classificacao",
        "descricao_sku_usada",
        "texto_normalizado_usado",
        "regex_usada",
    ]

    colunas_ordenadas = [c for c in ordem_preferida if c in df_auditoria.columns]
    outras_colunas = [c for c in df_auditoria.columns if c not in colunas_ordenadas]

    return df_auditoria[colunas_ordenadas + outras_colunas]


# =========================================================
# CABEÇALHO
# =========================================================
st.markdown(
    """
    <div class="hero">
        <div class="hero-badge">⚡ 100% local • sem APIs externas</div>
        <h1>🏷️ Classificador Local de SKUs</h1>
        <p>
            Classifique produtos por dicionário de regex, escolha quais colunas serão analisadas
            e baixe a planilha final com resumo, auditoria e estatísticas.
        </p>
        <div class="hero-grid">
            <div class="hero-mini"><b>🔒 Seguro:</b><br>arquivos lidos apenas em memória.</div>
            <div class="hero-mini"><b>🧩 Flexível:</b><br>várias colunas alvo no mesmo dicionário.</div>
            <div class="hero-mini"><b>📈 Auditável:</b><br>mostra regex, status e descrição usada.</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================
with st.sidebar:
    st.header("📁 Arquivos")
    st.caption("Os arquivos são lidos em memória apenas durante a sessão.")

    st.download_button(
        "📘 Baixar dicionário de exemplo",
        data=gerar_dicionario_exemplo(),
        file_name="Dicionario_Exemplo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

    file_base = st.file_uploader(
        "Base de SKUs",
        type=["xlsx", "xls", "csv"],
        help="Planilha com as descrições dos produtos.",
    )

    file_dict = st.file_uploader(
        "Dicionário de classificação",
        type=["xlsx", "xls", "csv"],
        help="Planilha com Coluna Alvo, Regex e Classificacao.",
    )

    st.divider()
    st.header("⚙️ Configuração")


# =========================================================
# ESTADO INICIAL
# =========================================================
if not file_base or not file_dict:
    st.info("Envie a base de SKUs e o dicionário para configurar a classificação.")

    st.markdown(
        """
        <div class="steps-grid">
            <div class="step-card">
                <div class="step-number">1</div>
                <h3>Envie a base</h3>
                <p>Faça upload da planilha com os SKUs que serão classificados.</p>
            </div>
            <div class="step-card">
                <div class="step-number">2</div>
                <h3>Envie o dicionário</h3>
                <p>Use seu dicionário de regex ou baixe o modelo de exemplo.</p>
            </div>
            <div class="step-card">
                <div class="step-number">3</div>
                <h3>Baixe o resultado</h3>
                <p>Receba a base classificada com resumo, auditoria e gráficos.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.stop()


# =========================================================
# LEITURA DOS ARQUIVOS
# =========================================================
try:
    df_base = carregar_planilha(file_base)
    df_dict = carregar_planilha(file_dict)
except Exception as erro:
    st.error(f"Erro ao carregar os arquivos: {erro}")
    st.stop()


if df_base.empty:
    st.error("A base de SKUs está vazia.")
    st.stop()


colunas_dicionario = listar_colunas_dicionario(df_dict)

if not colunas_dicionario:
    st.error("Não encontrei a coluna 'Coluna Alvo' no dicionário.")
    st.stop()


with st.sidebar:
    colunas_texto = st.multiselect(
        "Colunas da base usadas para ler o texto do SKU",
        options=list(df_base.columns),
        default=sugerir_colunas_texto(df_base.columns),
        help="Você pode selecionar mais de uma. O app concatena esses campos e aplica as regex do dicionário.",
    )

    colunas_alvo = st.multiselect(
        "Colunas que serão classificadas/preenchidas",
        options=colunas_dicionario,
        default=colunas_dicionario,
        help="São as colunas cadastradas no dicionário em 'Coluna Alvo'.",
    )

    colunas_sobrescrever = st.multiselect(
        "Sobrescrever colunas já preenchidas",
        options=colunas_alvo,
        default=[],
        help="Se deixar vazio, o app só preenche células vazias, '-', NULL ou N/D.",
    )

    executar = st.button("🚀 Iniciar classificação local", type="primary", use_container_width=True)


# =========================================================
# PRÉVIAS
# =========================================================
col_info1, col_info2, col_info3 = st.columns(3)

with col_info1:
    st.success(f"Base carregada: {len(df_base):,} linhas".replace(",", "."))
with col_info2:
    st.info(f"{len(df_base.columns)} colunas na base")
with col_info3:
    st.info(f"{len(df_dict):,} regras no dicionário".replace(",", "."))


with st.expander("Prévia da base", expanded=False):
    st.caption("Mostrando apenas as primeiras 20 linhas da base enviada.")
    st.dataframe(df_base.head(20), use_container_width=True)

with st.expander("Prévia do dicionário", expanded=False):
    st.caption("Mostrando apenas as primeiras 40 regras do dicionário enviado.")
    st.dataframe(df_dict.head(40), use_container_width=True)


if not executar:
    st.info("Configure as colunas na barra lateral e clique em **Iniciar classificação local**.")
    st.stop()


if not colunas_texto:
    st.warning("Selecione pelo menos uma coluna da base para servir como texto de classificação.")
    st.stop()


if not colunas_alvo:
    st.warning("Selecione pelo menos uma coluna alvo para classificar.")
    st.stop()


try:
    classificador = SKUClassifier(df_dict, colunas_alvo)
except Exception as erro:
    st.error(f"Erro no dicionário: {erro}")
    st.stop()


progress_bar = st.progress(0)
status_text = st.empty()


def atualizar_progresso(atual: int, total: int):
    percentual = atual / total if total else 1
    progress_bar.progress(min(percentual, 1.0))
    status_text.write(f"Processando linha {atual} de {total}...")


try:
    with st.spinner("Classificando localmente com base no dicionário..."):
        df_resultado, df_auditoria = classificador.processar_dataframe(
            df_base=df_base,
            colunas_texto=colunas_texto,
            colunas_sobrescrever=colunas_sobrescrever,
            callback_progresso=atualizar_progresso,
        )

        df_auditoria = garantir_descricao_na_auditoria(
            df_base=df_base,
            df_auditoria=df_auditoria,
            colunas_texto=colunas_texto,
        )

        df_resumo = SKUClassifier.montar_resumo(df_auditoria)

except Exception as erro:
    st.error(f"Erro durante a classificação: {erro}")
    st.stop()


progress_bar.progress(1.0)
status_text.write("Classificação concluída.")
st.success("🎉 Classificação local concluída com sucesso!")


desenhar_dashboard(df_resultado, df_resumo, df_auditoria, colunas_alvo)


st.divider()
abrir_secao("Baixar resultado", "💾")

resultado_bytes = preparar_download_excel(df_resultado, df_resumo, df_auditoria)

st.download_button(
    label="📥 Baixar base classificada (.xlsx)",
    data=resultado_bytes,
    file_name="BASE_SKUS_CLASSIFICADA_LOCAL.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    use_container_width=True,
)

with st.expander("Prévia do resultado", expanded=False):
    st.dataframe(df_resultado.head(50), use_container_width=True)

with st.expander("Prévia da auditoria", expanded=False):
    st.dataframe(df_auditoria.head(100), use_container_width=True)
