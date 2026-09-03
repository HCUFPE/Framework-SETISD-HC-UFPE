# Sistema de Autenticação

O framework implementa um sistema de autenticação híbrido e robusto, projetado para funcionar tanto em um ambiente corporativo com Active Directory (AD) quanto em um ambiente de desenvolvimento local sem acesso à rede.

## Estratégia de Autenticação Dupla

O sistema utiliza um padrão de provedor para a lógica de autenticação, permitindo alternar entre dois modos:

1.  **ActiveDirectoryAuthProvider**: O provedor padrão para produção. Ele se conecta a um servidor LDAP para validar as credenciais do usuário e buscar suas informações e grupos de acesso.

2.  **MockAuthProvider**: Um provedor para desenvolvimento offline. Ele não requer conexão de rede e simula a autenticação, permitindo que desenvolvedores testem rotas protegidas e funcionalidades de diferentes níveis de acesso.

## Seleção Automática do Provedor

A escolha entre o provedor `ActiveDirectory` e o `Mock` é feita automaticamente na inicialização da aplicação, com base na presença de variáveis de ambiente.

-   **Para ativar a autenticação com Active Directory:**
    -   Descomente e preencha as variáveis de ambiente relacionadas ao AD no seu arquivo `.env`. No mínimo, a variável `AD_URL` deve estar presente.
    ```env
    # .env
    AD_URL="ldap://seu-servidor-ad:389"
    AD_BASEDN="dc=sua-empresa,dc=com"
    # ... outras variáveis de AD
    ```
    Ao iniciar, a aplicação detectará `AD_URL` e utilizará o `ActiveDirectoryAuthProvider`.

-   **Para ativar a autenticação Mock (offline):**
    -   Comente ou remova as variáveis de ambiente do AD do seu arquivo `.env`.
    ```env
    # .env
    # AD_URL="ldap://seu-servidor-ad:389"
    # AD_BASEDN="dc=sua-empresa,dc=com"
    ```
    Ao iniciar, a aplicação não encontrará `AD_URL` e, por segurança, utilizará o `MockAuthProvider`. Uma mensagem de aviso será exibida no console.

### Credenciais do Provedor Mock

Quando o `MockAuthProvider` está ativo, você pode se autenticar com as seguintes credenciais:

-   **Usuário:** `admin`
-   **Senha:** `admin`

Este usuário receberá um conjunto de grupos pré-definidos, incluindo o grupo de administrador (`GLO-SEC-HCPE-SETISD`), permitindo testar todas as funcionalidades restritas do frontend.

## Fluxo de Tokens (JWT)

Independentemente do provedor utilizado, após a autenticação bem-sucedida, o sistema gera um **Access Token (JWT)** e um **Refresh Token**.

-   **Access Token**: É um token de curta duração (configurável via `JWT_EXP_HOURS`) que é enviado em cada requisição à API para autorizar o acesso.
-   **Refresh Token**: É um token de longa duração (configurável via `REFRESH_TOKEN_EXP_DAYS`) armazenado em um cookie `HttpOnly`. Ele é usado para obter um novo Access Token sem que o usuário precise fazer login novamente.

---

## Modelo de Segurança Híbrido (Autenticação AD + RBAC Local)

Para combinar **máxima segurança corporativa** com **autonomia da gestão hospitalar**, todo sistema construído sobre este framework deve seguir o modelo em 2 etapas:

### 1. Etapa 1: Autenticação no Active Directory (AD / LDAP)
- Garante a autenticidade da conta corporativa na rede Ebserh (`EBSERHNET`).
- **Segurança Máxima:** Se um funcionário for desligado do hospital, a TI desativa a conta dele no AD e o acesso a todos os sistemas cessa automaticamente.
- **Zero Burocracia na TI:** Elimina a necessidade de criar grupos de segurança no AD para cada novo sistema.

### 2. Etapa 2: Autorização Local por Perfis (RBAC no Banco `data/app.db`)
- Cada sistema mantém sua tabela de usuários autorizados no banco local (`data/app.db`).
- A chefia/gestão do setor cadastra o usuário digitando o login do AD e selecionando seu perfil.
- Mesmo com senha do AD correta, um funcionário sem cadastro prévio no banco local do sistema recebe mensagem de acesso negado.

### Exemplos de Perfis de Acesso (Exemplificativos / Customizáveis por Sistema)
Cada sistema construído com o framework definirá seus próprios perfis de acordo com as necessidades do negócio do setor. Abaixo estão alguns exemplos comuns:

1. 🛡️ **`ADMINISTRADOR`**: Acesso total às configurações, auditoria e gestão de usuários/perfis.
2. 👨‍⚕️ **`MEDICO`**: Acesso a evolução clínica, prescrições e altas hospitalares.
3. 🩺 **`ENFERMAGEM`**: Acesso ao censo diário de leitos, checagem e sinais vitais.
4. 💊 **`FARMACEUTICO`**: Acesso à dispensação de medicamentos e controle de estoque.
5. 📊 **`GESTOR_UNIDADE`**: Acesso a relatórios estratégicos, indicadores e dashboards.
6. 👁️ **`CONSULTA`**: Acesso estritamente somente-leitura (Read-Only) para auditoria e equipes de BI.

