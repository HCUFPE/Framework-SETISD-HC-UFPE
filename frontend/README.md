# Frontend — Anatomia Patológica

Frontend do sistema de Anatomia Patológica do HC, desenvolvido como parte da disciplina IESI (UFPE).

## Stack

- **Vue 3** (Composition API, `<script setup>`)
- **TypeScript**
- **Vite**
- **Tailwind CSS v4** (alpha)
- **Pinia** — estado global
- **Vue Router** — rotas
- **Axios** — cliente HTTP
- **vee-validate + zod** — validação de formulários
- **vue-toastification** — notificações
- **lucide-vue-next** + **@heroicons/vue** — ícones

## Rodando o projeto

```bash
npm install
npm run dev
```

Build de produção:
```bash
npm run build
npm run preview
```

## Variáveis de ambiente

Crie um `.env.local` na raiz de `frontend/` (não versionado):
VITE_USE_MOCK_AUTH=true

Com `true`, o login usa usuários fake (sem backend) — ver `stores/auth.ts` e `mocks/mockUsers.ts`. Necessário reiniciar `npm run dev` após criar/editar esse arquivo (Vite só lê env vars no boot).

**Usuários mock disponíveis** (senha `123456` para todos):

| Usuário | Setor |
|---|---|
| `recepcao` | Recepção |
| `macroscopia` | Macroscopia |
| `microscopia` | Microscopia |
| `tecnico` | Processamento Técnico |
| `admin` | Administrador |

Quando o backend estiver pronto, troque para `VITE_USE_MOCK_AUTH=false` (ou apague o arquivo) — nenhum outro código precisa ser alterado.

## Estrutura de pastas

Cada pasta abaixo tem seu próprio `README.md` com a lógica interna, convenções e como adicionar coisas novas. Aqui é só o mapa:

- `router/` — rotas e controle de acesso
- `stores/` — estado global (Pinia)
- `services/` — comunicação com a API
- `layouts/` — estruturas visuais (sidebar/topbar, tela de auth)
- `views/` — páginas
- `components/` — componentes de UI reutilizáveis
- `mocks/` — dados fake para desenvolvimento sem backend
- `constants/` — dados constantes e estáticos utilizados em várias partes da aplicação

## Convenções gerais do projeto

- Nomes de arquivo em inglês, lowercase/camelCase (ex: `frontDesk.vue`, `mockUsers.ts`). Conteúdo (textos, labels, mensagens) em português.
- Cores e tokens visuais usam o prefixo `lab-*` (definidos em `index.css`, via `@theme` do Tailwind v4).
- Toda chamada à API passa pela instância única em `services/api.ts` — nunca `axios` direto.
- Toda rota nasce **protegida por padrão**; só é pública se tiver `meta.public: true` (ver `router/README.md`).
- Erros de API já disparam toast automaticamente (interceptor global) — não precisa tratar manualmente em cada chamada, a menos que queira uma mensagem específica.

## Pendências conhecidas

- Backend ainda não está rodando — login real (`/api/login`), cadastro e recuperação de senha dependem dele.
- Campo de **setor** no cadastro está em aberto — depende de definição com o time do HC sobre como cada usuário recebe seu setor (Recepção/Macroscopia/Microscopia/Processamento Técnico).
- Campos **Cargo** e **Matrícula** do perfil (`ProfileDropdown`) ficam "Não Informado" até decisão do HC se esses dados vão existir no cadastro.
- Sem testes automatizados configurados ainda (Vitest não está no projeto).
- Sem ESLint/Prettier configurado.
