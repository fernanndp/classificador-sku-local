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
    .main .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .hero {
        padding: 1.25rem 1.4rem;
        border-radius: 22px;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 52%, #334155 100%);
        color: white;
        margin-bottom: 1rem;
        border: 1px solid rgba(255,255,255,.12);
    }
    .hero h1 {margin: 0; font-size: 2.05rem;}
    .hero p {margin: .35rem 0 0; color: #dbeafe; font-size: 1rem;}
   .step-card {
    padding: 1rem;
    border-radius: 18px;
    border: 1px solid #e2e8f0;
    background: #ffffff;
    color: #0f172a !important;
    box-shadow: 0 10px 25px rgba(15,23,42,.05);
    }
    
    .step-card * {
        color: #0f172a !important;
    }
    
    .step-card b {
        color: #1d4ed8 !important;
    }
    .metric-card {
        padding: .9rem 1rem;
        border: 1px solid #e2e8f0;
        background: #f8fafc;
        border-radius: 16px;
        min-height: 94px;
    }
    .metric-card .label {font-size: .82rem; color: #64748b; margin-bottom: .25rem;}
    .metric-card .value {font-size: 1.55rem; font-weight: 800; color: #0f172a;}
    .metric-card .hint {font-size: .78rem; color: #64748b; margin-top: .2rem;}
    div[data-testid="stMetricValue"] {font-size: 1.5rem;}
    div[data-testid="stDataFrame"] {border: 1px solid #e2e8f0; border-radius: 14px; overflow: hidden;}

    /* Tradução visual do componente padrão st.file_uploader do Streamlit.
       O Streamlit não expõe esses textos como parâmetro, então a troca é feita por CSS. */
    div[data-testid="stFileUploaderDropzoneInstructions"] span {
        font-size: 0 !important;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] span::after {
        content: "Arraste e solte o arquivo aqui";
        font-size: 1rem !important;
        font-weight: 700;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] small {
        font-size: 0 !important;
    }
    div[data-testid="stFileUploaderDropzoneInstructions"] small::after {
        content: "Limite de 200 MB por arquivo • XLSX, CSV";
        font-size: .875rem !important;
        color: inherit;
    }
    div[data-testid="stFileUploaderDropzone"] button,
    div[data-testid="stFileUploaderDropzone"] button p,
    div[data-testid="stFileUploaderDropzone"] button span {
        font-size: 0 !important;
    }
    div[data-testid="stFileUploaderDropzone"] button::after {
        content: "Procurar arquivos";
        font-size: 1rem !important;
        font-weight: 600;
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
    nome = uploaded_file.name.lower()
    conteudo = uploaded_file.getvalue()


    if nome.endswith((".xlsx", ".xlsm", ".xls")) or conteudo[:2] == b"PK":
        return pd.read_excel(io.BytesIO(conteudo))

    # CSV/TXT: tenta os encodings mais comuns no Brasil/Excel.
    encodings = ["utf-8-sig", "utf-8", "utf-16", "utf-16-le", "utf-16-be", "cp1252", "latin1"]
    separadores = [None, ";", ",", "\t", "|"]
    erros = []

    for encoding in encodings:
        for sep in separadores:
            try:
                df = pd.read_csv(
                    io.BytesIO(conteudo),
                    sep=sep,
                    engine="python",
                    encoding=encoding,
                    dtype=str,
                )
                # Evita aceitar uma leitura ruim que trouxe tudo em uma única coluna quando há separador claro.
                if df.shape[1] > 1 or sep is not None:
                    return df
            except Exception as erro:
                erros.append(f"encoding={encoding}, sep={sep}: {erro}")

    raise ValueError(
        "Não consegui ler o arquivo. Salve como .xlsx ou CSV UTF-8/CSV separado por ponto e vírgula. "
        f"Últimos erros testados: {' | '.join(erros[-3:])}"
    )


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
                    "Nome da coluna que será criada/preenchida na base, por exemplo: CATEGORIA, MARCA, SABOR.",
                    "Expressão regular que será procurada no texto das colunas escolhidas da base.",
                    "Valor final que entrará na coluna alvo quando a regex casar.",
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

    colunas_texto = []
    for coluna in colunas:
        colunas_texto.append(coluna)
        if len(colunas_texto) == 1:
            break
    return colunas_texto


def listar_colunas_dicionario(df_dict: pd.DataFrame) -> list[str]:
    df_tmp = df_dict.copy()
    df_tmp.columns = [SKUClassifier._nome_canonico_coluna(c) for c in df_tmp.columns]
    if "Coluna Alvo" not in df_tmp.columns:
        return []
    return sorted(df_tmp["Coluna Alvo"].dropna().map(TextUtils.normalizar).unique().tolist())


def desenhar_metric_card(label: str, value: str, hint: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="hint">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def desenhar_dashboard(df_resultado: pd.DataFrame, df_resumo: pd.DataFrame, df_auditoria: pd.DataFrame, colunas_alvo: list[str]):
    st.subheader("📊 Estatísticas da classificação")

    total_linhas = len(df_resultado)
    total_colunas = len(colunas_alvo)
    total_celulas = int(total_linhas * total_colunas)
    classificados = int(df_resumo["classificados"].sum()) if not df_resumo.empty else 0
    fallback = int(df_resumo["fallback"].sum()) if not df_resumo.empty else 0
    preservados = int(df_resumo["preservados"].sum()) if not df_resumo.empty else 0
    nao_classificados = int(df_resumo["nao_classificados"].sum()) if not df_resumo.empty else 0
    taxa = round(((classificados + fallback + preservados) / total_celulas * 100), 2) if total_celulas else 0

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
        desenhar_metric_card("Taxa preenchida", f"{taxa}%", "inclui preservados")

    st.markdown("#### Resumo por coluna")
    st.dataframe(df_resumo, use_container_width=True, hide_index=True)

    col_graf1, col_graf2 = st.columns([1.2, 1])
    with col_graf1:
        st.markdown("#### Quantidade por status")
        status_chart = df_auditoria["status"].value_counts().rename_axis("status").reset_index(name="quantidade")
        st.bar_chart(status_chart, x="status", y="quantidade", use_container_width=True)

    with col_graf2:
        st.markdown("#### Colunas com maior não classificação")
        nao_chart = df_resumo[["coluna_alvo", "nao_classificados"]].sort_values("nao_classificados", ascending=False)
        st.bar_chart(nao_chart, x="coluna_alvo", y="nao_classificados", use_container_width=True)

    st.markdown("#### Distribuição de valores por coluna classificada")
    abas = st.tabs(colunas_alvo)
    for aba, coluna_alvo in zip(abas, colunas_alvo):
        with aba:
            coluna_saida = None
            matches = df_auditoria.loc[df_auditoria["coluna_alvo"] == coluna_alvo, "coluna_saida"].dropna().unique()
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


st.markdown(
    """
    <div class="hero">
        <h1>🏷️ Classificador Local de SKUs</h1>
        <p>Classificação 100% local por dicionário de regex.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

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

    file_base = st.file_uploader("Base de SKUs", type=["xlsx", "csv"], help="Planilha com as descrições dos produtos.")
    file_dict = st.file_uploader("Dicionário de classificação", type=["xlsx", "csv"], help="Planilha com Coluna Alvo, Regex e Classificacao.")

    st.divider()
    st.header("⚙️ Configuração")

if not file_base or not file_dict:
    st.info("Envie a base de SKUs e o dicionário para configurar a classificação.")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("<div class='step-card'><b>1. Base</b><br>Faça upload da planilha com os SKUs.</div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("<div class='step-card'><b>2. Dicionário</b><br>Use seu dicionário ou baixe o modelo de exemplo.</div>", unsafe_allow_html=True)
    with col_c:
        st.markdown("<div class='step-card'><b>3. Resultado</b><br>Baixe a base classificada com resumo e auditoria.</div>", unsafe_allow_html=True)
    st.stop()

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
        help="Se deixar vazio, o app só preenche células vazias, '-' ou N/D.",
    )

    executar = st.button("🚀 Iniciar classificação local", type="primary", use_container_width=True)

st.success(f"Base carregada com {len(df_base):,} linhas e {len(df_base.columns)} colunas.".replace(",", "."))
st.caption(f"Dicionário carregado com {len(df_dict):,} regras brutas.".replace(",", "."))

with st.expander("👀 Prévia da base", expanded=False):
    st.dataframe(df_base.head(20), use_container_width=True)

with st.expander("📚 Prévia do dicionário", expanded=False):
    st.dataframe(df_dict.head(30), use_container_width=True)

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
        df_resumo = SKUClassifier.montar_resumo(df_auditoria)
except Exception as erro:
    st.error(f"Erro durante a classificação: {erro}")
    st.stop()

progress_bar.progress(1.0)
status_text.write("Classificação concluída.")
st.success("🎉 Classificação local concluída com sucesso!")

desenhar_dashboard(df_resultado, df_resumo, df_auditoria, colunas_alvo)

st.divider()
st.subheader("💾 Baixar resultado")
resultado_bytes = preparar_download_excel(df_resultado, df_resumo, df_auditoria)
st.download_button(
    label="📥 Baixar base classificada (.xlsx)",
    data=resultado_bytes,
    file_name="BASE_SKUS_CLASSIFICADA_LOCAL.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary",
    use_container_width=True,
)

with st.expander("🔎 Prévia do resultado", expanded=False):
    st.dataframe(df_resultado.head(50), use_container_width=True)
