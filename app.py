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

# --- FUNÇÃO DE CARREGAMENTO DE DADOS (COM CACHE) ---
@st.cache_data
def carregar_dados_agregados():
    """Carrega os arquivos de resumo pré-calculados de forma robusta."""
    try:
        diretorio_script = Path(__file__).parent
        caminho_app_data = diretorio_script / "app_data"

        df_filtros = pd.read_csv(caminho_app_data / "dados_agregados_filtros.csv")
        df_mapa = pd.read_csv(caminho_app_data / "dados_mapa_uf.csv")
        df_dist = pd.read_csv(caminho_app_data / "distribuicao_diversificacao.csv")
        df_temporal = pd.read_csv(caminho_app_data / "evolucao_temporal_regional.csv")
        df_perfil = pd.read_csv(caminho_app_data / "perfil_investidor_agregado.csv")
        df_ocupacao = pd.read_csv(caminho_app_data / "ocupacao_agregado.csv")
        df_interacao = pd.read_csv(caminho_app_data / "interacao_renda_complex_agregado.csv")

        df_temporal['anomes'] = pd.to_datetime(df_temporal['anomes'])
        return df_filtros, df_mapa, df_dist, df_temporal, df_perfil, df_ocupacao, df_interacao
        
    except FileNotFoundError as e:
        st.error(
            f"ERRO: Um arquivo de dados agregados não foi encontrado. "
            f"Certifique-se de que a pasta 'app_data' existe e contém todos os CSVs. Detalhe: {e}"
        )
        return None, None, None, None, None, None, None

# --- CARREGANDO OS DADOS ---
df_filtros, df_mapa, df_dist, df_temporal, df_perfil, df_ocupacao, df_interacao = carregar_dados_agregados()

# --- TÍTULO E INTRODUÇÃO ---
st.title("Decisões Sob Risco: Uma Análise Interativa do Investidor Brasileiro")
st.markdown("Análise baseada na dissertação de Vinícios Silveira (Fucape, 2025).")
st.warning(
    "🔒 **Privacidade:** Este aplicativo exibe análises de um conjunto de dados real e confidencial. "
    "Nenhum dado individual é exposto. Todas as visualizações são baseadas em dados pré-agregados "
    "para garantir o anonimato e a conformidade com a LGPD."
)

