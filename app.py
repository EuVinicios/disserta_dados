# app.py
from pathlib import Path
import os  # para GA_ID via env var
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
    ga_id = os.getenv("GA_ID")
    if not ga_id:
        try:
            ga_id = st.secrets["GA_ID"]
        except Exception:
            ga_id = None
    if not ga_id:
        return
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
    try:
        return dict(st.query_params)
    except AttributeError:
        qp = st.experimental_get_query_params()
        return {k: (v[0] if isinstance(v, list) and len(v) == 1 else ",".join(v)) for k, v in qp.items()}

def _set_query_params(d: dict):
    clean = {k: (",".join(v) if isinstance(v, (list, tuple)) else str(v)) for k, v in d.items() if v is not None}
    try:
        st.query_params.clear()
        st.query_params.update(clean)
    except AttributeError:
        st.experimental_set_query_params(**clean)

def _csv_or_parquet(path_csv: Path) -> Path:
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

def _order_income_bands(df_filtros: pd.DataFrame) -> list[str]:
    """
    Ordena as faixas de renda por renda média (asc), para gráficos ficarem “crescentes”.
    Fallback: ordem alfabética.
    """
    try:
        s = df_filtros.groupby("faixa_renda", dropna=True)["renda_media"].mean().sort_values()
        return list(s.index)
    except Exception:
        vals = pd.Series(df_filtros["faixa_renda"].dropna().unique(), dtype="object").tolist()
        return sorted(vals)

def _toast(msg: str):
    try:
        st.toast(msg)
    except Exception:
        st.info(msg)

def _switch_tab(label: str):
    """Troca para a aba cujo rótulo começa com `label` (ex.: '💡 Renda vs. Complexidade')."""
    import json as _json
    st.components.v1.html(f"""
    <script>
      const target = {_json.dumps(label)};
      const tabs = window.parent.document.querySelectorAll('button[role="tab"]');
      for (const t of tabs) {{
        const txt = (t.innerText || t.textContent || '').trim();
        if (txt.startsWith(target)) {{ t.click(); break; }}
      }}
    </script>
    """, height=0)

def _complexity_uplift_stats(df_interacao):
    """Retorna (media_complexos, media_simples, uplift) em pontos (diferença absoluta)."""
    try:
        m_c = df_interacao[df_interacao["complex"] == "Possui Ativos Complexos"]["diversificacao_media"].mean()
        m_s = df_interacao[df_interacao["complex"] == "Apenas Ativos Simples"]["diversificacao_media"].mean()
        return m_c, m_s, (m_c - m_s)
    except Exception:
        return None, None, None

