# app.py
from pathlib import Path
import os  # <- para ler GA_ID via variável de ambiente
import streamlit as st
import pandas as pd
import plotly.express as px
import json
import base64

# =========================
# CONFIGURAÇÃO DA PÁGINA
# =========================
st.set_page_config(
    page_title="Análise de Portfólio de Investidores Brasileiros",
    page_icon="🇧🇷",
    layout="wide"
)

# =========================
# HELPERS
# =========================
def _base_dir() -> Path:
    try:
        return Path(__file__).parent
    except NameError:
        return Path.cwd()

def _inject_analytics():
    """Injeta Google Analytics se houver GA_ID (env var ou secrets). Silencioso se não houver."""
    ga_id = os.getenv("GA_ID")  # 1) tenta variável de ambiente (seguro local/dev)
    if not ga_id:
        try:
            ga_id = st.secrets["GA_ID"]  # 2) tenta secrets (pode não existir localmente)
        except Exception:
            ga_id = None

    if not ga_id:
        return  # sem GA_ID, não injeta nada

    st.components.v1.html(f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());
      gtag('config', '{ga_id}');
    </script>
    """, height=0)

def _get_query_params() -> dict:
    # Compatível com versões novas/antigas do Streamlit
    try:
        return dict(st.query_params)
    except AttributeError:
        qp = st.experimental_get_query_params()
        return {k: (v[0] if isinstance(v, list) and len(v) == 1 else ",".join(v)) for k, v in qp.items()}

def _set_query_params(d: dict):
    # Evita None; converte listas em strings CSV
    clean = {k: (",".join(v) if isinstance(v, (list, tuple)) else str(v)) for k, v in d.items() if v is not None}
    try:
        st.query_params.clear()
        st.query_params.update(clean)
    except AttributeError:
        st.experimental_set_query_params(**clean)

def _csv_or_parquet(path_csv: Path) -> Path:
    # Se houver .parquet com o mesmo basename, usa-o; senão, usa CSV
    pqt = path_csv.with_suffix(".parquet")
    return pqt if pqt.exists() else path_csv

def _read_table(path_like: Path) -> pd.DataFrame:
    p = _csv_or_parquet(path_like)
    if p.suffix == ".parquet":
        return pd.read_parquet(p)
    return pd.read_csv(p)

def _chips(label: str, values: list[str]) -> str:
    pills = "".join([f"<span class='chip'>{v}</span>" for v in values]) if values else "<span class='chip chip--muted'>—</span>"
    return f"<div class='chip-row'><span class='chip chip--label'>{label}</span>{pills}</div>"

def _copy_link_button():
    st.components.v1.html("""
    <div style="display:flex;align-items:center;gap:8px;margin:6px 0 2px 0;">
      <button id="copyLink" style="padding:6px 10px;border:1px solid #ddd;border-radius:8px;background:#fff;cursor:pointer">
        Copiar link desta visão
      </button>
      <span id="copiedMsg" style="font-size:0.9rem;color:#4caf50;"></span>
    </div>
    <script>
      const btn = document.getElementById('copyLink');
      const msg = document.getElementById('copiedMsg');
      btn.onclick = async () => {
        try {
          await navigator.clipboard.writeText(window.location.href);
          msg.textContent = "Link copiado!";
          setTimeout(()=> msg.textContent="", 1800);
        } catch(e) {
          msg.textContent = "Não foi possível copiar :(";
          setTimeout(()=> msg.textContent="", 1800);
        }
      }
    </script>
    """, height=40)

# =========================
# CARREGAMENTO (CACHE)
# =========================
@st.cache_data
def carregar_dados_agregados():
    """Carrega arquivos pré-agregados. Usa Parquet se existir; caso contrário, CSV."""
    diretorio = _base_dir()
    app_data = diretorio / "app_data"
    try:
        df_filtros = _read_table(app_data / "dados_agregados_filtros.csv")
        df_mapa = _read_table(app_data / "dados_mapa_uf.csv")
        df_dist = _read_table(app_data / "distribuicao_diversificacao.csv")
        df_temporal = _read_table(app_data / "evolucao_temporal_regional.csv")
        df_perfil = _read_table(app_data / "perfil_investidor_agregado.csv")
        df_ocupacao = _read_table(app_data / "ocupacao_agregado.csv")
        df_interacao = _read_table(app_data / "interacao_renda_complex_agregado.csv")
        df_dist_cat = _read_table(app_data / "dist_categorica_diversificacao.csv")
        df_sample_boxplot = _read_table(app_data / "sample_diversificacao_boxplot.csv")

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
            "Confirme a pasta 'app_data' e os arquivos necessários. "
            f"Detalhe: {e}"
        )
        return (None,) * 9

# =========================
# INÍCIO
# =========================
_injected_css = """
<style>
.chip-row { display:flex; flex-wrap:wrap; align-items:center; gap:6px; margin: 2px 0 8px 0; }
.chip { display:inline-flex; align-items:center; padding:4px 10px; border-radius:999px; border:1px solid #e0e0e0; background:#fafafa; font-size:0.86rem; }
.chip--label { background:#eef6ff; border-color:#cfe4ff; font-weight:600; }
.chip--muted { color:#999; }
.callout { padding:12px 14px; border:1px solid #eaeaea; border-radius:12px; background:#fcfcfc; }
.kpi { font-size:0.95rem; color:#666; margin-top:-10px; }
.hero { padding:14px 16px; border:1px solid #f0f0f0; border-radius:14px; background:linear-gradient(180deg,#ffffff,#fbfbff); }
.card { border:1px solid #eee; border-radius:14px; padding:14px; }
</style>
"""
st.markdown(_injected_css, unsafe_allow_html=True)
_inject_analytics()

st.title("Decisões Sob Risco: Uma Análise Interativa do Investidor Brasileiro")
st.markdown("Análise baseada na dissertação de Vinícios Silveira (Fucape, 2025).")
st.warning(
    "🔒 **Privacidade:** Este aplicativo exibe análises de um conjunto de dados real e confidencial. "
    "Nenhum dado individual é exposto. Visualizações são pré-agregadas (LGPD)."
)

# Carrega dados
dfs = carregar_dados_agregados()
(df_filtros, df_mapa, df_dist, df_temporal, df_perfil,
 df_ocupacao, df_interacao, df_dist_cat, df_sample_boxplot) = dfs

if any(df is None for df in dfs):
    st.stop()

# =========================
# SIDEBAR (com leitura da URL)
# =========================
st.sidebar.header("Painel de Filtros")

# Opções base
opcoes_regiao = sorted([r for r in df_filtros["regiao"].dropna().unique() if r != "Não Identificada"]) or sorted(df_filtros["regiao"].dropna().unique())
opcoes_renda = sorted(pd.Series(df_filtros["faixa_renda"].dropna().unique(), dtype="object").tolist())
opcoes_perfil = sorted(pd.Series(df_perfil["perfil_grupo"].dropna().unique(), dtype="object").tolist())
opcoes_ocupacao = sorted(pd.Series(df_ocupacao["grupo_ocupacao"].dropna().unique(), dtype="object").tolist())

# Lê query params (se existirem) para setar defaults
qp = _get_query_params()
def _parse_list(key, all_options):
    val = qp.get(key)
    if not val:  # default = todas
        return all_options
    items = [v for v in str(val).split(",") if v]
    # mantém apenas itens válidos
    return [v for v in items if v in all_options] or all_options

regioes_selecionadas = st.sidebar.multiselect("Selecione a(s) Região(ões)", options=opcoes_regiao, default=_parse_list("regiao", opcoes_regiao))
faixas_renda_selecionadas = st.sidebar.multiselect("Selecione a(s) Faixa(s) de Renda", options=opcoes_renda, default=_parse_list("renda", opcoes_renda))

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Adicionais")
perfis_selecionados = st.sidebar.multiselect("Selecione o(s) Perfil(is) de Investidor", options=opcoes_perfil, default=_parse_list("perfil", opcoes_perfil))
ocupacoes_selecionadas = st.sidebar.multiselect("Selecione o(s) Grupo(s) de Ocupação", options=opcoes_ocupacao, default=_parse_list("ocup", opcoes_ocupacao))

# Atualiza query params sempre que filtros mudarem
_set_query_params({
    "regiao": regioes_selecionadas,
    "renda": faixas_renda_selecionadas,
    "perfil": perfis_selecionados,
    "ocup": ocupacoes_selecionadas
})

# =========================
# FILTROS ATIVOS (BADGES) + copiar link
# =========================
st.markdown(
    _chips("Região:", regioes_selecionadas) +
    _chips("Faixa de renda:", faixas_renda_selecionadas) +
    _chips("Perfil:", perfis_selecionados) +
    _chips("Ocupação:", ocupacoes_selecionadas),
    unsafe_allow_html=True
)
_copy_link_button()

# =========================
# FILTRAGEM
# =========================
df_kpis_filtrado = df_filtros[
    (df_filtros["regiao"].isin(regioes_selecionadas)) &
    (df_filtros["faixa_renda"].isin(faixas_renda_selecionadas))
]
df_temporal_filtrado = df_temporal[df_temporal["regiao"].isin(regioes_selecionadas)]
df_perfil_filtrado = df_perfil[df_perfil["perfil_grupo"].isin(perfis_selecionados)]
df_ocupacao_filtrada = df_ocupacao[df_ocupacao["grupo_ocupacao"].isin(ocupacoes_selecionadas)]

# KPIs curtos para hero
diver_med = df_kpis_filtrado["diversificacao_media"].mean() if not df_kpis_filtrado.empty else float("nan")
renda_med = df_kpis_filtrado["renda_media"].mean() if not df_kpis_filtrado.empty else float("nan")
complex_med = df_kpis_filtrado["proporcao_complex"].mean() if not df_kpis_filtrado.empty else float("nan")

# =========================
# ABAS (inclui Home e Implicações)
# =========================
home, tab1, tab2, tab3, tab4, tab5, tab6, tabImp, tab7 = st.tabs([
    "🏠 Início (História)", "📊 Visão Geral", "🌍 Análise Geográfica", "📈 Análise Temporal",
    "👤 Análise por Perfil", "💼 Análise por Ocupação", "💡 Renda vs. Complexidade",
    "🧭 Implicações", "📜 Dissertação e Materiais"
])

# -------------------- HOME --------------------
with home:
    st.markdown("### Uma história sobre **complexidade** e **contexto**")
    with st.container():
        colA, colB, colC = st.columns(3)
        with colA:
            st.markdown("#### Achado 1")
            st.markdown(
                "<div class='card'><b>Complexidade percebida derruba a diversificação</b>.<br>"
                "Reduzir o custo mental (linguagem simples, onboarding guiado) aumenta a adoção de classes e a diversificação.</div>",
                unsafe_allow_html=True
            )
        with colB:
            st.markdown("#### Achado 2")
            st.markdown(
                "<div class='card'><b>Estabilidade da renda regional → mais diversificação</b>.<br>"
                "Contextos com menor volatilidade de renda tendem a carteiras mais diversificadas.</div>",
                unsafe_allow_html=True
            )
        with colC:
            st.markdown("#### Achado 3")
            st.markdown(
                "<div class='card'><b>Alta renda: IDH local pesa menos</b>.<br>"
                "Efeito de 'isolamento da riqueza' suaviza o impacto do contexto local na composição da carteira.</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown("### KPIs da seleção atual")
    c1, c2, c3 = st.columns(3)
    c1.metric("Diversificação Média", f"{diver_med:.2%}" if pd.notnull(diver_med) else "—")
    c2.metric("Renda Média", f"R$ {renda_med:,.2f}" if pd.notnull(renda_med) else "—")
    c3.metric("Com ativos complexos", f"{complex_med:.2%}" if pd.notnull(complex_med) else "—")
    st.markdown("<p class='kpi'>*Estes valores obedecem aos filtros ativos acima.</p>", unsafe_allow_html=True)

    with st.expander("ℹ️ Método e glossário (resumo)"):
        st.markdown(
            "- **População/Período:** Investidores BB (2021–2024), dados agregados por privacidade.\n"
            "- **Diversificação:** proporção de classes não-correlacionadas na carteira.\n"
            "- **Complexidade:** presença/ausência de produtos tidos como complexos (ex.: multimercados, exterior, alternativos), "
            "usada como proxy de barreira cognitiva.\n"
            "- **Skew de renda (proxy de estabilidade):** medida de assimetria que capta menor probabilidade de quedas extremas.\n"
            "- **H1–H3:** (i) complexidade↑ → diversificação↑; (ii) estabilidade de renda↑ → diversificação↑; "
            "(iii) em alta renda, IDH local ≈ não significativo."
        )
    st.info("Dica: navegue pelas abas para explorar cada achado com os filtros do seu interesse. Use “Copiar link” para compartilhar exatamente esta visão.")

# -------------------- ABA 1 --------------------
with tab1:
    st.header("Visão Geral da Amostra")
    st.subheader("Métricas da Seleção Atual")
    if not df_kpis_filtrado.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Diversificação Média", f"{diver_med:.2%}")
        col2.metric("Renda Média", f"R$ {renda_med:,.2f}")
        col3.metric("Proporção com Ativos Complexos", f"{complex_med:.2%}")
    else:
        st.warning("Nenhum dado disponível para a seleção de filtros atual.")

    st.markdown("---")
    st.subheader("Distribuição da Diversificação na Amostra Completa")

    # Barras de níveis de diversificação
    st.markdown("#### Níveis de Diversificação")
    fig_dist_cat = px.bar(
        df_dist_cat,
        x="nivel_diversificacao", y="percentual",
        title="Percentual de Investidores por Nível de Diversificação",
        text_auto=".2%",
        labels={"nivel_diversificacao": "Nível de Diversificação", "percentual": "Percentual de Investidores"}
    )
    fig_dist_cat.update_layout(
        xaxis={"categoryorder": "array",
               "categoryarray": ["Nenhuma Diversificação (0%)", "Baixa (1%-25%)", "Média (26%-50%)", "Alta (>50%)"]}
    )
    st.plotly_chart(fig_dist_cat, use_container_width=True)
    with st.expander("🔍 Como interpretar"):
        st.markdown("Quatro categorias simples evidenciam concentração em **nula/baixa** diversificação — insight-chave da pesquisa.")

    # Box por região
    st.markdown("#### Análise Estatística da Diversificação por Região")
    fig_boxplot = px.box(
        df_sample_boxplot,
        x="regiao", y="diver", color="regiao",
        title="Distribuição da Diversificação por Região",
        labels={"regiao": "Região", "diver": "Índice de Diversificação"}
    )
    st.plotly_chart(fig_boxplot, use_container_width=True)
    with st.expander("🔍 Como interpretar"):
        st.markdown(
            "- **Linha central**: mediana.\n"
            "- **Caixa**: intervalo interquartil (25%–75%).\n"
            "- **Antenas**: abrangência principal da distribuição.\n"
            "- **Pontos fora**: outliers."
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

        metrica_selecionada = st.selectbox("Selecione a Métrica para Visualizar no Mapa:", options=["Diversificação Média", "Renda Média"])
        coluna_cor = "diversificacao_media" if metrica_selecionada == "Diversificação Média" else "renda_media"

        fig_mapa = px.choropleth(
            df_mapa, geojson=geojson_brasil, locations="UF_CADASTRO", featureidkey="id",
            color=coluna_cor, color_continuous_scale="Viridis",
            hover_name="UF_CADASTRO",
            hover_data={"diversificacao_media": ":.2%", "renda_media": ":.2f"},
            labels={"diversificacao_media": "Diversificação Média", "renda_media": "Renda Média (R$)"},
            projection="mercator"
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(title_text=f"{metrica_selecionada} por Estado", margin={"r":0,"t":40,"l":0,"b":0})
        st.plotly_chart(fig_mapa, use_container_width=True)
        with st.expander("🔍 Como interpretar"):
            st.markdown("Cores mais **escuras** indicam valores **mais altos**. Use os filtros para comparar regiões equivalentes em renda/perfil.")

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
            x="anomes", y="diver", color="regiao",
            title="Média de Diversificação por Região ao Longo do Tempo",
            labels={"anomes": "Data", "diver": "Diversificação Média", "regiao": "Região"}
        )
        st.plotly_chart(fig_temporal, use_container_width=True)
        with st.expander("🔍 Como interpretar"):
            st.markdown("Observe **tendências e convergências** entre regiões; quedas/picos sinalizam mudanças de contexto (ex.: renda, fluxo, notícias).")

# -------------------- ABA 4 --------------------
with tab4:
    st.header("Análise por Perfil de Investidor (API)")
    st.markdown("Diversificação e adoção de produtos complexos por perfil de risco.")
    if df_perfil_filtrado.empty:
        st.info("A seleção atual não possui dados para os perfis escolhidos.")
    else:
        df_perfil_vis = df_perfil_filtrado.sort_values(by="diversificacao_media", ascending=False)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Diversificação Média")
            fig_perfil_diver = px.bar(df_perfil_vis, x="perfil_grupo", y="diversificacao_media", text_auto=".2%")
            st.plotly_chart(fig_perfil_diver, use_container_width=True)
        with col2:
            st.subheader("Adoção de Produtos Complexos")
            fig_perfil_complex = px.bar(df_perfil_vis, x="perfil_grupo", y="proporcao_complex", text_auto=".2%")
            st.plotly_chart(fig_perfil_complex, use_container_width=True)
        with st.expander("🔍 Como interpretar"):
            st.markdown("Perfis com **maior adoção de complexos** tendem a **maior diversificação**. Use isso para orientar educação/onboarding.")

# -------------------- ABA 5 --------------------
with tab5:
    st.header("Análise por Grupo de Ocupação")
    st.markdown("Como a diversificação se distribui entre áreas profissionais?")
    if df_ocupacao_filtrada.empty:
        st.info("A seleção atual não possui dados para os grupos de ocupação escolhidos.")
    else:
        df_ocupacao_vis = df_ocupacao_filtrada.sort_values(by="diversificacao_media", ascending=False)
        st.subheader("Diversificação Média por Ocupação")
        fig_ocup_diver = px.bar(
            df_ocupacao_vis, x="diversificacao_media", y="grupo_ocupacao",
            orientation="h", text_auto=".2%",
            labels={"grupo_ocupacao": "Grupo de Ocupação", "diversificacao_media": "Diversificação Média"}
        )
        fig_ocup_diver.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig_ocup_diver, use_container_width=True)
        with st.expander("🔍 Como interpretar"):
            st.markdown("Grupos com maior **conhecimento financeiro** ou **estabilidade de renda** tendem a diversificar mais.")

# -------------------- ABA 6 --------------------
with tab6:
    st.header("Análise de Interação: Renda vs. Complexidade")
    st.markdown("Como a estrutura do portfólio difere entre faixas de renda.")
    if df_interacao.empty:
        st.info("Não há dados de interação para a seleção atual.")
    else:
        col1, col2 = st.columns(2)
        media_complexos = df_interacao[df_interacao["complex"] == "Possui Ativos Complexos"]["diversificacao_media"].mean()
        media_simples = df_interacao[df_interacao["complex"] == "Apenas Ativos Simples"]["diversificacao_media"].mean()
        col1.metric("Diversificação Média (com complexos)", f"{media_complexos:.2%}")
        col2.metric("Diversificação Média (apenas simples)", f"{media_simples:.2%}")

        st.markdown("---")
        st.subheader("Composição por Faixa de Renda")
        fig_composicao = px.bar(
            df_interacao, x="faixa_renda", y="total_clientes", color="complex",
            title="Carteiras Simples vs. Complexas por Faixa de Renda",
            labels={"faixa_renda": "Faixa de Renda", "total_clientes": "Número de Clientes", "complex": "Tipo de Carteira"},
            text_auto=True
        )
        st.plotly_chart(fig_composicao, use_container_width=True)
        with st.expander("🔍 Como interpretar"):
            st.markdown("A **presença de complexos** cresce com renda, mas o **onboarding** reduz barreiras mesmo em faixas médias.")

# -------------------- ABA IMPLICAÇÕES --------------------
with tabImp:
    st.header("Implicações Práticas")
    st.markdown("**Como aplicar os achados** para pessoas investidoras e para o Banco.")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Para pessoas investidoras")
        st.markdown(
            "- **Trilhas anti-complexidade**: conteúdos curtos que reduzem jargão e mostram o passo-a-passo para 1º ativo complexo.\n"
            "- **Checklists de decisão**: 3 perguntas para cada nova classe (objetivo, prazo, tolerância a oscilação).\n"
            "- **Carteira degrau**: comece com 1 classe adicional e revise em 90 dias."
        )
    with c2:
        st.subheader("Para o Banco")
        st.markdown(
            "- **Onboarding guiado** em produtos de entrada (ex.: multimercado “light”, COE didático) para renda média.\n"
            "- **Prioridade por contexto**: regiões com renda menos estável → foco em produtos simples + liquidez; estáveis → escada de complexidade.\n"
            "- **Cartões de conversa** para gerentes: 3 bullets + mini-gráfico das vantagens da diversificação."
        )
    st.info("Use os filtros atuais para gerar insumos de atuação local. Compartilhe o link filtrado com o time.")

# -------------------- ABA 7 (MATERIAIS) --------------------
with tab7:
    diretorio = _base_dir()
    caminho_materiais = diretorio / "materiais"

    st.header("Dissertação e Materiais de Apoio")
    st.markdown("Acesse o trabalho completo, o podcast explicativo e os scripts de análise.")

    # PDF
    st.subheader("Leia a Dissertação Completa")
    arquivo_pdf_path = caminho_materiais / "DISSERTAÇÃO_Vinicios.pdf"
    try:
        with open(arquivo_pdf_path, "rb") as pdf_file:
            PDFbyte = pdf_file.read()
        st.download_button(
            label="⬇️ Baixar o PDF da Dissertação",
            data=PDFbyte, file_name="DISSERTAÇÃO_Vinicios.pdf", mime="application/pdf"
        )
        with st.expander("📖 Abrir leitor de PDF (pode não funcionar em todos navegadores)"):
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
            data=do_file_content, file_name="script_dissertacao_stata.do", mime="text/plain"
        )
    except FileNotFoundError:
        st.error(f"ERRO: Arquivo do Stata ('{arquivo_do_path.name}') não encontrado.")
