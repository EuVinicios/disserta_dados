# Decisões Sob Risco em Mercados Emergentes: Análise de Dados da Dissertação

[cite_start]Este repositório contém os códigos e materiais de análise de dados utilizados na dissertação "Decisões Sob Risco em Mercados Emergentes: evidências quantitativas sobre o comportamento do investidor brasileiro"[cite: 1265], apresentada ao Programa de Pós-Graduação em Ciências Contábeis da Fucape Business School.

## 📄 Sobre o Projeto

O objetivo deste projeto é fornecer uma replicação completa do processo de análise de dados da dissertação, desde o tratamento inicial dos dados até a estimação dos modelos econométricos e a geração dos resultados finais. [cite_start]A análise foi originalmente realizada em Stata e posteriormente migrada para Python, utilizando um ambiente de dados em painel para investigar os determinantes da diversificação de portfólio entre investidores brasileiros[cite: 1601, 1296].

As principais bibliotecas Python utilizadas são:
* **Pandas:** para manipulação e tratamento dos dados.
* **linearmodels:** para a estimação de modelos de regressão com dados em painel (Efeitos Fixos e Aleatórios).
* **statsmodels:** para análises estatísticas complementares.
* **Matplotlib / Seaborn:** para a visualização de dados.

## 🗂️ Estrutura do Repositório

* `dados.ipynb`: Notebook Jupyter contendo todo o fluxo de análise em Python, desde a importação, tratamento, engenharia de variáveis, até a estimação dos modelos e geração de outputs.
* `requirements.txt`: Lista de todas as dependências Python necessárias para executar o projeto.
* `bootstrap_deps.py`: Script auxiliar para garantir que as dependências estejam instaladas no ambiente.
* `gerar_dados_sinteticos.py`: Script Python para gerar uma base de dados sintética para fins de teste e estudo (veja a seção de Dados abaixo).
* `/resultados_python/`: Pasta onde todos os outputs da análise (tabelas de regressão, gráficos, etc.) são salvos.

## 💾 Sobre os Dados

### Dados Originais

[cite_start]A pesquisa original utilizou uma base de dados de uma grande instituição financeira brasileira, abrangendo o período de 2021 a 2024[cite: 1295, 1345, 1476]. A base contém informações sensíveis sobre o portfólio e características demográficas de investidores individuais.

**Em conformidade com a Lei Geral de Proteção de Dados (LGPD) e os termos de confidencialidade firmados para a realização da pesquisa, a base de dados original, mesmo que anonimizada, não pode ser disponibilizada publicamente.**

### Dados Sintéticos para Estudo

Para permitir que outros pesquisadores, estudantes e entusiastas possam executar o notebook de análise e estudar os procedimentos metodológicos, foi criado o script `gerar_dados_sinteticos.py`.

Este script gera um arquivo `dados_sinteticos.csv` que **imita a estrutura** (colunas e tipos de dados) da base original, mas com dados gerados de forma **completamente aleatória**.

**Atenção:** Qualquer resultado, coeficiente ou p-valor gerado a partir desta base sintética **não é real** e não corresponde aos achados da dissertação. O propósito desses dados é exclusivamente educacional, para permitir a execução do código sem erros.

## 🚀 Como Executar o Projeto

Siga os passos abaixo para replicar a análise com os dados sintéticos:

1.  **Clone o Repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
    cd seu-repositorio
    ```

2.  **Crie e Ative um Ambiente Virtual:**
    ```bash
    # Criar o ambiente
    python3 -m venv .venv

    # Ativar no macOS/Linux
    source .venv/bin/activate

    # Ativar no Windows (PowerShell)
    .venv\Scripts\Activate.ps1
    ```

3.  **Instale as Dependências:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Gere os Dados Sintéticos:**
    ```bash
    python gerar_dados_sinteticos.py
    ```
    Isso criará o arquivo `dados_sinteticos.csv` na pasta do projeto.

5.  **Execute a Análise:**
    * Abra o arquivo `dados.ipynb` no VSCode ou Jupyter.
    * Localize a célula de **Configuração** no início do notebook.
    * Altere a variável `INPUT_PATH` para apontar para os dados sintéticos:
        ```python
        INPUT_PATH = "./dados_sinteticos.csv"
        ```
    * Execute todas as células do notebook.

## 🎓 Citação

Se você utilizar o código ou a metodologia deste projeto em sua pesquisa, por favor, cite a dissertação original:

SILVEIRA, V. (2025). *Decisões Sob Risco em Mercados Emergentes: evidências quantitativas sobre o comportamento do investidor brasileiro*. Dissertação de Mestrado, Fucape Pesquisa e Ensino S/A, Rio de Janeiro, RJ, Brasil.
