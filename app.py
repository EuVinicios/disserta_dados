# app.py
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Análise de Portfólio de Investidores Brasileiros",
    page_icon="🇧🇷",
    layout="wide"
)

# --- FUNÇÃO DE CARREGAMENTO DE DADOS (COM CACHE) ---
@st.cache_data
def carregar_dados_agregados():
    """Carrega os arquivos de resumo pré-calculados de forma robusta."""
    try:
        # Pega o caminho do diretório onde o script app.py está
        diretorio_script = Path(__file__).parent
        
        # Constrói o caminho para a pasta app_data
        caminho_app_data = diretorio_script / "app_data"

        # Carrega os arquivos usando o caminho completo e seguro
        df_filtros = pd.read_csv(caminho_app_data / "dados_agregados_filtros.csv")
        df_mapa = pd.read_csv(caminho_app_data / "dados_mapa_uf.csv")
        df_dist = pd.read_csv(caminho_app_data / "distribuicao_diversificacao.csv")
        df_temporal = pd.read_csv(caminho_app_data / "evolucao_temporal_regional.csv")
        df_temporal['anomes'] = pd.to_datetime(df_temporal['anomes'])
        return df_filtros, df_mapa, df_dist, df_temporal
    except FileNotFoundError:
        st.error(
            "ERRO: Arquivos de dados agregados não encontrados. "
            "Certifique-se de que a pasta 'app_data' e seus arquivos CSV estão no repositório."
        )
        return None, None, None, None

# --- CARREGANDO OS DADOS ---
df_filtros, df_mapa, df_dist, df_temporal = carregar_dados_agregados()

# --- TÍTULO E INTRODUÇÃO ---
st.title("Decisões Sob Risco: Uma Análise Interativa do Investidor Brasileiro")
st.markdown("Análise baseada na dissertação de Vinícios Silveira (Fucape, 2025).")
st.warning(
    "🔒 **Privacidade:** Este aplicativo exibe análises de um conjunto de dados real e confidencial. "
    "Nenhum dado individual é exposto. Todas as visualizações são baseadas em dados pré-agregados "
    "para garantir o anonimato e a conformidade com a LGPD."
)

# --- APLICAÇÃO ---
if df_filtros is not None:
    # --- BARRA LATERAL (SIDEBAR) ---
    st.sidebar.header("Filtros da Análise")
    
    regiao = st.sidebar.multiselect(
        "Região",
        options=df_filtros['regiao'].unique(),
        default=df_filtros['regiao'].unique()
    )

    faixa_renda = st.sidebar.multiselect(
        "Faixa de Renda",
        options=df_filtros['faixa_renda'].unique(),
        default=df_filtros['faixa_renda'].unique()
    )

    # Filtrando o DataFrame principal de agregados
    df_filtrado_kpis = df_filtros[
        (df_filtros['regiao'].isin(regiao)) &
        (df_filtros['faixa_renda'].isin(faixa_renda))
    ]

    # --- ABAS COM AS ANÁLISES ---
    tab1, tab2, tab3 = st.tabs(["📊 Visão Geral", "🌍 Análise Geográfica", "📈 Análise Temporal"])

    with tab1:
        st.header("Estatísticas Descritivas da Seleção")
        
        # Recalculando KPIs com base no grupo filtrado
        if not df_filtrado_kpis.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Diversificação Média", f"{df_filtrado_kpis['diversificacao_media'].mean():.2%}")
            col2.metric("Renda Média", f"R$ {df_filtrado_kpis['renda_media'].mean():,.2f}")
            col3.metric("Proporção com Ativos Complexos", f"{df_filtrado_kpis['proporcao_complex'].mean():.2%}")
        else:
            st.warning("Nenhum dado disponível para a seleção de filtros atual.")

        st.markdown("---")
        st.subheader("Distribuição Geral da Diversificação na Amostra Completa")
        fig_dist = px.bar(df_dist, x='faixa_diversificacao', y='percentual', labels={'faixa_diversificacao': 'Nível de Diversificação (0 a 1)', 'percentual': 'Percentual de Observações'})
        st.plotly_chart(fig_dist, use_container_width=True)

    with tab2:
        st.header("Análise da Diversificação pelo Brasil")
        st.info("O mapa abaixo não é afetado pelos filtros da barra lateral.")
        
        # (Nota: Este mapa requer um arquivo GeoJSON. O código está aqui como um exemplo funcional que você pode adaptar)
        st.subheader("Diversificação Média por Estado")
        st.markdown("Passe o mouse sobre um estado para ver os detalhes. Infelizmente, não possuo o arquivo GeoJSON para renderizar o mapa neste momento, mas o código está pronto.")
        # O código abaixo funcionaria se você tivesse um arquivo 'brasil_estados.json'
        # import json
        # try:
        #     with open('brasil_estados.json') as f:
        #         geojson_brasil = json.load(f)
        #     fig_mapa = px.choropleth(
        #         df_mapa,
        #         geojson=geojson_brasil,
        #         locations='UF_CADASTRO',
        #         featureidkey="properties.sigla",
        #         color='diversificacao_media',
        #         color_continuous_scale="Viridis",
        #         scope="south america",
        #         hover_name='UF_CADASTRO',
        #         hover_data={'renda_media': ':.2f'}
        #     )
        #     fig_mapa.update_geos(fitbounds="locations", visible=False)
        #     st.plotly_chart(fig_mapa, use_container_width=True)
        # except FileNotFoundError:
        # st.error("Arquivo 'brasil_estados.json' não encontrado. O mapa não pode ser exibido.")

    with tab3:
        st.header("Evolução Temporal da Diversificação")
        df_temporal_filtrado = df_temporal[df_temporal['regiao'].isin(regiao)]
        
        fig_temporal = px.line(
            df_temporal_filtrado,
            x='anomes',
            y='diver',
            color='regiao',
            title='Média de Diversificação por Região ao Longo do Tempo',
            labels={'anomes': 'Data', 'diver': 'Diversificação Média', 'regiao': 'Região'}
        )
        st.plotly_chart(fig_temporal, use_container_width=True)