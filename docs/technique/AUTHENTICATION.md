# Sistema de Autenticacao

O framework implementa um sistema de autenticacao hibrido e robusto, projetado para funcionar tanto em um ambiente corporativo com Active Directory (AD) quanto em um ambiente de desenvolvimento local sem acesso a rede.

## Estrategia de Autenticacao Dupla

O sistema utiliza um padrao de provedor para a logica de autenticacao, permitindo alternar entre dois modos:

1.  **ActiveDirectoryAuthProvider**: O provedor padrao para producao. Ele se conecta a um servidor LDAP para validar as credenciais do usuario e buscar suas informacoes e grupos de acesso.

2.  **MockAuthProvider**: Um provedor para desenvolvimento offline. Ele nao requer conexao de rede e simula a autenticacao, permitindo que desenvolvedores testem rotas protegidas e funcionalidades de diferentes niveis de acesso.

## Selecao Automatica do Provedor

A escolha entre o provedor `ActiveDirectory` e o `Mock` e feita automaticamente na inicializacao da aplicacao, com base na presenca de variaveis de ambiente.

-   **Para ativar a autenticacao com Active Directory:**
    -   Descomente e preencha as variaveis de ambiente relacionadas ao AD no seu arquivo `.env`. No minimo, a variavel `AD_URL` deve estar presente.
    ```env
    # .env
    AD_URL="ldap://seu-servidor-ad:389"
    AD_BASEDN="dc=sua-empresa,dc=com"
    # ... outras variaveis de AD
    ```
    Ao iniciar, a aplicacao detectara `AD_URL` e utilizara o `ActiveDirectoryAuthProvider`.

-   **Para ativar a autenticacao Mock (offline):**
    -   Comente ou remova as variaveis de ambiente do AD do seu arquivo `.env`.
    ```env
    # .env
    # AD_URL="ldap://seu-servidor-ad:389"
    # AD_BASEDN="dc=sua-empresa,dc=com"
    ```
    Ao iniciar, a aplicacao nao encontrara `AD_URL` e, por seguranca, utilizara o `MockAuthProvider`. Uma mensagem de aviso sera exibida no console.

### Credenciais do Provedor Mock

Quando o `MockAuthProvider` esta ativo, voce pode se autenticar com as seguintes credenciais:

-   **Usuario:** `admin`
-   **Senha:** `admin`

Este usuario recebera um conjunto de grupos pre-definidos, incluindo o grupo de administrador (`GLO-SEC-HCPE-SETISD`), permitindo testar todas as funcionalidades restritas do frontend.

## Fluxo de Tokens (JWT)

Independentemente do provedor utilizado, apos a autenticacao bem-sucedida, o sistema gera um **Access Token (JWT)** e um **Refresh Token**.

-   **Access Token**: E um token de curta duracao (configuravel via `JWT_EXP_HOURS`) que e enviado em cada requisicao a API para autorizar o acesso.
-   **Refresh Token**: E um token de longa duracao (configuravel via `REFRESH_TOKEN_EXP_DAYS`) armazenado em um cookie `HttpOnly`. Ele e usado para obter um novo Access Token sem que o usuario precise fazer login novamente.
