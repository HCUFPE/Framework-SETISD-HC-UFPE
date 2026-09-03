# Arquitetura do Projeto

Este documento detalha a arquitetura em camadas e os padrões de projeto utilizados no framework, com foco em desacoplamento e flexibilidade.

## Arquitetura em Camadas

O fluxo de uma requisição na aplicação segue um padrão claro e unidirecional, garantindo a separação de responsabilidades.

**Fluxo: `Roteador` -> `Controller` -> `Provedor`**

1.  **Roteador (`src/routers/`)**
    - **Responsabilidade:** Define os endpoints da API (`@router.get`, `@router.post`, etc.), valida os dados de entrada (usando Pydantic) e gerencia a injeção de dependências.
    - **Função:** É o ponto de entrada de uma requisição HTTP. Ele utiliza o sistema `Depends` do FastAPI para solicitar as dependências necessárias (como um provedor de dados) e, em seguida, chama a função apropriada no controller, passando a dependência já resolvida.

2.  **Controller (`src/controllers/`)**
    - **Responsabilidade:** Contém a lógica de negócio. Ele orquestra as operações, formata dados e toma decisões.
    - **Função:** Recebe as dependências já prontas do roteador. Ele não sabe (e não deve saber) qual implementação concreta está sendo usada (ex: se os dados vêm de um banco ou de um CSV). Ele apenas utiliza os métodos definidos pela interface do provedor.

3.  **Provedor (`src/providers/`)**
    - **Responsabilidade:** Camada de acesso a dados. É a única parte do sistema que sabe como obter ou persistir dados em uma fonte específica (PostgreSQL AGHU, SQLite Local, CSV, Oracle, etc.).
    - **Função:** Implementa uma interface (contrato) definida em `src/providers/interfaces/`. Cada implementação concreta (ex: `PacientePostgresProvider`, `PacienteCsvProvider`) contém a lógica específica para uma fonte de dados.

## Estratégia de Bancos de Dados

O framework trabalha com três papéis claros para armazenamento de dados:

1. **Banco Interno da Aplicação (SQLite `APP_DB_URL`):**
   - Banco de dados padrão da aplicação para salvar estados locais, sessões e tabelas nativas do novo sistema.
2. **Banco Corporativo do Hospital (PostgreSQL `POSTGRES_DSN`):**
   - Banco oficial de produção para **consultar dados do AGHU** (leitos, prontuários, faturamento).
3. **Provedor de Desenvolvimento Offline (CSV `data/pacientes.csv`):**
   - Provedor secundário ativado em desenvolvimento local sem acesso à rede do hospital.

## Padrão de Provedor com Seleção de Estratégia

A principal característica arquitetural do framework é a capacidade de trocar a fonte de dados de um domínio de forma limpa e explícita.

### Como Funciona

1.  **Interfaces (`src/providers/interfaces/`)**: Para cada domínio (ex: `paciente`), existe um "contrato" (`PacienteProviderInterface`) que define os métodos que devem estar disponíveis (ex: `listar_pacientes`).

2.  **Implementações (`src/providers/implementations/`)**: Para cada interface, podem existir várias implementações concretas. Por exemplo, `PacientePostgresProvider` e `PacienteCsvProvider` ambas implementam `PacienteProviderInterface`.

3.  **Fábrica de Dependências (`src/dependencies.py`)**: Este arquivo contém uma função fábrica (ex: `get_paciente_provider`) que recebe uma string de "estratégia" (`'postgres'` ou `'csv'`). Com base nessa string, a fábrica retorna a **função de dependência correta** que o FastAPI deve usar para criar o provedor. Isso garante que a conexão com o banco de dados só seja tentada se a estratégia `'postgres'` for selecionada.

4.  **Configuração no Roteador (`src/routers/`)**: O arquivo do roteador é o local onde a estratégia é definida.

    ```python
    # Em src/routers/paciente.py

    # --- PONTO ÚNICO DE CONFIGURAÇÃO PARA ESTE ROTEADOR ---
    # Para usar o banco de dados em produção, altere esta linha para "postgres"
    STRATEGY = "csv"
    # ----------------------------------------------------

    @router.get("", ...)
    async def listar_pacientes(
        # A fábrica é chamada com a estratégia, e o FastAPI injeta o provedor correto.
        provider: PacienteProviderInterface = Depends(get_paciente_provider(STRATEGY))
    ):
        return await paciente_controller.listar_pacientes(provider)
    ```

### Vantagens desta Abordagem

- **Flexibilidade:** Permite usar fontes de dados diferentes em ambientes diferentes (ex: CSV em desenvolvimento, Postgres em produção).
- **Desacoplamento Real:** A lógica de negócio no controller nunca é afetada pela fonte de dados.
- **Clareza:** Fica explícito no roteador qual fonte de dados está sendo utilizada para aquele domínio.
- **Eficiência:** Recursos como pools de conexão com o banco de dados só são inicializados se forem realmente necessários para a estratégia selecionada.

## Estratégia Híbrida de Segurança (Autenticação AD + RBAC Local)

A arquitetura de segurança do framework combina **autenticação corporativa centralizada** com **autorização local descentralizada**:

1. **Autenticação no Active Directory (AD):** Validação da conta corporativa da Ebserh (`EBSERHNET`). Se o funcionário for desligado, a TI desativa no AD e o acesso cessa em todos os sistemas do hospital.
2. **Autorização por Perfis (RBAC em `data/app.db`):** Tabela de usuários autorizados no banco local do sistema. A chefia do setor inclui o colaborador pelo seu login de rede e atribui o perfil de acesso adequado.

