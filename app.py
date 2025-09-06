# app.py
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Análise de Portfólio de Investidores Brasileiros",
    page_icon="🇧🇷",
    layout="wide"
)

# --- HELPERS ---
def _base_dir() -> Path:
    """Retorna o diretório base do app de forma robusta (funciona no Streamlit Cloud e local)."""
    try:
        return Path(__file__).parent
    except NameError:
        # Fallback quando __file__ não existe (ex.: execução interativa)
        return Path.cwd()

# --- FUNÇÃO DE CARREGAMENTO DE DADOS (COM CACHE) ---
@st.cache_data
def carregar_dados_agregados():
    """Carrega os arquivos de resumo pré-calculados de forma robusta."""
    diretorio = _base_dir()
    caminho_app_data = diretorio / "app_data"

    try:
        df_filtros = pd.read_csv(caminho_app_data / "dados_agregados_filtros.csv")
        df_mapa = pd.read_csv(caminho_app_data / "dados_mapa_uf.csv")
        df_dist = pd.read_csv(caminho_app_data / "distribuicao_diversificacao.csv")
        df_temporal = pd.read_csv(caminho_app_data / "evolucao_temporal_regional.csv")
        df_perfil = pd.read_csv(caminho_app_data / "perfil_investidor_agregado.csv")
        df_ocupacao = pd.read_csv(caminho_app_data / "ocupacao_agregado.csv")
        df_interacao = pd.read_csv(caminho_app_data / "interacao_renda_complex_agregado.csv")
        df_dist_cat = pd.read_csv(caminho_app_data / "dist_categorica_diversificacao.csv")
        df_sample_boxplot = pd.read_csv(caminho_app_data / "sample_diversificacao_boxplot.csv")

        # Parse de datas e ordenação
        if "anomes" in df_temporal.columns:
            df_temporal["anomes"] = pd.to_datetime(df_temporal["anomes"], errors="coerce")
            df_temporal = df_temporal.sort_values("anomes")

        return (
            df_filtros, df_mapa, df_dist, df_temporal, df_perfil,
            df_ocupacao, df_interacao, df_dist_cat, df_sample_boxplot
        )
    except FileNotFoundError as e:
        st.error(
            "ERRO: Um arquivo de dados agregados não foi encontrado. "
            "Certifique-se de que a pasta 'app_data' existe e contém todos os CSVs. "
            f"Detalhes: {e}"
        )
        # Retorno padrão com Nones para manter assinatura da função
        return (None,)*9

# --- CARREGANDO OS DADOS ---
dfs = carregar_dados_agregados()
(
    df_filtros, df_mapa, df_dist, df_temporal, df_perfil,
    df_ocupacao, df_interacao, df_dist_cat, df_sample_boxplot
) = dfs

# --- TÍTULO E INTRODUÇÃO ---
st.title("Decisões Sob Risco: Uma Análise Interativa do Investidor Brasileiro")
st.markdown("Análise baseada na dissertação de Vinícios Silveira (Fucape, 2025).")
st.warning(
    "🔒 **Privacidade:** Este aplicativo exibe análises de um conjunto de dados real e confidencial. "
    "Nenhum dado individual é exposto. Todas as visualizações são baseadas em dados pré-agregados "
    "para garantir o anonimato e a conformidade com a LGPD."
)

# --- VALIDAÇÃO DE CARGA ---
if any(df is None for df in dfs):
    st.stop()

# --- BARRA LATERAL (SIDEBAR) COM FILTROS APRIMORADOS ---
st.sidebar.header("Painel de Filtros")

# Filtro de Região
opcoes_regiao = sorted([r for r in df_filtros["regiao"].dropna().unique() if r != "Não Identificada"])
if not opcoes_regiao:
    opcoes_regiao = sorted(df_filtros["regiao"].dropna().unique())
regioes_selecionadas = st.sidebar.multiselect(
    "Selecione a(s) Região(ões)",
    options=opcoes_regiao,
    default=opcoes_regiao
)

