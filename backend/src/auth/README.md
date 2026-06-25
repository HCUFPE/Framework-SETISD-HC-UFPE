# Autenticação e Autorização

Responsável por identificar o usuário e garantir que ele tem permissão para acessar cada rota.

---

## Arquivos

### `auth.py`

Núcleo de autenticação. Define a interface `AuthProviderInterface` e duas implementações:

| Implementação | Quando é usada | Como ativar |
|---|---|---|
| `MockAuthProvider` | Desenvolvimento offline | `AD_URL` ausente no `.env` |
| `ActiveDirectoryAuthProvider` | Produção (LDAP/AD do HC) | `AD_URL` presente no `.env` |

A escolha é automática na inicialização da aplicação — basta configurar ou omitir `AD_URL`.

**`MockAuthProvider`**: aceita `admin / admin` e devolve um usuário com grupo admin pré-configurado. Não faz chamadas de rede.

**`ActiveDirectoryAuthProvider`**: faz bind LDAP com `EBSERHNET\{username}`, busca atributos do usuário (nome, email, cargo, departamento, grupos) e extrai os grupos do campo `memberof`. Trata erros específicos do protocolo LDAP (credenciais inválidas, servidor indisponível).

**`AuthHandler`** é o ponto de entrada único — instanciado como singleton `auth_handler` e injetado via `Depends` em todas as rotas protegidas. Suas responsabilidades:

- Delegar autenticação ao provedor ativo
- Gerar e assinar tokens JWT (HS256, expiração configurável)
- Criar e validar refresh tokens (armazenados no banco de dados local)
- Decodificar o JWT em cada requisição protegida (`decode_token`)

O campo `setor` é incluído no JWT para que o frontend saiba para qual tela redirecionar o usuário após o login.

---

### `perfis.py`

Define os perfis de acesso e a dependency `require_perfil()`.

**Perfis disponíveis:**

| Perfil | Descrição |
|---|---|
| `ADMIN` | Acesso total |
| `RECEPCIONISTA` | Triagem de amostras |
| `MACROSCOPISTA` | Etapa de macroscopia |
| `TECNICO` | Processamento técnico |
| `PATOLOGISTA` | Leitura e liberação |

**`require_perfil(*perfis_exigidos)`** retorna uma dependency FastAPI que:
1. Decodifica o JWT da requisição
2. Admins sempre passam, independente dos perfis exigidos
3. Verifica se o usuário tem ao menos um dos perfis requeridos
4. Lança 403 caso contrário

> **Modo permissivo:** enquanto o HC não define os grupos AD por setor, a variável `MODO_PERMISSIVO` permite que qualquer usuário autenticado acesse todas as rotas. Isso deve ser desativado antes de ir a produção.

---

## Fluxo de autenticação

```
Login (POST /api/login)
  └─ auth_handler.authenticate_user(username, password)
      └─ Provedor ativo (Mock ou AD)
          └─ Retorna dict com username, grupos, setor
  └─ Gera access token JWT (15min com remember_me, 24h sem)
  └─ Se remember_me: gera refresh token → salva no banco → HttpOnly cookie

Requisição protegida
  └─ Bearer token no header Authorization
  └─ decode_token() verifica assinatura e expiração
  └─ require_perfil() verifica grupos/perfil
  └─ current_user dict disponível no controller

Renovação (POST /api/token/refresh)
  └─ Lê refresh_token do cookie HttpOnly
  └─ Valida contra banco de dados
  └─ Invalida o token antigo (rotation)
  └─ Reautentica usuário no AD (atualiza grupos)
  └─ Retorna novos access token + refresh token
```

---

## Variáveis de ambiente relevantes

```
JWT_SECRET          — chave de assinatura dos tokens (obrigatório)
JWT_EXP_HOURS       — duração do access token (padrão: 24h)
REFRESH_TOKEN_EXP_DAYS — duração do refresh token (padrão: 30 dias)
AD_URL              — URL do servidor LDAP (ex: ldap://servidor-ad)
AD_BASEDN           — base DN de busca (ex: cn=users,dc=ebserh,dc=net)
AD_BIND_USER        — usuário de serviço para buscas (opcional)
AD_BIND_PASSWORD    — senha do usuário de serviço (opcional)
```
