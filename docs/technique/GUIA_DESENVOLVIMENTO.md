# Guia de Implementação: Framework Web Full-Stack (Python/Vue)

Este guia descreve o passo a passo para criar novas funcionalidades neste framework, utilizando como exemplo a implementação de um módulo de consulta de **Leitos**.

---

## 1. Visão Geral da Arquitetura

O framework segue uma arquitetura em camadas com fluxo unidirecional:
**Frontend (Vue 3)** -> **Router (API)** -> **Controller** -> **Provider** -> **SQL Template**.

---

## 2. Implementação do Backend (API)

Para criar uma nova funcionalidade que lê dados do hospital (AGHU), siga estas 5 etapas:

### Passo 1: SQL Template
Crie o arquivo SQL puro que será executado no banco do hospital. Use `:parametro` para valores dinâmicos.

*   **Arquivo:** `src/providers/sql/leito/listar_leitos.sql`
```sql
SELECT 
    lto_id, 
    qrt_numero, 
    unf_seq, 
    ind_situacao 
FROM 
    agh.ain_leitos 
WHERE 
    unf_seq = :setor_id
ORDER BY 
    qrt_numero, lto_id;
```

### Passo 2: Provider
A camada que executa o SQL e retorna dicionários Python simples.

*   **Arquivo:** `src/providers/implementations/leito_postgres_provider.py`
```python
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

def get_sql_query(file_path: str) -> str:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sql_file_path = os.path.join(base_dir, '..', 'sql', file_path)
    with open(sql_file_path, 'r') as f:
        return f.read()

class LeitoPostgresProvider:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def listar_por_setor(self, setor_id: int) -> List[Dict[str, Any]]:
        query_string = get_sql_query("leito/listar_leitos.sql")
        query = text(query_string)
        
        result = await self.session.execute(query, {"setor_id": setor_id})
        return [dict(row) for row in result.mappings().all()]
```

### Passo 3: Injeção de Dependência
Configure o framework para fornecer o banco de dados correto ao seu Provider.

*   **Arquivo:** `src/dependencies.py`
```python
from .providers.implementations.leito_postgres_provider import LeitoPostgresProvider
from .resources.database import get_aghu_db_session

def get_leito_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> LeitoPostgresProvider:
    return LeitoPostgresProvider(session=session)
```

### Passo 4: Controller
Implemente a lógica de negócio e validações.

*   **Arquivo:** `src/controllers/leito_controller.py`
```python
from typing import List, Dict, Any
from fastapi import HTTPException
from ..providers.implementations.leito_postgres_provider import LeitoPostgresProvider

async def listar_leitos_setor(
    setor_id: int, 
    provider: LeitoPostgresProvider
) -> List[Dict[str, Any]]:
    if setor_id <= 0:
         raise HTTPException(status_code=400, detail="Setor inválido.")
    return await provider.listar_por_setor(setor_id)
```

### Passo 5: Router (API)
Exponha a funcionalidade via HTTP e proteja-a com autenticação.

*   **Arquivo:** `src/routers/leito.py`
```python
from fastapi import APIRouter, Depends
from typing import List
from ..auth.auth import auth_handler
from ..controllers import leito_controller
from ..dependencies import get_leito_provider
from ..providers.implementations.leito_postgres_provider import LeitoPostgresProvider

router = APIRouter(
    prefix="/api/leitos",
    tags=["Leitos"],
    dependencies=[Depends(auth_handler.decode_token)]
)

@router.get("/setor/{setor_id}", response_model=List[dict])
async def listar_leitos(
    setor_id: int,
    provider: LeitoPostgresProvider = Depends(get_leito_provider)
):
    return await leito_controller.listar_leitos_setor(setor_id, provider)
```
**Importante:** Registre o roteador em `src/main.py` usando `app.include_router(leito.router)`.

---

## 3. Implementação do Frontend (Vue 3)

### Passo 6: Gerenciamento de Estado (Pinia)
Crie uma Store para gerenciar os dados e chamadas à API.

*   **Arquivo:** `frontend/src/stores/leito.ts`
```typescript
import { defineStore } from 'pinia';
import { ref } from 'vue';
import api from '../services/api';

export const useLeitoStore = defineStore('leito', () => {
  const leitos = ref<any[]>([]);
  const loading = ref(false);

  async function buscarLeitosDoSetor(setorId: number) {
    loading.value = true;
    try {
      const response = await api.get(`/api/leitos/setor/${setorId}`);
      leitos.value = response.data;
    } catch (error) {
      console.error("Erro ao buscar leitos:", error);
    } finally {
      loading.value = false;
    }
  }
  return { leitos, loading, buscarLeitosDoSetor };
});
```

### Passo 7: Tela (View)
Crie o componente de interface usando os padrões de estilo (Tailwind) e componentes (`Card`, `Button`) do framework.

*   **Arquivo:** `frontend/src/views/Leitos.vue`
```vue
<template>
  <div class="grid grid-cols-12 gap-6">
    <div class="col-span-12">
      <Card>
        <template #header>
          <div class="flex justify-between items-center">
            <h2 class="text-xl font-semibold">Leitos do Setor</h2>
            <div class="flex space-x-2">
               <input v-model="setorInput" type="number" class="border rounded p-1" placeholder="Cód. Setor"/>
               <Button @click="carregar" variant="primary" :loading="leitoStore.loading">Buscar</Button>
            </div>
          </div>
        </template>
        
        <table class="min-w-full divide-y divide-gray-200 mt-4">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">ID</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Quarto</th>
              <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Situação</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="leito in leitoStore.leitos" :key="leito.lto_id">
              <td class="px-6 py-4">{{ leito.lto_id }}</td>
              <td class="px-6 py-4">{{ leito.qrt_numero }}</td>
              <td class="px-6 py-4">{{ leito.ind_situacao }}</td>
            </tr>
          </tbody>
        </table>
      </Card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useLeitoStore } from '../stores/leito';
import Card from '../components/Card.vue';
import Button from '../components/Button.vue';

const leitoStore = useLeitoStore();
const setorInput = ref(1);

const carregar = async () => {
  await leitoStore.buscarLeitosDoSetor(setorInput.value);
};
</script>
```

### Passo 8: Navegação
Registre a nova tela em `frontend/src/router/index.ts` e adicione o link no menu lateral em `frontend/src/layouts/DefaultLayout.vue`.

---

## 4. Regras de Ouro
1.  **Não pule camadas:** O Router nunca deve conter lógica de banco.
2.  **SQL Nativo:** Para o banco do hospital (AGHU), use sempre arquivos `.sql` brutos.
3.  **ORM:** Utilize o SQLAlchemy apenas para o banco local de lógica da aplicação (SQLite).
4.  **Segurança:** Todas as rotas de API sensíveis devem ter a dependência `Depends(auth_handler.decode_token)`.