# Filtro de Faixa de Renda
opcoes_renda = sorted(pd.Series(df_filtros["faixa_renda"].dropna().unique(), dtype="object").tolist())
faixas_renda_selecionadas = st.sidebar.multiselect(
    "Selecione a(s) Faixa(s) de Renda",
    options=opcoes_renda,
    default=opcoes_renda
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Adicionais")

# Filtro por Perfil de Investidor
opcoes_perfil = sorted(pd.Series(df_perfil["perfil_grupo"].dropna().unique(), dtype="object").tolist())
perfis_selecionados = st.sidebar.multiselect(
    "Selecione o(s) Perfil(is) de Investidor",
    options=opcoes_perfil,
    default=opcoes_perfil
)

# Filtro por Grupo de Ocupação
opcoes_ocupacao = sorted(pd.Series(df_ocupacao["grupo_ocupacao"].dropna().unique(), dtype="object").tolist())
ocupacoes_selecionadas = st.sidebar.multiselect(
    "Selecione o(s) Grupo(s) de Ocupação",
    options=opcoes_ocupacao,
    default=opcoes_ocupacao
)

# --- LÓGICA DE FILTRAGEM ---
df_kpis_filtrado = df_filtros[
    (df_filtros["regiao"].isin(regioes_selecionadas)) &
    (df_filtros["faixa_renda"].isin(faixas_renda_selecionadas))
]
df_temporal_filtrado = df_temporal[df_temporal["regiao"].isin(regioes_selecionadas)]
df_perfil_filtrado = df_perfil[df_perfil["perfil_grupo"].isin(perfis_selecionados)]
df_ocupacao_filtrada = df_ocupacao[df_ocupacao["grupo_ocupacao"].isin(ocupacoes_selecionadas)]

# --- ABAS COM AS ANÁLISES ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Visão Geral", "🌍 Análise Geográfica", "📈 Análise Temporal", "👤 Análise por Perfil",
    "💼 Análise por Ocupação", "💡 Renda vs. Complexidade", "📜 Dissertação e Materiais"
])

# -------------------- ABA 1 --------------------
with tab1:
    st.header("Visão Geral da Amostra")

    # KPIs Dinâmicos (afetados pelos filtros da sidebar)
    st.subheader("Métricas da Seleção Atual")
    if not df_kpis_filtrado.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Diversificação Média", f"{df_kpis_filtrado['diversificacao_media'].mean():.2%}")
        col2.metric("Renda Média", f"R$ {df_kpis_filtrado['renda_media'].mean():,.2f}")
        col3.metric("Proporção com Ativos Complexos", f"{df_kpis_filtrado['proporcao_complex'].mean():.2%}")
    else:
        st.warning("Nenhum dado disponível para a seleção de filtros atual.")

    st.markdown("---")

    # --- NOVAS VISUALIZAÇÕES ---
    st.subheader("Distribuição da Diversificação na Amostra Completa")

    # Gráfico de Barras com Categorias
    st.markdown("#### Níveis de Diversificação")
    fig_dist_cat = px.bar(
        df_dist_cat,
        x="nivel_diversificacao",
        y="percentual",
        title="Percentual de Investidores por Nível de Diversificação",
        text_auto=".2%",
        labels={"nivel_diversificacao": "Nível de Diversificação", "percentual": "Percentual de Investidores"}
    )
    fig_dist_cat.update_layout(
        xaxis={
            "categoryorder": "array",
            "categoryarray": ["Nenhuma Diversificação (0%)", "Baixa (1%-25%)", "Média (26%-50%)", "Alta (>50%)"]
        }
    )
    st.plotly_chart(fig_dist_cat, use_container_width=True)

    with st.expander("🔍 Como interpretar este gráfico?"):
        st.markdown(
            "Este gráfico agrupa os investidores em quatro categorias claras, mostrando que a grande maioria "
            "da amostra possui uma diversificação nula ou baixa — um achado chave da pesquisa."
        )

    # Box Plot por Região
    st.markdown("#### Análise Estatística da Diversificação por Região")
    fig_boxplot = px.box(
        df_sample_boxplot,
        x="regiao",
        y="diver",
        color="regiao",
        title="Distribuição da Diversificação por Região",
        labels={"regiao": "Região", "diver": "Índice de Diversificação"}
    )
    st.plotly_chart(fig_boxplot, use_container_width=True)

    with st.expander("🔍 Como interpretar este gráfico?"):
        st.markdown(
            "- A **linha central** é a mediana (50%).\n"
            "- A **caixa** cobre o intervalo interquartil (25%–75%).\n"
            "- As **antenas** mostram a maior parte da distribuição.\n"
            "- **Pontos** fora das antenas são outliers.\n"
            "Permite comparar não só médias, mas toda a dispersão entre as regiões."
        )

