clear all	

* Importar base formato .Sas7bdat
import sas using "/Users/macvini/Library/CloudStorage/OneDrive-Pessoal/Mestrado/base_final_mestrado.sas7bdat"

* Converter formato da variável para mês, dia e ano
gen data_nascimento = mdy(1,1,1960) + DT_NASCIMENTO 
format DT_NASCIMENTO %td   

* Criar a variável idade a partir da data de nascimento convertida
gen idade = (td("`c(current_date)'") - data_nascimento) / 365.25
gen idade_int = floor(idade)

* Criar variável Investimentos Exterior unificando informações
egen investimento_exterior = rowtotal(INVEST_EXT_RENDA_VARIAVEL INVEST_NO_EXTERIOR INVEST_EXTERIOR INVEST_EXT_RENDA_FIXA)
order investimento_exterior, after(INVEST_ALTERNATIVOS)

* Recodificar a variável ID para código únicos
egen id_cliente = group(cliente)
drop if missing(cliente) | cliente == ""
order id_cliente, first

* Criar variável dummy para sexo
gen sexo_dummy = . 
replace sexo_dummy = 1 if SEXO == "M"
replace sexo_dummy = 0 if SEXO == "F"

* Criar variáveis dummy região cadastro 
gen regiao_norte = inlist(UF_CADASTRO, "AC", "AP", "AM", "PA", "RO", "RR", "TO")
gen regiao_nordeste = inlist(UF_CADASTRO, "AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE")
gen regiao_sudeste = inlist(UF_CADASTRO, "ES", "MG", "RJ", "SP")
gen regiao_sul = inlist(UF_CADASTRO, "PR", "RS", "SC")
gen regiao_centro_oeste = inlist(UF_CADASTRO, "DF", "GO", "MT", "MS")

* Criar variável Dummy carteira do relacionameto - se é ou não Estilo Investidor
gen estilo_investidor = NM_TIP_CTRA == "ESTILO INVESTIDOR"

* Criar variável Dummy Estado Civil - agrupado
gen ec_solteiro  = inlist(EST_CIVIL, 1)
gen ec_casado    = inlist(EST_CIVIL, 2, 3, 4, 8, 9, 11, 12)
gen ec_separado  = inlist(EST_CIVIL, 6, 7)
gen ec_viuvo     = EST_CIVIL == 5

* Criar variável Dummy Escolaridade - agrupada 
gen esc_baixa = inlist(ESCOLAR, 1, 2)
gen esc_media = inlist(ESCOLAR, 3, 4, 9)
gen esc_alta  = inlist(ESCOLAR, 5, 6, 7, 8)
gen esc_missing = ESCOLAR == 0

* Criar variável Dummy Perfil Investidor - tratado faltantes e agrupado com não respondidos
gen prfl_codigo = CD_PRFL_API
replace prfl_codigo = 5 if CD_PRFL_API == 0 | missing(CD_PRFL_API)
gen perfil_conservador = prfl_codigo == 1
gen perfil_moderado    = prfl_codigo == 2
gen perfil_arrojado    = prfl_codigo == 3
gen perfil_agressivo   = prfl_codigo == 4
gen perfil_nao_resp    = prfl_codigo == 5

* Criar variável Dummy e tratamento das ocupações
gen grupo_ocupacao = "Outros" // default

