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
        df_perfil = pd.read_csv('app_data/perfil_investidor_agregado.csv')
        df_ocupacao = pd.read_csv('app_data/ocupacao_agregado.csv')
        df_interacao = pd.read_csv('app_data/interacao_renda_complex_agregado.csv')
        return df_filtros, df_mapa, df_dist, df_temporal, df_perfil, df_ocupacao, df_interacao
    except FileNotFoundError:
        st.error(
            "ERRO: Arquivos de dados agregados não encontrados. "
            "Certifique-se de que a pasta 'app_data' e seus arquivos CSV estão no repositório."
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
    # Mude esta linha no seu app.py
    # Mude esta linha no seu app.py
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Visão Geral", "🌍 Análise Geográfica", "📈 Análise Temporal", "👤 Análise por Perfil", "💼 Análise por Ocupação", "💡 Renda vs. Complexidade"])

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
    st.header("Análise Geográfica do Investidor Brasileiro")
    st.markdown("Explore como as métricas financeiras se distribuem pelo território nacional.")

    # Importa a biblioteca para ler o arquivo JSON
    import json

    # Tenta carregar o arquivo GeoJSON que você baixou
    try:
        with open('brasil_estados.json') as f:
            geojson_brasil = json.load(f)
        
        if df_mapa is not None:
            # Controle para o usuário escolher a métrica
            metrica_selecionada = st.selectbox(
                "Selecione a Métrica para Visualizar no Mapa:",
                options=['Diversificação Média', 'Renda Média']
            )

            # Mapeia a escolha do usuário para o nome da coluna no DataFrame
            coluna_cor = 'diversificacao_media' if metrica_selecionada == 'Diversificação Média' else 'renda_media'

            # Cria o mapa interativo
            fig_mapa = px.choropleth(
                df_mapa,
                geojson=geojson_brasil,
                locations='UF_CADASTRO', # Coluna do seu DF com a sigla do estado
                featureidkey="properties.sigla", # Caminho para a sigla do estado no arquivo GeoJSON
                color=coluna_cor,
                color_continuous_scale="Viridis",
                scope="south america", # Foca o mapa na América do Sul
                hover_name='UF_CADASTRO',
                hover_data={'diversificacao_media': ':.2%', 'renda_media': ':,.2f'},
                labels={'diversificacao_media': 'Diversificação Média', 'renda_media': 'Renda Média (R$)'}
            )
            fig_mapa.update_geos(fitbounds="locations", visible=False)
            fig_mapa.update_layout(
                title_text=f"{metrica_selecionada} por Estado",
                margin={"r":0,"t":40,"l":0,"b":0}
            )
            
            st.plotly_chart(fig_mapa, use_container_width=True)

        else:
            st.warning("Dados do mapa não puderam ser carregados.")

    except FileNotFoundError:
        st.error(
            "ERRO: Arquivo `brasil_estados.json` não encontrado. "
            "Por favor, baixe o arquivo GeoJSON dos estados brasileiros e salve-o na pasta raiz do projeto."
        )

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

with tab4:
    st.header("Análise por Perfil de Investidor (API)")
    st.markdown("Esta seção explora como a diversificação e a adoção de produtos complexos variam entre os diferentes perfis de risco dos investidores.")

    if df_perfil is not None:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Diversificação Média por Perfil")
            fig_perfil_diver = px.bar(
                df_perfil,
                x='perfil_grupo',
                y='diversificacao_media',
                title='Diversificação Média',
                text_auto='.2%',
                labels={'perfil_grupo': 'Perfil de Risco', 'diversificacao_media': 'Diversificação Média'}
            )
            fig_perfil_diver.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_perfil_diver, use_container_width=True)

        with col2:
            st.subheader("Adoção de Produtos Complexos")
            fig_perfil_complex = px.bar(
                df_perfil,
                x='perfil_grupo',
                y='proporcao_complex',
                title='Proporção com Ativos Complexos',
                text_auto='.2%',
                labels={'perfil_grupo': 'Perfil de Risco', 'proporcao_complex': 'Proporção de Investidores'}
            )
            fig_perfil_complex.update_layout(xaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig_perfil_complex, use_container_width=True)

        with st.expander("🔍 Como interpretar estes gráficos?"):
            st.markdown("""
            - **Diversificação Média:** Mostra o quão diversificada é a carteira média de cada perfil. Perfis mais arrojados ou agressivos deveriam, teoricamente, apresentar maior diversificação.
            - **Adoção de Produtos Complexos:** Indica o percentual de investidores em cada perfil que possuem ao menos um ativo financeiro considerado complexo. Este é um forte indicador de sofisticação e está diretamente ligado à **Hipótese 1** da dissertação.
            """)
    else:
        st.warning("Dados de perfil não puderam ser carregados.")

