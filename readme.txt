Perfeitamente! Vou montar um manual de operação completo e organizado, focado no uso prático do dia a dia. Como o sistema já tem todas as funcionalidades implementadas, ele serve tanto para treinar novos operadores quanto para documentar o fluxo para a equipe.

Abaixo está o manual pronto para você copiar e formatar (Word, PDF ou impressão). 

---

# MANUAL DE OPERAÇÃO DO SISTEMA Docksync
### Sistema de Gestão Portuária de Cargas RoRo

---

## 1. ACESSO AO SISTEMA

1. **Abra o navegador** e acesse o endereço do sistema (ex: `http://localhost:8000`).
2. Na tela de login, informe seu **Usuário** e **Senha**.
3. Resolva o **desafio matemático** exibido na tela (ex: `5 + 3 = ?`). Digite o resultado no campo indicado.
4. Clique em **"Entrar"**.
5. Caso tenha esquecido a senha, entre em contato com o administrador do sistema.

---

## 2. DASHBOARD GERENCIAL
*Após o login, esta é a tela inicial.*

- **Visão Geral**: Exibe os principais indicadores do porto.
- **Cards Superiores**:
  - **Saídas (7 dias)**: Total de veículos que saíram do porto no período.
  - **Tempo de Armazenagem**: Tempo médio que os veículos permanecem no pátio.
  - **Navios Atracados**: Quantidade de navios em operação no momento.
  - **Veículos Armazenados**: Total de veículos atualmente no pátio.
- **Gráficos**:
  - **Movimentações**: Gráfico de linha com entradas e saídas por dia.
  - **Distribuição por Operador**: Gráfico de rosca (pizza) mostrando a participação de cada operadora.
  - **Top 5 Operadores**: Gráfico de barras com os operadores com mais veículos.
- **Últimas Movimentações**: Tabela com os 10 registros mais recentes.

**Como usar**: No canto superior direito, você pode selecionar o período (7, 15, 30 ou 90 dias) e clicar em **"Aplicar"** para filtrar os dados.

---

## 3. GESTÃO DE PÁTIO
*Menu: "Gestão de Pátio"*

Esta tela mostra a situação **atual** do pátio principal (Pátio Modelo).

- **Informações do Pátio**: Código, Quantidade de Carros, Prazo Excedido, Metragem Ocupada e Metragem Total.
- **Botão "Ver Subpátios"**: Acessa a visão detalhada dos 12 subpátios (P1 ao P12).

### 3.1 Subpátios
*Clique em "Ver Subpátios"*

- Exibe cards individuais para cada subpátio, organizados em grade (refletindo a disposição física).
- **Cada card mostra**:
  - Nome (P1, P2, etc.);
  - Quantidade de carros;
  - Área ocupada (m²);
  - Percentual de ocupação (com barra de progresso colorida);
  - Botão **"Ver Detalhes"**.

---

## 4. BUSCA DE VEÍCULO (POR CHASSI)
*Menu: "Buscar Veículo"*

- Digite o **chassi completo** do veículo no campo de busca.
- Clique em **"Buscar"**.
- O sistema exibirá um cartão com:
  - **Localização Atual**: Setor, localização aproximada e latitude/longitude.
  - **Mapa**: Exibe a posição no mapa (se GPS disponível).
  - **Identificação**: Navio, Nº Programação, BL, Operador, Fiel Depositário, Previsões de Chegada e Saída.
  - **Histórico**: Lista todas as movimentações (Chegada, Interna, Saída) com data/hora e operador responsável.

---

## 5. REGISTRAR MOVIMENTAÇÃO
*Menu: "Movimentação"*

Esta é a tela mais utilizada pelos operadores em campo. 

**Passo a passo:**
1. **Tipo da Movimentação**: Selecione:
   - **Chegada**: Entrada do veículo no porto.
   - **Interna**: Mudança de um setor para outro dentro do porto.
   - **Saída**: Retirada do veículo do porto.
2. **Busca Rápida (Opcional)**: Digite o chassi e clique em **"Buscar"** para preencher automaticamente os campos de Navio, Programação, BL e Veículo.
3. **Seleções em Cascata**:
   - **1. Navio**: Selecione o navio.
   - **2. Nº Programação**: Selecione a viagem.
   - **3. BL**: Selecione o conhecimento de embarque.
   - **4. Veículo (Chassi)**: Selecione o veículo.