replace grupo_ocupacao = "Administração" if regexm(DS_OCUPACAO, "ADMINISTRADOR|CONTADOR|ANALISTA|CONSULTOR|ECONOMISTA")
replace grupo_ocupacao = "Servidor Público" if regexm(DS_OCUPACAO, "SERVIDOR PUBLICO|DEPUTADO|PREFEITO|SECRETARIO|MAGISTRADO|PROCURADOR")
replace grupo_ocupacao = "Saúde" if regexm(DS_OCUPACAO, "MEDICO|ENFERMEIRO|FISIOTERAPEUTA|ODONTOLOGO|FARMACEUTICO|NUTRICIONISTA|FONOAUDIOLOGO|PSICOLOGO|TERAPEUTA")
replace grupo_ocupacao = "Educação" if regexm(DS_OCUPACAO, "PROFESSOR|ESTUDANTE|ESTAGIARIO|BOLSISTA|PEDAGOGO")
replace grupo_ocupacao = "Autônomo/Comércio" if regexm(DS_OCUPACAO, "COMERCIANTE|AMBULANTE|TAXISTA|VENDEDOR|FEIRANTE|REPRESENTANTE COMERCIAL")
replace grupo_ocupacao = "Agropecuária" if regexm(DS_OCUPACAO, "AGRICULTOR|PECUARISTA|PESCADOR|AVICULTOR|RURAL|FLORICULTOR|AGRONOMO|AGROPECUARISTA")
replace grupo_ocupacao = "Industrial" if regexm(DS_OCUPACAO, "MECANICO|ELETRICISTA|OPERADOR|CONSTRUCAO|MARCENEIRO|INDUSTRIARIO|SERRALHEIRO|TECNIC")
replace grupo_ocupacao = "Justiça" if regexm(DS_OCUPACAO, "ADVOGADO|DELEGADO|DEFENSOR|PROMOTOR|JUIZ|OFICIAL DE JUSTICA|TABELIAO|CARTORIO")
replace grupo_ocupacao = "Segurança" if regexm(DS_OCUPACAO, "POLICIAL|MILITAR|VIGILANTE|SEGURANCA|BOMBEIRO")
replace grupo_ocupacao = "Cultura/Comunicação" if regexm(DS_OCUPACAO, "MUSICO|ATOR|ARTESAO|JORNALISTA|ESCULTOR|PUBLICITARIO|FOTOGRAFO|LOCUTOR")
replace grupo_ocupacao = "Outros" if missing(DS_OCUPACAO)

gen oc_administracao       = grupo_ocupacao == "Administração"
gen oc_servidor_publico    = grupo_ocupacao == "Servidor Público"
gen oc_saude               = grupo_ocupacao == "Saúde"
gen oc_educacao            = grupo_ocupacao == "Educação"
gen oc_autonomo_comercio   = grupo_ocupacao == "Autônomo/Comércio"
gen oc_agropecuaria        = grupo_ocupacao == "Agropecuária"
gen oc_industrial          = grupo_ocupacao == "Industrial"
gen oc_justica             = grupo_ocupacao == "Justiça"
gen oc_seguranca           = grupo_ocupacao == "Segurança"
gen oc_cultura_comunic     = grupo_ocupacao == "Cultura/Comunicação"
gen oc_outros              = grupo_ocupacao == "Outros"

* Excluir variáveis transformadas/tratadas 
drop DT_NASCIMENTO SEXO cliente idade UF_CADASTRO data_nascimento CARTEIRA CD_TIP_CTRA NM_TIP_CTRA EST_CIVIL ESCOLAR CD_PRFL_API TX_DCR_PRFL prfl_codigo GRUPO_OCUPACAO CD_NTZ_OCUPACAO DS_NTZ_OCUPACAO CD_OCUPACAO DS_OCUPACAO grupo_ocupacao INVEST_EXT_RENDA_VARIAVEL INVEST_NO_EXTERIOR INVEST_EXTERIOR INVEST_EXT_RENDA_FIXA

* Criar variável de escolaridade média da região
gen escolaridade_regiao = .

replace escolaridade_regiao = 9.2 if regiao_norte == 1
replace escolaridade_regiao = 8.3 if regiao_nordeste == 1
replace escolaridade_regiao = 10.0 if regiao_sudeste == 1
replace escolaridade_regiao = 10.1 if regiao_sul == 1
replace escolaridade_regiao = 10.1 if regiao_centro_oeste == 1

* Criar variável com a renda média regional (baseada nos trimestres de 2022, 2023 e 2024)
gen renda_regional = .

replace renda_regional = 2421.7 if regiao_norte == 1
replace renda_regional = 2078 if regiao_nordeste == 1
replace renda_regional = 3514 if regiao_sudeste == 1
replace renda_regional = 3423.7 if regiao_sul == 1
replace renda_regional = 3604 if regiao_centro_oeste == 1

* Criar variável com o IDH médio por região
gen idh_regional = .