# -------------------- ABA 2 --------------------
with tab2:
    st.header("Análise Geográfica do Investidor Brasileiro")
    st.markdown("Explore como as métricas financeiras se distribuem pelo território nacional.")

    diretorio = _base_dir()
    caminho_geojson = diretorio / "brasil_estados.json"

    try:
        with open(caminho_geojson, "r", encoding="utf-8") as f:
            geojson_brasil = json.load(f)

        metrica_selecionada = st.selectbox(
            "Selecione a Métrica para Visualizar no Mapa:",
            options=["Diversificação Média", "Renda Média"]
        )
        coluna_cor = "diversificacao_media" if metrica_selecionada == "Diversificação Média" else "renda_media"

        fig_mapa = px.choropleth(
            df_mapa,
            geojson=geojson_brasil,
            locations="UF_CADASTRO",
            featureidkey="id",
            color=coluna_cor,
            color_continuous_scale="Viridis",
            hover_name="UF_CADASTRO",
            hover_data={
                "diversificacao_media": ":.2%",
                "renda_media": ":.2f"
            },
            labels={
                "diversificacao_media": "Diversificação Média",
                "renda_media": "Renda Média (R$)"
            },
            projection="mercator"
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(
            title_text=f"{metrica_selecionada} por Estado",
            margin={"r": 0, "t": 40, "l": 0, "b": 0}
        )
        st.plotly_chart(fig_mapa, use_container_width=True)

    except FileNotFoundError:
        st.error("ERRO: Arquivo `brasil_estados.json` não encontrado na raiz do projeto.")

# -------------------- ABA 3 --------------------
with tab3:
    st.header("Evolução Temporal da Diversificação")
    if df_temporal_filtrado.empty:
        st.info("A seleção atual não possui dados temporais para as regiões escolhidas.")
    else:
        fig_temporal = px.line(
            df_temporal_filtrado,
            x="anomes",
            y="diver",
            color="regiao",
            title="Média de Diversificação por Região ao Longo do Tempo",
            labels={"anomes": "Data", "diver": "Diversificação Média", "regiao": "Região"}
        )
        st.plotly_chart(fig_temporal, use_container_width=True)

# -------------------- ABA 4 --------------------
with tab4:
    st.header("Análise por Perfil de Investidor (API)")
    st.markdown("Explore a diversificação e a adoção de produtos complexos por perfil de risco.")

    if df_perfil_filtrado.empty:
        st.info("A seleção atual não possui dados para os perfis escolhidos.")
    else:
        df_perfil_vis = df_perfil_filtrado.sort_values(by="diversificacao_media", ascending=False)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Diversificação Média")
            fig_perfil_diver = px.bar(
                df_perfil_vis, x="perfil_grupo", y="diversificacao_media", text_auto=".2%"
            )
            st.plotly_chart(fig_perfil_diver, use_container_width=True)
        with col2:
            st.subheader("Adoção de Produtos Complexos")
            fig_perfil_complex = px.bar(
                df_perfil_vis, x="perfil_grupo", y="proporcao_complex", text_auto=".2%"
            )
            st.plotly_chart(fig_perfil_complex, use_container_width=True)

# -------------------- ABA 5 --------------------
with tab5:
    st.header("Análise por Grupo de Ocupação")
    st.markdown("Como a diversificação do portfólio se distribui entre diferentes áreas profissionais?")

    if df_ocupacao_filtrada.empty:
        st.info("A seleção atual não possui dados para os grupos de ocupação escolhidos.")
    else:
        df_ocupacao_vis = df_ocupacao_filtrada.sort_values(by="diversificacao_media", ascending=False)
        st.subheader("Diversificação Média por Ocupação")
        fig_ocup_diver = px.bar(
            df_ocupacao_vis,
            x="diversificacao_media",
            y="grupo_ocupacao",
            orientation="h",
            text_auto=".2%",
            labels={"grupo_ocupacao": "Grupo de Ocupação", "diversificacao_media": "Diversificação Média"}
        )
        fig_ocup_diver.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_ocup_diver, use_container_width=True)

