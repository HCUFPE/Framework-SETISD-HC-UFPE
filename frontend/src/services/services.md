# services/

Camada de comunicação com o backend. Nenhuma view ou store deve importar `axios` diretamente — sempre passam por aqui.

## Arquivo central: cliente HTTP

Existe uma instância única do Axios configurada com:
- **Interceptor de request**: injeta automaticamente o header de autenticação em toda chamada, lendo o token do store de sessão.
- **Interceptor de response**: trata erros de autenticação de forma centralizada (ex: token expirado → tenta renovar e repete a requisição original; se falhar, desloga o usuário). Isso evita que cada chamada precise tratar expiração de token manualmente.

Qualquer chamada à API deve usar essa instância, não `fetch` ou `axios` cru.

## Convenção para novos domínios de API

Conforme o projeto crescer, evite chamar `api.get(...)`/`api.post(...)` direto dentro das views. Prefira criar um arquivo por domínio aqui, ex:

```
services/
    ├──api.ts          # instância base do axios + ├──interceptors
    ├──pacientes.ts    # funções específicas desse domínio
    └──exames.ts
```

Cada arquivo de domínio exporta funções puras que recebem parâmetros e retornam dados já tratados:

```ts
// exames.ts
import api from './api';

export async function listarExames() {
  const { data } = await api.get('/api/exames');
  return data;
}
```

Vantagens: facilita teste, evita repetir URLs/lógica em várias views, e centraliza qualquer mudança de contrato da API num único lugar.

## Como adicionar uma nova chamada à API

1. Identifique o domínio (existe um arquivo pra ele? se não, crie).
2. Escreva a função usando a instância `api`.
3. Importe e use a função na view/store — nunca chame `api` direto na view se já existir (ou se fizer sentido existir) um arquivo de domínio.