with tab5:
    st.header("Análise por Grupo de Ocupação")
    st.markdown("Como a diversificação do portfólio e a sofisticação financeira se distribuem entre diferentes áreas profissionais?")

    if df_ocupacao is not None:
        # Controle para o usuário selecionar o número de grupos a exibir
        top_n = st.slider(
            'Selecione o número de grupos de ocupação para exibir:', 
            min_value=3, 
            max_value=len(df_ocupacao), 
            value=10,
            key='slider_ocupacao'
        )

        # Gráfico de Diversificação Média
        st.subheader(f"Top {top_n} Ocupações por Diversificação Média")
        df_ocupacao_sorted_diver = df_ocupacao.sort_values(by='diversificacao_media', ascending=False).head(top_n)
        
        fig_ocup_diver = px.bar(
            df_ocupacao_sorted_diver,
            x='diversificacao_media',
            y='grupo_ocupacao',
            orientation='h', # Gráfico horizontal para melhor leitura dos nomes
            title='Diversificação Média por Ocupação',
            text_auto='.2%',
            labels={'grupo_ocupacao': 'Grupo de Ocupação', 'diversificacao_media': 'Diversificação Média'}
        )
        fig_ocup_diver.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_ocup_diver, use_container_width=True)

        # Gráfico de Proporção com Ativos Complexos
        st.subheader(f"Top {top_n} Ocupações por Adoção de Produtos Complexos")
        df_ocupacao_sorted_complex = df_ocupacao.sort_values(by='proporcao_complex', ascending=False).head(top_n)

        fig_ocup_complex = px.bar(
            df_ocupacao_sorted_complex,
            x='proporcao_complex',
            y='grupo_ocupacao',
            orientation='h',
            title='Proporção com Ativos Complexos por Ocupação',
            text_auto='.2%',
            labels={'grupo_ocupacao': 'Grupo de Ocupação', 'proporcao_complex': 'Proporção de Investidores'}
        )
        fig_ocup_complex.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_ocup_complex, use_container_width=True)

    else:
        st.warning("Dados de ocupação não puderam ser carregados.")

with tab6:
    st.header("Análise de Interação: Renda, Complexidade e Diversificação")
    st.markdown("""
    Esta seção explora como a estrutura do portfólio dos investidores difere entre as faixas de renda.
    """)

    if df_interacao is not None:
        # --- Parte 1: KPIs Claros ---
        st.subheader("Diversificação Média por Grupo")
        col1, col2 = st.columns(2)
        
        # Filtra os dados para cada grupo
        media_complexos = df_interacao[df_interacao['complex'] == 'Possui Ativos Complexos']['diversificacao_media'].mean()
        media_simples = df_interacao[df_interacao['complex'] == 'Apenas Ativos Simples']['diversificacao_media'].mean()

        col1.metric("Média de Diversificação (com Ativos Complexos)", f"{media_complexos:.2%}")
        col2.metric("Média de Diversificação (apenas Ativos Simples)", f"{media_simples:.2%}")

        st.markdown("---")

        # --- Parte 2: Gráfico de Composição ---
        st.subheader("Composição de Investidores por Faixa de Renda")

        # Usamos o total de clientes para criar um gráfico de barras 100% empilhado
        fig_composicao = px.bar(
            df_interacao,
            x="faixa_renda",
            y="total_clientes",
            color="complex",
            title="Como cada Faixa de Renda se divide entre Carteiras Simples vs. Complexas",
            labels={
                "faixa_renda": "Faixa de Renda Mensal",
                "total_clientes": "Número de Clientes",
                "complex": "Tipo de Carteira"
            },
            text_auto=True # Adiciona os números nas barras
        )
        # Opcional: para forçar 100% (se preferir proporção em vez de contagem)
        # fig_composicao = px.bar(..., barnorm='percent')
        
        st.plotly_chart(fig_composicao, use_container_width=True)

        with st.expander("🔍 Como interpretar estes dados?"):
            st.markdown("""
            A análise mostra dois pontos importantes:

            1.  **KPIs:** A diversificação média para investidores com *apenas ativos simples* é **zero**, como definido pela metodologia. Em contraste, investidores que adotam produtos complexos atingem uma diversificação média de aproximadamente **32%**.

            2.  **Composição:** O gráfico de barras mostra a quantidade de clientes em cada categoria. Podemos observar a distribuição de investidores que optam ou não por produtos complexos dentro de cada faixa de renda. Isso nos permite analisar se a propensão a ter ativos complexos muda significativamente com o aumento da renda.
            """)
    else:
        st.warning("Dados da análise de interação não puderam ser carregados.")