4. **Setor de Destino**: Selecione o setor para onde o veículo vai (obrigatório para Chegada e Interna).
5. **Localização do Veículo (GPS)**: Clique em **"Capturar GPS"** para obter a coordenada do aparelho (preenche automaticamente).
6. **Trabalhador Portuário**: Selecione o responsável pela movimentação.
7. **Foto do Chassi (Opcional)**: Anexe uma foto (no celular, abre a câmera).
8. Clique em **"Registrar Movimentação"**.

**Atenção**: Se o tipo for **"Saída"**, o campo "Setor de Destino" será ocultado e a localização da carga será limpa automaticamente.

---

## 6. GESTÃO DE CARGAS
*Menu: "Gestão" > "Cargas"*

- Lista todas as cargas cadastradas com paginação (30 por página).
- **Filtros**: Utilize os campos no topo para filtrar por Chassi, BL, Operador ou Setor.
- **Ordenação**: Clique nos cabeçalhos da tabela (Chassi, BL, etc.) para ordenar.
- **Ações**: Clique em **"Ver"** para acessar a ficha completa do veículo.

### 6.1 Adicionar Nova Carga
- Clique em **"+ Adicionar Carga"**.
- Preencha os dados do veículo (BL, Chassi, Manifesto, Operador, Fiel, Modelo). A metragem é calculada automaticamente ao selecionar o modelo.

---

## 7. GESTÃO DE NAVIOS E TRÂNSITOS
*Menu: "Gestão" > "Navios" ou "Trânsito de Carga"*

### 7.1 Navios
- Cadastra a frota (Nome, IMO, MMSI).

### 7.2 Trânsito de Carga (Viagens)
- Lista todas as viagens programadas.
- **Importar Lineup**: Envie um arquivo Excel com o lineup do porto para cadastrar várias viagens de uma vez.
- **Adicionar Trânsito**: Cadastre manualmente uma viagem (Navio, Nº Programação, PSP, Datas ETA/ETB/ETS, Berço, Operador, Status).

---

## 8. GESTÃO DE MANIFESTOS
*Menu: "Gestão" > "Manifestos"*

- Lista os manifestos com BL, Navio, Operador, Fiel, nº de veículos e status.
- **Adicionar Manifesto**: 
  1. Informe a Viagem, Operador e Fiel Depositário.
  2. Preencha os itens do manifesto (BL, Modelo, Quantidade e Chassis). 
  3. Os campos "Nº Veículos" e "Metragem Total" são calculados automaticamente.
  4. Clique em **"Salvar Manifesto"**. As cargas são geradas automaticamente a partir dos chassis informados.

---

## 9. CADASTROS AUXILIARES
*Menu: "Cadastro" (Acesso restrito ao Administrador)*

- **Usuários**: Gerenciar contas e permissões (Administrador, Gestor, Operador).
- **Operadores Portuários**: Cadastro de empresas operadoras (importação via Excel disponível).
- **Fiel Depositário**: Cadastro de entidades responsáveis pela carga.
- **Pátios**: Cadastro de setores e subpátios.
- **Modelos de Veículos**: Cadastro de fabricantes, modelos, ano e dimensões.
- **Trabalhadores Portuários**: Cadastro dos operadores de campo (matrícula).

---

## 10. RELATÓRIOS
*Menu: "Relatórios"*

- **Exportação para Excel**: Gere planilhas de Movimentações, Manifestos ou Cargas, filtrando por período.
- **Relatório de Ocupação do Pátio (PDF)**: Relatório com a ocupação atual do pátio e subpátios.
- **Relatório de Saídas (PDF)**: Auditoria de veículos que saíram no período.
- **Ocupação por Operador (PDF)**: Metragem ocupada por cada operadora.
- **Ranking de Modelos (PDF)**: Modelos de veículos mais frequentes.
- **Prazos Excedentes (PDF)**: Lista de veículos que passaram da data prevista de saída (alerta urgente).

---

## 11. DICAS IMPORTANTES
- **Foto sempre que possível**: A foto do chassi é uma evidência importante, mas não é obrigatória.
- **GPS**: Se estiver no pátio, capture o GPS para melhorar o rastreamento.
- **Nunca edite uma movimentação**: O histórico é imutável. Se cometeu um erro, registre uma nova movimentação corretiva.
- **Chassi é a chave**: Sempre confirme o chassi antes de registrar qualquer movimentação.

---

*Este manual está alinhado com a versão atual do sistema. Em caso de dúvidas, entre em contato com o suporte técnico.*