replace idh_regional = 0.6847 if regiao_norte == 1
replace idh_regional = 0.6487 if regiao_nordeste == 1
replace idh_regional = 0.7537 if regiao_sudeste == 1
replace idh_regional = 0.7563 if regiao_sul == 1
replace idh_regional = 0.7533 if regiao_centro_oeste == 1

* Criar variável com o PIB per capita regional (valores de 2022 IBGE)
gen pib_percapita_regional = .

replace pib_percapita_regional = 33123 if regiao_norte == 1
replace pib_percapita_regional = 25401 if regiao_nordeste == 1
replace pib_percapita_regional = 63327 if regiao_sudeste == 1
replace pib_percapita_regional = 55942 if regiao_sul == 1
replace pib_percapita_regional = 65651 if regiao_centro_oeste == 1

// Início das Análises 

* Criar variável dependende

* Numerador: soma apenas dos produtos diversificação
egen soma_complex = rowtotal(MULTIMERCADOS RENDA_VARIAVEL INVEST_ALTERNATIVOS investimento_exterior)
* Denominador: soma de todo o portfólio (já feito anteriormente)
egen soma_total = rowtotal(RENDA_FIXA_POS_CDI RENDA_FIXA_PRE RENDA_FIXA_INFLACAO MULTIMERCADOS RENDA_VARIAVEL INVEST_ALTERNATIVOS investimento_exterior)
* Criar a variável de diversificação
gen diver = soma_complex / soma_total if soma_total > 0
* Se quiser substituir missing por zero:
replace diver = 0 if missing(diver)
label var diver "Diversificação"

* Criar Variável Complexidade Financeira 
* Cria a variável dummy (1 se houver alocação em qualquer produto complexo)
gen complex = soma_complex > 0
label var complex "Investidor aplica em produtos complexos"

* Verificar e eliminar duplicações no painel
duplicates tag id_cliente anomes, gen(flag_dup)
drop if flag_dup > 0
drop flag_dup

* Definir estrutura de dados em painel
xtset id_cliente anomes

* (0) Preservar ordem original
gen ordem_original = _n

* (1) Calcular variação da renda mensal por cliente
gen delta_y = .
sort id_cliente anomes
by id_cliente (anomes): replace delta_y = log(renda + 1) - log(renda[_n-1] + 1) if _n > 1 & !missing(renda) & !missing(renda[_n-1])

* (2) Criar identificador único por região
gen regiao_codigo = .
replace regiao_codigo = 1 if regiao_norte == 1
replace regiao_codigo = 2 if regiao_nordeste == 1
replace regiao_codigo = 3 if regiao_sudeste == 1
replace regiao_codigo = 4 if regiao_sul == 1
replace regiao_codigo = 5 if regiao_centro_oeste == 1

* (3) Calcular média anual da variação da renda por cliente
gen delta_y_anual = .
bysort id_cliente ano (anomes): egen media_anual_cliente = mean(delta_y)
replace delta_y_anual = media_anual_cliente
drop media_anual_cliente

* (4) Calcular média e desvio padrão da variação anual por região e ano
bysort regiao_codigo ano: egen media_dy = mean(delta_y_anual)
bysort regiao_codigo ano: egen sd_dy = sd(delta_y_anual)

* (5) Padronizar a variação anual
gen delta_y_pad = (delta_y_anual - media_dy) / sd_dy if sd_dy > 0

* (6) Calcular skew_aux
gen skew_aux = delta_y_pad^3 if !missing(delta_y_pad)

* (7) Calcular número de observações válidas
bysort regiao_codigo ano: egen grupo_n = count(skew_aux)

* (8) Calcular skew regional anual
bysort regiao_codigo ano: egen skew = mean(skew_aux)
replace skew = . if grupo_n < 30

* (9) Marcar se observação é válida
gen obs_valida_skew = grupo_n >= 30

* (10) Restaurar ordem original
sort ordem_original
drop ordem_original

* (11) Calcular skew_final apenas para anos após 2021
gen skew_final = skew if ano > 2021

* (12) Colapsar a skewness média por região (com dados válidos)
preserve
collapse (mean) skew_final, by(regiao_codigo)
rename skew_final skew_media_regional