# --- APLICAÇÃO ---
# Verifica se todos os dataframes foram carregados antes de continuar
if all(df is not None for df in [df_filtros, df_mapa, df_dist, df_temporal, df_perfil, df_ocupacao, df_interacao]):

    # --- BARRA LATERAL (SIDEBAR) COM FILTROS APRIMORADOS ---
    st.sidebar.header("Painel de Filtros")

    # Filtro de Região (limpo e como menu suspenso)
    opcoes_regiao = sorted([r for r in df_filtros['regiao'].unique() if r != 'Não Identificada'])
    regioes_selecionadas = st.sidebar.multiselect(
        "Selecione a(s) Região(ões)",
        options=opcoes_regiao,
        default=opcoes_regiao
    )

    # Filtro de Faixa de Renda (como menu suspenso)
    opcoes_renda = df_filtros['faixa_renda'].unique()
    faixas_renda_selecionadas = st.sidebar.multiselect(
        "Selecione a(s) Faixa(s) de Renda",
        options=opcoes_renda,
        default=opcoes_renda
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("Filtros Adicionais")

    # Filtro por Perfil de Investidor
    opcoes_perfil = df_perfil['perfil_grupo'].unique()
    perfis_selecionados = st.sidebar.multiselect(
        "Selecione o(s) Perfil(is) de Investidor",
        options=opcoes_perfil,
        default=opcoes_perfil
    )

    # Filtro por Grupo de Ocupação
    opcoes_ocupacao = df_ocupacao['grupo_ocupacao'].unique()
    ocupacoes_selecionadas = st.sidebar.multiselect(
        "Selecione o(s) Grupo(s) de Ocupação",
        options=opcoes_ocupacao,
        default=opcoes_ocupacao
    )

    # --- LÓGICA DE FILTRAGEM ---
    # Aplica os filtros aos dataframes que serão usados nas abas
    df_kpis_filtrado = df_filtros[
        (df_filtros['regiao'].isin(regioes_selecionadas)) &
        (df_filtros['faixa_renda'].isin(faixas_renda_selecionadas))
    ]
    df_temporal_filtrado = df_temporal[df_temporal['regiao'].isin(regioes_selecionadas)]
    df_perfil_filtrado = df_perfil[df_perfil['perfil_grupo'].isin(perfis_selecionados)]
    df_ocupacao_filtrada = df_ocupacao[df_ocupacao['grupo_ocupacao'].isin(ocupacoes_selecionadas)]


    # --- ABAS COM AS ANÁLISES ---
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Visão Geral", "🌍 Análise Geográfica", "📈 Análise Temporal", "👤 Análise por Perfil",
        "💼 Análise por Ocupação", "💡 Renda vs. Complexidade", "📜 Dissertação e Materiais"
    ])

    with tab1:
        st.header("Estatísticas Descritivas da Seleção")
        if not df_kpis_filtrado.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Diversificação Média", f"{df_kpis_filtrado['diversificacao_media'].mean():.2%}")
            col2.metric("Renda Média", f"R$ {df_kpis_filtrado['renda_media'].mean():,.2f}")
            col3.metric("Proporção com Ativos Complexos", f"{df_kpis_filtrado['proporcao_complex'].mean():.2%}")
        else:
            st.warning("Nenhum dado disponível para a seleção de filtros atual.")

        st.markdown("---")
        st.subheader("Distribuição Geral da Diversificação na Amostra Completa")
        fig_dist = px.bar(df_dist, x='faixa_diversificacao', y='percentual', labels={'faixa_diversificacao': 'Nível de Diversificação (0 a 1)', 'percentual': 'Percentual de Observações'})
        st.plotly_chart(fig_dist, use_container_width=True)

    with tab2:
        st.header("Análise Geográfica do Investidor Brasileiro")
        st.markdown("Explore como as métricas financeiras se distribuem pelo território nacional.")
        
        diretorio_script = Path(__file__).parent
        caminho_geojson = diretorio_script / "brasil_estados.json"

        try:
            with open(caminho_geojson, 'r', encoding='utf-8') as f:
                geojson_brasil = json.load(f)

            metrica_selecionada = st.selectbox(
                "Selecione a Métrica para Visualizar no Mapa:",
                options=['Diversificação Média', 'Renda Média']
            )
            coluna_cor = 'diversificacao_media' if metrica_selecionada == 'Diversificação Média' else 'renda_media'

            fig_mapa = px.choropleth(
                df_mapa, geojson=geojson_brasil, locations='UF_CADASTRO',
                featureidkey="id", color=coluna_cor,
                color_continuous_scale="Viridis", hover_name='UF_CADASTRO',
                hover_data={'diversificacao_media': ':.2%', 'renda_media': ':,.2f'},
                labels={'diversificacao_media': 'Diversificação Média', 'renda_media': 'Renda Média (R$)'},
                projection="mercator"
            )
            fig_mapa.update_geos(fitbounds="locations", visible=False)
            fig_mapa.update_layout(title_text=f"{metrica_selecionada} por Estado", margin={"r":0,"t":40,"l":0,"b":0})
            st.plotly_chart(fig_mapa, use_container_width=True)
            
        except FileNotFoundError:
            st.error(f"ERRO: Arquivo `brasil_estados.json` não encontrado. Verifique se ele está na pasta raiz do projeto.")

    with tab3:
        st.header("Evolução Temporal da Diversificação")
        fig_temporal = px.line(
            df_temporal_filtrado, x='anomes', y='diver', color='regiao',
            title='Média de Diversificação por Região ao Longo do Tempo',
            labels={'anomes': 'Data', 'diver': 'Diversificação Média', 'regiao': 'Região'}
        )
        st.plotly_chart(fig_temporal, use_container_width=True)

    with tab4:
        st.header("Análise por Perfil de Investidor (API)")
        st.markdown("Explore a diversificação e a adoção de produtos complexos por perfil de risco.")
        
        df_perfil_vis = df_perfil_filtrado.sort_values(by='diversificacao_media', ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Diversificação Média")
            fig_perfil_diver = px.bar(df_perfil_vis, x='perfil_grupo', y='diversificacao_media', text_auto='.2%')
            st.plotly_chart(fig_perfil_diver, use_container_width=True)
        with col2:
            st.subheader("Adoção de Produtos Complexos")
            fig_perfil_complex = px.bar(df_perfil_vis, x='perfil_grupo', y='proporcao_complex', text_auto='.2%')
            st.plotly_chart(fig_perfil_complex, use_container_width=True)

    with tab5:
        st.header("Análise por Grupo de Ocupação")
        st.markdown("Como a diversificação do portfólio se distribui entre diferentes áreas profissionais?")
        
        df_ocupacao_vis = df_ocupacao_filtrada.sort_values(by='diversificacao_media', ascending=False)
        st.subheader("Diversificação Média por Ocupação")
        fig_ocup_diver = px.bar(
            df_ocupacao_vis, x='diversificacao_media', y='grupo_ocupacao',
            orientation='h', text_auto='.2%',
            labels={'grupo_ocupacao': 'Grupo de Ocupação', 'diversificacao_media': 'Diversificação Média'}
        )
        fig_ocup_diver.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_ocup_diver, use_container_width=True)

    with tab6:
        st.header("Análise de Interação: Renda vs. Complexidade")
        st.markdown("Como a estrutura do portfólio dos investidores difere entre as faixas de renda.")
        
        col1, col2 = st.columns(2)
        media_complexos = df_interacao[df_interacao['complex'] == 'Possui Ativos Complexos']['diversificacao_media'].mean()
        media_simples = df_interacao[df_interacao['complex'] == 'Apenas Ativos Simples']['diversificacao_media'].mean()
        col1.metric("Diversificação Média (com Ativos Complexos)", f"{media_complexos:.2%}")
        col2.metric("Diversificação Média (apenas Ativos Simples)", f"{media_simples:.2%}")

        st.markdown("---")
        st.subheader("Composição de Investidores por Faixa de Renda")
        fig_composicao = px.bar(
            df_interacao, x="faixa_renda", y="total_clientes", color="complex",
            title="Divisão entre Carteiras Simples vs. Complexas por Faixa de Renda",
            labels={"faixa_renda": "Faixa de Renda", "total_clientes": "Número de Clientes", "complex": "Tipo de Carteira"},
            text_auto=True
        )
        st.plotly_chart(fig_composicao, use_container_width=True)

    with tab7:
        st.header("Dissertação e Materiais de Apoio")
        st.markdown("Acesse aqui o trabalho completo, o podcast explicativo e os scripts de análise.")
        
        diretorio_script = Path(__file__).parent
        caminho_materiais = diretorio_script / "materiais"
        
        st.subheader("Leia a Dissertação Completa")
        arquivo_pdf_path = caminho_materiais / "DISSERTAÇÃO_Vinicios.pdf"
        try:
            with open(arquivo_pdf_path, "rb") as f:
                base64_pdf = base64.b64encode(f.read()).decode('utf-8')
            pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
            st.markdown(pdf_display, unsafe_allow_html=True)
        except FileNotFoundError:
            st.error(f"ERRO: Arquivo da dissertação ('{arquivo_pdf_path.name}') não encontrado.")

        st.markdown("---")
        st.subheader("Podcast: A Pesquisa em 15 Minutos")
        arquivo_audio_path = caminho_materiais / "podcast_dissertacao.mp3"
        try:
            st.audio(str(arquivo_audio_path))
        except Exception:
            st.error(f"ERRO: Arquivo de áudio ('{arquivo_audio_path.name}') não encontrado.")

        st.markdown("---")
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