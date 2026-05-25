# Arquitetura do Projeto

Este documento detalha a arquitetura em camadas e os padroes de projeto utilizados no framework, com foco em desacoplamento e flexibilidade.

## Arquitetura em Camadas

O fluxo de uma requisicao na aplicacao segue um padrao claro e unidirecional, garantindo a separacao de responsabilidades.

**Fluxo: `Roteador` -> `Controller` -> `Provedor`**

1.  **Roteador (`src/routers/`)**
    - **Responsabilidade:** Define os endpoints da API (`@router.get`, `@router.post`, etc.), valida os dados de entrada (usando Pydantic) e gerencia a injecao de dependencias.
    - **Funcao:** E o ponto de entrada de uma requisicao HTTP. Ele utiliza o sistema `Depends` do FastAPI para solicitar as dependencias necessarias (como um provedor de dados) e, em seguida, chama a funcao apropriada no controller, passando a dependencia ja resolvida.

2.  **Controller (`src/controllers/`)**
    - **Responsabilidade:** Contem a logica de negocio. Ele orquestra as operacoes, formata dados e toma decisoes.
    - **Funcao:** Recebe as dependencias ja prontas do roteador. Ele nao sabe (e nao deve saber) qual implementacao concreta esta sendo usada (ex: se os dados vem de um banco ou de um CSV). Ele apenas utiliza os metodos definidos pela interface do provedor.

3.  **Provedor (`src/providers/`)**
    - **Responsabilidade:** Camada de acesso a dados. E a unica parte do sistema que sabe como obter ou persistir dados em uma fonte especifica (PostgreSQL, Oracle, CSV, API externa, etc.).
    - **Funcao:** Implementa uma interface (contrato) definida em `src/providers/interfaces/`. Cada implementacao concreta (ex: `PacientePostgresProvider`, `PacienteCsvProvider`) contem a logica especifica para uma fonte de dados.

## Padrao de Provedor com Selecao de Estrategia

A principal caracteristica arquitetural do framework e a capacidade de trocar a fonte de dados de um dominio de forma limpa e explicita.

### Como Funciona

1.  **Interfaces (`src/providers/interfaces/`)**: Para cada dominio (ex: `paciente`), existe um "contrato" (`PacienteProviderInterface`) que define os metodos que devem estar disponiveis (ex: `listar_pacientes`).

2.  **Implementacoes (`src/providers/implementations/`)**: Para cada interface, podem existir varias implementacoes concretas. Por exemplo, `PacientePostgresProvider` e `PacienteCsvProvider` ambas implementam `PacienteProviderInterface`.

3.  **Fabrica de Dependencias (`src/dependencies.py`)**: Este arquivo contem uma funcao fabrica (ex: `get_paciente_provider`) que recebe uma string de "estrategia" (`'postgres'` ou `'csv'`). Com base nessa string, a fabrica retorna a **funcao de dependencia correta** que o FastAPI deve usar para criar o provedor. Isso garante que a conexao com o banco de dados so seja tentada se a estrategia `'postgres'` for selecionada.

4.  **Configuracao no Roteador (`src/routers/`)**: O arquivo do roteador e o local onde a estrategia e definida.

    ```python
    # Em src/routers/paciente.py

    # --- PONTO UNICO DE CONFIGURACAO PARA ESTE ROTEADOR ---
    # Para usar o banco de dados em producao, altere esta linha para "postgres"
    STRATEGY = "csv"
    # ----------------------------------------------------

    @router.get("", ...)
    async def listar_pacientes(
        # A fabrica e chamada com a estrategia, e o FastAPI injeta o provedor correto.
        provider: PacienteProviderInterface = Depends(get_paciente_provider(STRATEGY))
    ):
        return await paciente_controller.listar_pacientes(provider)
    ```

### Vantagens desta Abordagem

- **Flexibilidade:** Permite usar fontes de dados diferentes em ambientes diferentes (ex: CSV em desenvolvimento, Postgres em producao).
- **Desacoplamento Real:** A logica de negocio no controller nunca e afetada pela fonte de dados.
- **Clareza:** Fica explicito no roteador qual fonte de dados esta sendo utilizada para aquele dominio.
- **Eficiencia:** Recursos como pools de conexao com o banco de dados so sao inicializados se forem realmente necessarios para a estrategia selecionada.