* (13) Salvar temporariamente o resultado
tempfile skewmed
save `skewmed', replace
restore

* (14) Mesclar média regional de skew de volta na base original
merge m:1 regiao_codigo using `skewmed'

* (15) Criar variável proxy final com preenchimento da skew média onde faltava
gen skew_proxy = skew
replace skew_proxy = skew_media_regional if missing(skew_proxy)
label var skew_proxy "Proxy de skewness regional da renda (média regional)"

* (16) Limpar variáveis auxiliares
drop _merge
sort id_cliente anomes

* --------------------------------------------
* Normalização com log natural (LN)
* Aplicado apenas onde faz sentido — evitar distorções
* --------------------------------------------

* Variável dependente: diversificação (valor entre 0 e 1)
gen ln_diver = ln(diver + 0.01)  // Usar +0.01 pois diver pode ser 0, e é percentual (mais interpretável com esse ajuste)

* Variáveis com valores em R$ ou índices (sem zeros)
gen ln_renda = ln(renda)                     // Não precisa de +1 se não há zeros
gen ln_ESC   = ln(escolaridade_regiao)
gen ln_IDH   = ln(idh_regional)
gen ln_PIB   = ln(pib_percapita_regional)

* Verificação opcional:
* sum renda escolaridade_regiao idh_regional pib_percapita_regional if renda==0 | escolaridade_regiao==0 | idh_regional==0 | pib_percapita_regional==0

* --------------------------------------------
* Winsorização para controlar outliers extremos
* --------------------------------------------

drop if missing(ln_diver, ln_renda, ln_ESC, ln_IDH, ln_PIB)
ssc install winsor2, replace
winsor2 ln_diver ln_renda ln_ESC ln_IDH ln_PIB, suffix(_w) cuts(1 99)

* --------------------------------------------
* Matriz de Correlação (testar multicolinearidade entre preditoras)
* --------------------------------------------
pwcorr ln_diver_w ln_renda_w ln_ESC_w ln_IDH_w ln_PIB_w idade_int sexo_dummy skew_proxy, star(0.10)

* --------------------------------------------
* Modelos com Pooled, FE e RE
* --------------------------------------------

* Modelo Pooled (dados empilhados)
* teste retirando ln_ESC_w
reg ln_diver_w ln_renda_w ln_IDH_w sexo_dummy idade_int
vif
hettest
estimates store r1, title(Pooled)

* Modelo de Efeitos Fixos
* teste retirando ln_ESC_w
xtreg ln_diver_w ln_renda_w ln_IDH_w sexo_dummy idade_int, fe
estimates store r2, title(Efeito Fixo)

* Modelo de Efeitos Aleatórios
* teste retirando ln_ESC_w
xtreg ln_diver_w ln_renda_w ln_IDH_w sexo_dummy idade_int, re
estimates store r3, title(Efeito Aleatório)

* Teste de heterocedasticidade e Hausman
xttest0
hausman r2 r3

* --------------------------------------------
* Regressões para Hipóteses
* --------------------------------------------

* H1 e H1a — Efeito da complexidade e contexto regional
xtreg ln_diver_w complex ln_ESC_w ln_renda_w regiao_norte regiao_nordeste regiao_sul regiao_centro_oeste sexo_dummy idade_int, fe robust
estimates store h1, title(H1-H1a)

* H2 — Efeito do risco cíclico de renda (skew_proxy = com valores completados)
xtreg ln_diver_w skew_proxy ln_ESC_w ln_renda_w regiao_norte regiao_nordeste regiao_sul regiao_centro_oeste sexo_dummy idade_int, fe robust
estimates store h2, title(H2)

* H3 — Efeito do IDH em portfólios de alta renda
gen renda_alta = renda > 20000
xtreg ln_diver_w ln_IDH_w ln_renda_w ln_ESC_w regiao_norte regiao_nordeste regiao_sul regiao_centro_oeste sexo_dummy idade_int if renda_alta==1, fe robust
estimates store h3, title(H3)

* --------------------------------------------
* Comparação dos Modelos — Tabela Final
* --------------------------------------------
ssc install estout, replace

