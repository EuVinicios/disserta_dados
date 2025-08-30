# -*- coding: utf-8 -*-
"""
gerar_dados_sinteticos.py
-------------------------
Este script gera uma base de dados sintética (falsa) que imita a estrutura
da base de dados original da dissertação.

O objetivo é permitir que o notebook de análise 'dados.ipynb' seja executado
sem erros, para fins educacionais e de estudo dos procedimentos.

ATENÇÃO: Os dados aqui gerados são aleatórios. Qualquer resultado ou conclusão
derivado deles não será real nem corresponderá aos achados da pesquisa.
"""

import pandas as pd
import numpy as np
import os

# --- Parâmetros da Simulação ---
NUM_CLIENTES = 500      # Número de clientes fictícios
DATA_INICIO = '2021-01-01'
DATA_FIM = '2024-12-31'
ARQUIVO_SAIDA = 'dados_sinteticos.csv'

print("Iniciando a geração de dados sintéticos...")

# --- Gerando a estrutura do painel (clientes x tempo) ---
# Criando IDs de clientes únicos
ids_clientes = [f'cliente_{i+1:05d}' for i in range(NUM_CLIENTES)]
# Criando o intervalo de tempo mensal
datas = pd.to_datetime(pd.date_range(start=DATA_INICIO, end=DATA_FIM, freq='MS'))
# Criando o DataFrame com todas as combinações
df = pd.DataFrame(
    index=pd.MultiIndex.from_product([ids_clientes, datas], names=['cliente', 'anomes_dt'])
).reset_index()

print(f"Estrutura do painel criada com {len(df)} observações.")

# --- Gerando características fixas por cliente ---
# Dicionário para armazenar características fixas de cada cliente
clientes_df = pd.DataFrame(index=ids_clientes)

# Demográficos
clientes_df['SEXO'] = np.random.choice(['M', 'F'], size=NUM_CLIENTES, p=[0.61, 0.39])
clientes_df['DT_NASCIMENTO'] = (
    pd.to_datetime('1960-01-01') + pd.to_timedelta(np.random.randint(5000, 25000), unit='D')
)
ufs = ["AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]
clientes_df['UF_CADASTRO'] = np.random.choice(ufs, size=NUM_CLIENTES)

# Outros atributos categóricos
clientes_df['EST_CIVIL'] = np.random.randint(1, 13, size=NUM_CLIENTES)
clientes_df['ESCOLAR'] = np.random.randint(0, 10, size=NUM_CLIENTES)
clientes_df['CD_PRFL_API'] = np.random.randint(0, 5, size=NUM_CLIENTES)
ocupacoes = ["ADMINISTRADOR", "MEDICO", "ADVOGADO", "PROFESSOR", "SERVIDOR PUBLICO", "ESTUDANTE", "COMERCIANTE", "ENGENHEIRO", "OUTROS"]
clientes_df['DS_OCUPACAO'] = np.random.choice(ocupacoes, size=NUM_CLIENTES, p=[0.1, 0.1, 0.1, 0.1, 0.2, 0.1, 0.1, 0.1, 0.1])
clientes_df['NM_TIP_CTRA'] = np.random.choice(["ESTILO INVESTIDOR", "CARTEIRA PADRAO"], size=NUM_CLIENTES, p=[0.7, 0.3])


# Juntando as características fixas ao painel principal
df = pd.merge(df, clientes_df, left_on='cliente', right_index=True)

print("Características demográficas e fixas geradas.")

# --- Gerando variáveis financeiras (variam no tempo) ---
df['anomes'] = df['anomes_dt'].dt.strftime('%Y%m')

# Gerando valores de portfólio com distribuição log-normal (mais realista)
portfolio_cols = [
    'RENDA_FIXA_POS_CDI', 'RENDA_FIXA_PRE', 'RENDA_FIXA_INFLACAO',
    'MULTIMERCADOS', 'RENDA_VARIAVEL', 'INVEST_ALTERNATIVOS',
    'INVEST_EXT_RENDA_VARIAVEL', 'INVEST_NO_EXTERIOR',
    'INVEST_EXTERIOR', 'INVEST_EXT_RENDA_FIXA'
]
for col in portfolio_cols:
    df[col] = np.random.lognormal(mean=10, sigma=2.5, size=len(df)) * np.random.choice([0,1], size=len(df), p=[0.4, 0.6])

# Gerando renda mensal
df['renda'] = np.random.lognormal(mean=10.5, sigma=1.0, size=len(df)) + 1000

# Limpando colunas desnecessárias
df = df.drop(columns=['anomes_dt'])

print("Variáveis financeiras geradas.")

# --- Salvando o arquivo ---
df.to_csv(ARQUIVO_SAIDA, index=False)

print("-" * 50)
print(f"✅ Base de dados sintética salva com sucesso em '{os.path.abspath(ARQUIVO_SAIDA)}'")
print(f"Colunas geradas: {df.columns.tolist()}")
print("\nLembre-se de atualizar a variável 'INPUT_PATH' no seu notebook 'dados.ipynb'.")