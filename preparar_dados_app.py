# preparar_dados_app.py (Versão final e robusta)

import pandas as pd
import numpy as np
import os
from pathlib import Path # <--- MUDANÇA: Importa a biblioteca Path

# --- CONFIGURAÇÃO ---
# ATENÇÃO: O caminho agora aponta para o arquivo .dta que você converteu no Stata
CAMINHO_DADOS_CONVERTIDOS = "/Users/macvini/Library/CloudStorage/OneDrive-Pessoal/Mestrado/base_final_mestrado_convertida.dta"

# --- MUDANÇA: Define os caminhos de forma robusta, relativa à localização deste script ---
DIRETORIO_ATUAL = Path(__file__).parent
PASTA_SAIDA_APP = DIRETORIO_ATUAL / "app_data"

# Garante que a pasta de saída exista
os.makedirs(PASTA_SAIDA_APP, exist_ok=True)


def tratar_dados(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica todo o tratamento e engenharia de variáveis da dissertação."""
    print("Iniciando tratamento e engenharia de variáveis...")
    
    df = df.dropna(subset=['cliente'])
    df = df[df['cliente'] != '']
    df['id_cliente'] = df.groupby('cliente').ngroup()

    df['DT_NASCIMENTO'] = pd.to_datetime(df['DT_NASCIMENTO'])
    df['idade_int'] = (pd.to_datetime('2025-01-01') - df['DT_NASCIMENTO']).dt.days / 365.25
    df['idade_int'] = df['idade_int'].astype(int)

    colunas_invest_ext = ['INVEST_EXT_RENDA_VARIAVEL', 'INVEST_NO_EXTERIOR', 'INVEST_EXTERIOR', 'INVEST_EXT_RENDA_FIXA']
    df['investimento_exterior'] = df[colunas_invest_ext].sum(axis=1, skipna=True)

    regioes = {
        'Norte': ["AC", "AP", "AM", "PA", "RO", "RR", "TO"],
        'Nordeste': ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
        'Sudeste': ["ES", "MG", "RJ", "SP"],
        'Sul': ["PR", "RS", "SC"],
        'Centro-Oeste': ["DF", "GO", "MT", "MS"],
    }
    conditions = [df['UF_CADASTRO'].isin(ufs) for ufs in regioes.values()]
    df['regiao'] = np.select(conditions, list(regioes.keys()), default='Não Identificada')

    soma_complex_cols = ['MULTIMERCADOS', 'RENDA_VARIAVEL', 'INVEST_ALTERNATIVOS', 'investimento_exterior']
    soma_total_cols   = ['RENDA_FIXA_POS_CDI', 'RENDA_FIXA_PRE', 'RENDA_FIXA_INFLACAO'] + soma_complex_cols
    df['soma_complex'] = df[soma_complex_cols].sum(axis=1, skipna=True)
    df['soma_total']   = df[soma_total_cols].sum(axis=1, skipna=True)
    df['diver'] = (df['soma_complex'] / df['soma_total']).replace([np.inf, -np.inf], 0).fillna(0).clip(upper=1.0)
    df['complex'] = (df['soma_complex'] > 0).astype(int)
    
    df['faixa_renda'] = pd.cut(df['renda'], bins=[0, 20000, np.inf], labels=['Até 20k', 'Acima de 20k'], right=False)
    
    df['anomes'] = pd.to_datetime(df['anomes'].astype(int).astype(str), format='%Y%m')
    df['ano'] = df['anomes'].dt.year

    print("Tratamento concluído.")
    return df

def main():
    """Função principal que orquestra o carregamento, tratamento e agregação dos dados."""
    print("--- INICIANDO SCRIPT DE PRÉ-PROCESSAMENTO LOCAL ---")
    try:
        df = pd.read_stata(CAMINHO_DADOS_CONVERTIDOS)
        print(f"Base de dados convertida (.dta) carregada com sucesso. {len(df)} linhas.")
    except Exception as e:
        print(f"ERRO: Não foi possível ler o arquivo de dados convertido em '{CAMINHO_DADOS_CONVERTIDOS}'.")
        print("Verifique se você executou a conversão no Stata primeiro.")
        print(f"Detalhe do erro: {e}")
        return

    df_tratado = tratar_dados(df)

    print("Iniciando cálculo e salvamento dos arquivos agregados...")

    # --- MUDANÇA: A forma de salvar os arquivos foi atualizada ---
    # Padrão antigo: os.path.join(PASTA_SAIDA_APP, 'nome.csv')
    # Padrão novo: PASTA_SAIDA_APP / 'nome.csv'

    # 1. Agregado para filtros principais (KPIs)
    agg_filtros = df_tratado.groupby(['regiao', 'faixa_renda']).agg(
        diversificacao_media=('diver', 'mean'),
        renda_media=('renda', 'mean'),
        idade_media=('idade_int', 'mean'),
        proporcao_complex=('complex', 'mean'),
        total_clientes=('id_cliente', 'nunique')
    ).reset_index()
    agg_filtros.to_csv(PASTA_SAIDA_APP / 'dados_agregados_filtros.csv', index=False)
    print(f"-> Salvo: {PASTA_SAIDA_APP / 'dados_agregados_filtros.csv'}")

    # 2. Agregado para o mapa por UF
    agg_mapa = df_tratado.groupby('UF_CADASTRO').agg(
        diversificacao_media=('diver', 'mean'),
        renda_media=('renda', 'mean')
    ).reset_index()
    agg_mapa.to_csv(PASTA_SAIDA_APP / 'dados_mapa_uf.csv', index=False)
    print(f"-> Salvo: {PASTA_SAIDA_APP / 'dados_mapa_uf.csv'}")

    # 3. Agregado para o gráfico de distribuição
    dist_diver = df_tratado['diver'].value_counts(bins=50, normalize=True).sort_index().reset_index()
    dist_diver.columns = ['faixa_diversificacao', 'percentual']
    dist_diver['faixa_diversificacao'] = dist_diver['faixa_diversificacao'].astype(str)
    dist_diver.to_csv(PASTA_SAIDA_APP / 'distribuicao_diversificacao.csv', index=False)
    print(f"-> Salvo: {PASTA_SAIDA_APP / 'distribuicao_diversificacao.csv'}")

    # 4. Agregado para a evolução temporal
    agg_temporal = df_tratado.groupby(['anomes', 'regiao'])['diver'].mean().reset_index()
    agg_temporal.to_csv(PASTA_SAIDA_APP / 'evolucao_temporal_regional.csv', index=False)
    print(f"-> Salvo: {PASTA_SAIDA_APP / 'evolucao_temporal_regional.csv'}")
    
    print("\n--- SCRIPT CONCLUÍDO COM SUCESSO! ---")

if __name__ == '__main__':
    main()