estout h1 h2 h3, cells(b(star fmt(3)) se(par fmt(2))) ///
 legend label varlabels(_cons Constant) ///
 stats(r2 df_r N, fmt(3 0 1 0) label(R-sqr dfres)) ///
 starlevels(* 0.1 ** 0.05 *** 0.01)

* --------------------------------------------
* Estatísticas Descritivas
* --------------------------------------------
summarize

* ================================
* BLOCO FINAL — Análises Avançadas
* ================================

* 1. Robustez: Rodar modelos separando ln_ESC_w e ln_IDH_w
xtreg ln_diver_w ln_renda_w ln_ESC_w sexo_dummy idade_int, fe robust
estimates store esc_only, title(Modelo ESC only)

xtreg ln_diver_w ln_renda_w ln_IDH_w sexo_dummy idade_int, fe robust
estimates store idh_only, title(Modelo IDH only)

* 2. Criar variável de interação: complexidade x renda
gen complex_renda = complex * ln_renda_w

* 3. Rodar modelo com termo de interação
xtreg ln_diver_w complex ln_renda_w ln_ESC_w complex_renda sexo_dummy idade_int, fe robust
estimates store interacao, title(Modelo com Interação)

* 4. Rodar modelo com perfil de investidor (se disponível)
xtreg ln_diver_w complex ln_ESC_w ln_renda_w ///
    perfil_conservador perfil_moderado perfil_arrojado ///
    sexo_dummy idade_int, fe robust
estimates store perfil, title(Modelo com Perfil)

* 5. Comparação dos modelos
estout esc_only idh_only interacao perfil, ///
    cells(b(star fmt(3)) se(par fmt(2))) ///
    legend label varlabels(_cons Constant) ///
    stats(r2 df_r N, fmt(3 0 1 0) label(R-sqr dfres)) ///
    starlevels(* 0.1 ** 0.05 *** 0.01)

* 6. Estatísticas descritivas atualizadas
summarize diver ln_diver_w ln_renda_w ln_ESC_w ln_IDH_w idade_int sexo_dummy complex skew_proxy perfil_conservador perfil_moderado perfil_arrojado

* ===============================================
* TESTES DE ROBUSTEZ — Inclusão de variáveis não utilizadas
* ===============================================

* 1. Modelo com dummies de perfil completo (incluindo não respondidos e agressivo)
xtreg ln_diver_w complex ln_ESC_w ln_renda_w ///
    perfil_conservador perfil_moderado perfil_arrojado perfil_agressivo perfil_nao_resp ///
    sexo_dummy idade_int, fe robust
estimates store perfil_completo, title(Perfil Completo)

* 2. Modelo com variável de estilo do investidor
xtreg ln_diver_w complex ln_ESC_w ln_renda_w ///
    estilo_investidor sexo_dummy idade_int, fe robust
estimates store estilo_inv, title(Estilo Investidor)

* 3. Modelo com estado civil (solteiro como referência)
xtreg ln_diver_w complex ln_ESC_w ln_renda_w ///
    ec_casado ec_separado ec_viuvo sexo_dummy idade_int, fe robust
estimates store estado_civil, title(Estado Civil)

* 4. Modelo com ocupação (grupo Outros como referência)
xtreg ln_diver_w complex ln_ESC_w ln_renda_w ///
    oc_administracao oc_servidor_publico oc_saude oc_educacao oc_autonomo_comercio ///
    oc_agropecuaria oc_industrial oc_justica oc_seguranca oc_cultura_comunic ///
    sexo_dummy idade_int, fe robust
estimates store ocupacao, title(Ocupação)

* 5. Modelo incluindo PIB regional per capita (log)
xtreg ln_diver_w complex ln_ESC_w ln_PIB_w ln_renda_w sexo_dummy idade_int, fe robust
estimates store pib_model, title(Com PIB Regional)

* ===============================================
* COMPARAÇÃO DOS MODELOS ALTERNATIVOS
* ===============================================

estout perfil_completo estilo_inv estado_civil ocupacao pib_model, ///
    cells(b(star fmt(3)) se(par fmt(2))) ///
    legend label varlabels(_cons Constant) ///
    stats(r2 df_r N, fmt(3 0 1 0) label(R-sqr dfres)) ///
    starlevels(* 0.1 ** 0.05 *** 0.01)