# -------------------- ABA 6 --------------------
with tab6:
    st.header("Análise de Interação: Renda vs. Complexidade")
    st.markdown("Como a estrutura do portfólio dos investidores difere entre as faixas de renda.")

    if df_interacao.empty:
        st.info("Não há dados de interação para a seleção atual.")
    else:
        col1, col2 = st.columns(2)
        media_complexos = df_interacao[df_interacao["complex"] == "Possui Ativos Complexos"]["diversificacao_media"].mean()
        media_simples = df_interacao[df_interacao["complex"] == "Apenas Ativos Simples"]["diversificacao_media"].mean()
        col1.metric("Diversificação Média (com Ativos Complexos)", f"{media_complexos:.2%}")
        col2.metric("Diversificação Média (apenas Ativos Simples)", f"{media_simples:.2%}")

        st.markdown("---")
        st.subheader("Composição de Investidores por Faixa de Renda")
        fig_composicao = px.bar(
            df_interacao,
            x="faixa_renda",
            y="total_clientes",
            color="complex",
            title="Divisão entre Carteiras Simples vs. Complexas por Faixa de Renda",
            labels={
                "faixa_renda": "Faixa de Renda",
                "total_clientes": "Número de Clientes",
                "complex": "Tipo de Carteira"
            },
            text_auto=True
        )
        st.plotly_chart(fig_composicao, use_container_width=True)

# -------------------- ABA 7 --------------------
with tab7:
    diretorio = _base_dir()
    caminho_materiais = diretorio / "materiais"

    st.header("Dissertação e Materiais de Apoio")
    st.markdown("Acesse aqui o trabalho completo, o podcast explicativo e os scripts de análise.")

    # PDF
    st.subheader("Leia a Dissertação Completa")
    arquivo_pdf_path = caminho_materiais / "DISSERTAÇÃO_Vinicios.pdf"
    try:
        with open(arquivo_pdf_path, "rb") as pdf_file:
            PDFbyte = pdf_file.read()
        st.download_button(
            label="⬇️ Baixar o PDF da Dissertação",
            data=PDFbyte,
            file_name="DISSERTAÇÃO_Vinicios.pdf",
            mime="application/pdf"
        )
        with st.expander("📖 Abrir leitor de PDF online (pode não ser compatível com todos os navegadores)"):
            base64_pdf = base64.b64encode(PDFbyte).decode("utf-8")
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
    except FileNotFoundError:
        st.error("ERRO: Arquivo da dissertação não encontrado em 'materiais/DISSERTAÇÃO_Vinicios.pdf'.")

    st.markdown("---")

    # Áudio
    st.subheader("Podcast: A Pesquisa em 15 Minutos")
    arquivo_audio_path = caminho_materiais / "podcast_dissertacao.mp3"
    if arquivo_audio_path.exists():
        st.audio(str(arquivo_audio_path))
    else:
        st.error(f"ERRO: Arquivo de áudio ('{arquivo_audio_path.name}') não encontrado.")

    st.markdown("---")

    # Script .do
    st.subheader("Faça o Download do Script de Análise (.do)")
    arquivo_do_path = caminho_materiais / "Trabalho_Completo_Reestruturado.do"
    try:
        with open(arquivo_do_path, "r", encoding="utf-8") as f:
            do_file_content = f.read()
        st.download_button(
            label="Clique aqui para baixar o arquivo .do",
            data=do_file_content,
            file_name="script_dissertacao_stata.do",
            mime="text/plain"
        )
    except FileNotFoundError:
        st.error(f"ERRO: Arquivo do Stata ('{arquivo_do_path.name}') não encontrado.")