def _wealth_insulation_stats(df_filtros):
    """
    Mede a 'dispersão regional' da diversificação por faixa de renda.
    Retorna (faixa_baixa, faixa_alta, disp_baixa, disp_alta, gap = baixa - alta).
    """
    try:
        faixas_ord = df_filtros.groupby("faixa_renda", dropna=True)["renda_media"].mean().sort_values()
        faixa_baixa = faixas_ord.index[0]
        faixa_alta = faixas_ord.index[-1]
        disp_baixa = df_filtros[df_filtros["faixa_renda"] == faixa_baixa].groupby("regiao")["diversificacao_media"].mean().std()
        disp_alta  = df_filtros[df_filtros["faixa_renda"] == faixa_alta ].groupby("regiao")["diversificacao_media"].mean().std()
        return faixa_baixa, faixa_alta, float(disp_baixa), float(disp_alta), float(disp_baixa - disp_alta)
    except Exception:
        return None, None, None, None, None

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
.kpi { font-size:0.95rem; color:#666; margin-top:-10px; }
.hero { padding:14px 16px; border:1px solid #f0f0f0; border-radius:14px; background:linear-gradient(180deg,#ffffff,#fbfbff); }
.card { border:1px solid #eee; border-radius:14px; padding:14px; }
.tag { display:inline-block; font-size:.78rem; padding:4px 8px; border-radius:999px; background:#eef2ff; border:1px solid #dfe5ff; }
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

# Lê query params para defaults
qp = _get_query_params()
def _parse_list(key, all_options):
    val = qp.get(key)
    if not val:
        return all_options
    items = [v for v in str(val).split(",") if v]
    return [v for v in items if v in all_options] or all_options

regioes_selecionadas = st.sidebar.multiselect("Selecione a(s) Região(ões)", options=opcoes_regiao, default=_parse_list("regiao", opcoes_regiao))
faixas_renda_selecionadas = st.sidebar.multiselect("Selecione a(s) Faixa(s) de Renda", options=opcoes_renda, default=_parse_list("renda", opcoes_renda))

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros Adicionais")
perfis_selecionados = st.sidebar.multiselect("Selecione o(s) Perfil(is) de Investidor", options=opcoes_perfil, default=_parse_list("perfil", opcoes_perfil))
ocupacoes_selecionadas = st.sidebar.multiselect("Selecione o(s) Grupo(s) de Ocupação", options=opcoes_ocupacao, default=_parse_list("ocup", opcoes_ocupacao))

# Atualiza query params
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

# KPIs curtos da seleção
diver_med = df_kpis_filtrado["diversificacao_media"].mean() if not df_kpis_filtrado.empty else float("nan")
renda_med = df_kpis_filtrado["renda_media"].mean() if not df_kpis_filtrado.empty else float("nan")
complex_med = df_kpis_filtrado["proporcao_complex"].mean() if not df_kpis_filtrado.empty else float("nan")

# =========================
# ABAS (inclui Home e Implicações)
# =========================
home, tab1, tab2, tab3, tab4, tab5, tab6, tabImp, tabNotas, tab7 = st.tabs([
    "🏠 Início (História)", "📊 Visão Geral", "🌍 Análise Geográfica", "📈 Análise Temporal",
    "👤 Análise por Perfil", "💼 Análise por Ocupação", "💡 Renda vs. Complexidade",
    "🧭 Implicações", "🧪 Notas de Pesquisa", "📜 Dissertação e Materiais"
])

# -------------------- HOME (com destaque dos achados) --------------------
with home:
    # Estatísticas para os achados
    m_c, m_s, uplift = _complexity_uplift_stats(df_interacao)
    faixa_baixa, faixa_alta, disp_baixa, disp_alta, gap_disp = _wealth_insulation_stats(df_filtros)

    def _pp(x):
        return f"{x*100:.1f} p.p." if x is not None and pd.notnull(x) else "—"
    def _pct(x):
        return f"{x:.2%}" if x is not None and pd.notnull(x) else "—"

    st.markdown("### Dois achados que mudam a conversa")

    colL, colR = st.columns(2)

    # ----------------- Paradoxo da Complexidade -----------------
    with colL:
        with st.container(border=True):
            st.markdown("<span class='tag'>🧩 Paradoxo da Complexidade</span>", unsafe_allow_html=True)
            st.markdown("### Menos barreira cognitiva → mais diversificação")
            st.markdown(
                f"Carteiras com **ativos complexos**: **{_pct(m_c)}** vs. **{_pct(m_s)}** só com ativos simples. "
                f"**Uplift:** **{_pp(uplift)}**."
            )
            if st.button("Explorar: Renda vs. Complexidade", key="cta_complex"):
                _switch_tab("💡 Renda vs. Complexidade")
            with st.expander("Por que isso importa?"):
                st.markdown(
                    "- **Didática e onboarding** reduzem a barreira mental e aceleram a adoção da 2ª/3ª classe.\n"
                    "- Gera **diversificação prática** especialmente entre investidores de renda mais baixa."
                )
            with st.expander("Mais detalhes (da dissertação)"):
                st.markdown(
                    "- O efeito da **complexidade** na diversificação **varia com a renda** (interação significativa): "
                    "maior ganho em **rendas baixas**, atenuado nas **rendas altas**.\n"
                    "- Em renda baixa, produtos “complexos” servem de **porta de entrada**; em renda alta, podem virar **apostas concentradas**.\n"
                    "- Base teórica: **preferência por simplicidade** (custo cognitivo)."
                )

    # ----------------- Efeito Isolamento da Riqueza -----------------
    with colR:
        with st.container(border=True):
            st.markdown("<span class='tag'>💎 Efeito Isolamento da Riqueza</span>", unsafe_allow_html=True)
            st.markdown("### Em alta renda, o contexto local pesa menos")
            if all(v is not None for v in [faixa_baixa, faixa_alta, disp_baixa, disp_alta, gap_disp]):
                st.markdown(
                    f"**Dispersão regional** da diversificação cai de **{disp_baixa:.2f}** ({faixa_baixa}) "
                    f"para **{disp_alta:.2f}** ({faixa_alta}). Δ = **{gap_disp:.2f}**."
                )
            else:
                st.markdown("Em **alta renda**, a diferença entre regiões diminui — o **IDH local** explica menos a carteira.")
            if st.button("Explorar: Geografia", key="cta_wealth"):
                _switch_tab("🌍 Análise Geográfica")
            with st.expander("Por que isso importa?"):
                st.markdown(
                    "- **Estratégia por contexto**: regiões menos estáveis → simplicidade e liquidez; estáveis → escada de complexidade.\n"
                    "- Em **alta renda**, foque em curadoria, eficiência fiscal e objetivos — o contexto local pesa menos."
                )
            with st.expander("Mais detalhes (da dissertação)"):
                st.markdown(
                    "- Entre **alta renda**, o coeficiente do **IDH** fica **insignificante** → a riqueza atua como **isolante** "
                    "(assessoria, informação e plataformas ampliam o horizonte além do município)."
                )

    st.markdown("---")

    # KPIs da seleção atual
    st.markdown("### KPIs da seleção atual")
    c1, c2, c3 = st.columns(3)
    c1.metric("Diversificação Média", f"{diver_med:.2%}" if pd.notnull(diver_med) else "—")
    c2.metric("Renda Média", f"R$ {renda_med:,.2f}" if pd.notnull(renda_med) else "—")
    c3.metric("Com ativos complexos", f"{complex_med:.2%}" if pd.notnull(complex_med) else "—")
    st.markdown("<p class='kpi'>*Os KPIs acima respeitam os filtros ativos.</p>", unsafe_allow_html=True)

    with st.expander("ℹ️ Método e glossário (resumo)"):
        st.markdown(
            "- **População/Período:** Investidores BB (2021–2024), dados agregados por privacidade.\n"
            "- **Diversificação:** proporção de classes não-correlacionadas na carteira.\n"
            "- **Complexidade:** presença de produtos tidos como complexos (proxy de barreira cognitiva).\n"
            "- **Skew de renda:** assimetria (menor cauda de quedas = maior estabilidade).\n"
            "- **H1–H3:** (i) complexidade↑ → diversificação↑; (ii) estabilidade de renda↑ → diversificação↑; (iii) em alta renda, IDH local ≈ menos relevante."
        )

    st.info("Use “Copiar link” (no topo) para compartilhar esta visão com filtros aplicados.")

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
    st.subheader("Podcast: A Pesquisa em 10 Minutos")
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

# -------------------- ABA NOTAS DE PESQUISA --------------------
with tabNotas:
    st.header("Notas de Pesquisa")
    st.caption("Mini-explicações dos dois achados com base nos dados agregados do app.")

# ---------- 3.1 Paradoxo da Complexidade: efeito por faixa de renda ----------
    st.subheader("Paradoxo da Complexidade — interação com renda")
    order_bands = _order_income_bands(df_filtros)

    # >>> NOVO: usa o agregado por quantis, com fallback para a versão antiga por faixas
    from pathlib import Path
    caminho_app_data = Path(__file__).parent / "app_data"
    arq_quantis = caminho_app_data / "interacao_renda_complex_quantis.csv"

    if arq_quantis.exists():
        # ===== NOVA VISUALIZAÇÃO (QUANTIS) =====
        df_q = pd.read_csv(arq_quantis)

        ord_quantis = ['Q1 (↓ renda)', 'Q2', 'Q3', 'Q4', 'Q5 (↑ renda)']
        if 'renda_quantil' in df_q.columns:
            df_q['renda_quantil'] = pd.Categorical(
                df_q['renda_quantil'], categories=ord_quantis, ordered=True
            )
            df_q = df_q.sort_values(['renda_quantil', 'complex'])

        # (A) Slope chart: Simples vs Complexos por quantil de renda
        fig_slope = px.line(
            df_q, x="renda_quantil", y="diversificacao_media", color="complex",
            markers=True,
            labels={
                "renda_quantil": "Quantil de renda",
                "diversificacao_media": "Diversificação média",
                "complex": ""
            },
            title="Diversificação média por quantil — com e sem ativos complexos",
            hover_data={"total_clientes": True}
        )
        fig_slope.update_layout(yaxis=dict(tickformat=".0%"), margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_slope, use_container_width=True)

        # (B) Uplift (p.p.) = Complexos – Simples (por quantil de renda)
        piv_q = (
            df_q.pivot_table(index="renda_quantil", columns="complex", values="diversificacao_media")
                .reindex(ord_quantis)
        )
        if {"Possui Ativos Complexos", "Apenas Ativos Simples"}.issubset(set(piv_q.columns)):
            df_uplift_q = (
                (piv_q["Possui Ativos Complexos"] - piv_q["Apenas Ativos Simples"]) * 100
            ).rename("uplift_pp").reset_index()

            fig_uplift_q = px.line(
                df_uplift_q, x="renda_quantil", y="uplift_pp", markers=True,
                labels={"renda_quantil":"Quantil de renda", "uplift_pp":"Ganho ao incluir complexos (p.p.)"},
                title="Ganho observado ao incluir ativos complexos (p.p.) por quantil de renda"
            )
            st.plotly_chart(fig_uplift_q, use_container_width=True)

        st.caption(
            "Nota: 'Apenas Ativos Simples' tem diversificação = 0% por construção; "
            "o *uplift* representa o ganho médio ao incluir ativos complexos em cada estrato de renda."
        )

        with st.expander("Como ler / por que importa (complexidade)"):
            st.markdown(
                "- **Linhas com marcadores:** comparam **lado a lado** (Com complexos vs. Só simples) em cada **quantil** de renda.\n"
                "- **Uplift (p.p.):** quanto a diversificação **sobe** ao incluir complexos. "
                "A tendência é **cair** nos quantis de renda mais altos → consistente com o efeito moderador da renda."
            )

    else:
        # ===== FALLBACK: mantém sua versão anterior por FAIXAS =====
        df_int = df_interacao.copy()
        if "total_clientes" not in df_int.columns:
            df_int["total_clientes"] = 1

        # Médias por faixa x tipo + n
        df_means = (
            df_int.groupby(["faixa_renda", "complex"], dropna=True)
                .agg(diversificacao_media=("diversificacao_media", "mean"),
                    n=("total_clientes", "sum"))
                .reset_index()
        )
        mapa_tipo = {"Possui Ativos Complexos": "Com complexos",
                    "Apenas Ativos Simples": "Só simples"}
        df_means["tipo"] = df_means["complex"].map(mapa_tipo)

        # (A) Barras agrupadas: comparação direta
        fig_comp = px.bar(
            df_means, x="faixa_renda", y="diversificacao_media", color="tipo",
            barmode="group", category_orders={"faixa_renda": order_bands},
            labels={"faixa_renda":"Faixa de renda", "diversificacao_media":"Diversificação média", "tipo":""},
            title="Diversificação média por faixa — com e sem ativos complexos",
            text_auto=".1%"
        )
        fig_comp.update_layout(yaxis=dict(tickformat=".0%"), margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_comp, use_container_width=True)

        # (B) Uplift em p.p. (com complexos – só simples)
        piv = df_means.pivot_table(index="faixa_renda", columns="tipo", values="diversificacao_media").reindex(order_bands)
        uplift = (piv.get("Com complexos") - piv.get("Só simples")) * 100
        df_uplift = uplift.rename("uplift_pp").reset_index().sort_values("uplift_pp", ascending=False)

        fig_u = px.bar(
            df_uplift, x="faixa_renda", y="uplift_pp",
            labels={"faixa_renda":"Faixa de renda", "uplift_pp":"Uplift de diversificação (p.p.)"},
            title="Ganho observado ao incluir ativos complexos (por faixa de renda)",
            text_auto=".1f"
        )
        fig_u.update_layout(margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig_u, use_container_width=True)

        with st.expander("Como ler / por que importa (complexidade)"):
            st.markdown(
                "- **Barras agrupadas:** comparação direta **lado a lado** (Com complexos vs. Só simples) em cada faixa.\n"
                "- **Uplift (p.p.):** o **quanto sobe** a diversificação ao incluir complexos."
            )

    # ---------- 3.2 Efeito Isolamento da Riqueza: dispersão regional vs renda ----------
    st.subheader("Efeito Isolamento da Riqueza — dispersão regional cai na alta renda")

    # Dispersão regional da diversificação por faixa (σ entre regiões)
    rows = []
    for faixa in order_bands:
        g = (df_filtros[df_filtros["faixa_renda"] == faixa]
             .groupby("regiao")["diversificacao_media"].mean())
        if len(g) > 1:
            rows.append({"faixa_renda": faixa, "disp_regional": float(g.std())})
    df_disp = pd.DataFrame(rows)

    if not df_disp.empty:
        fig_disp = px.line(
            df_disp, x="faixa_renda", y="disp_regional", markers=True,
            category_orders={"faixa_renda": order_bands},
            labels={"faixa_renda": "Faixa de renda", "disp_regional": "Dispersão regional (σ)"},
            title="Dispersão da diversificação entre regiões por faixa de renda"
        )
        st.plotly_chart(fig_disp, use_container_width=True)
    else:
        st.info("Sem variação regional suficiente por faixa de renda para estimar a dispersão.")

    with st.expander("Como ler / por que importa (isolamento)"):
        st.markdown(
            "- **Quanto menor a dispersão (σ)**, **menos** a região 'explica' a composição da carteira.\n"
            "- Em **alta renda**, a dispersão entre regiões tende a cair ⇒ **contexto local pesa menos** (isolamento da riqueza).\n"
            "- Implicação prática: estratégia comercial e educacional **por nível de renda** (contexto importa mais nas faixas baixas e médias)."
        )

    # ---------- 3.3 Observações metodológicas ----------
    st.subheader("Observações metodológicas")
    with st.expander("Resumo"):
        st.markdown(
            "- Os gráficos acima são **descritivos** com base em dados **pré-agregados** do app.\n"
            "- O uplift por faixa é uma **proxy observacional** do efeito marginal de complexidade; a dissertação usa especificações "
            "com interação e controles.\n"
            "- Para detalhes (modelos, robustez e limitações), consulte a **Dissertação** na aba “📜 Dissertação e Materiais”."
        )

    colA, colB, colC = st.columns(3)
    with colA:
        if st.button("Ir para 💡 Renda vs. Complexidade"):
            _switch_tab("💡 Renda vs. Complexidade")
    with colB:
        if st.button("Ir para 🌍 Geográfica"):
            _switch_tab("🌍 Análise Geográfica")
    with colC:
        if st.button("Ir para 📈 Temporal"):
            _switch_tab("📈 Análise Temporal")
