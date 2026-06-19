# constants/

Valores estáticos, configurações globais, dicionários e mapeamentos que não mudam durante a execução da aplicação. Centralizar esses dados evita *magic strings* espalhadas pelo código e facilita manutenções futuras.

## Como funciona a organização

As constantes são separadas por domínio ou contexto (como `sectors.ts` para dados dos setores do laboratório). Elas devem ser exportadas de forma limpa para que qualquer componente, store ou arquivo de rotas possa consumi-las.

```ts
// Exemplo de consumo (em um componente ou router)
import { OPERATIONAL_SECTORS, SECTOR_INFO } from '@/constants/sectors';
```

## Convenção de uma constante

### Imutabilidade

Devem representar dados puramente estáticos. Se o valor depende do estado da aplicação ou de requisições HTTP, deve ficar em uma store (Pinia), não aqui.

### Tipagem Forte

Sempre que aplicável, defina os tipos TypeScript correspondentes (como `export type Sector = ...`) no próprio arquivo da constante para garantir consistência em todo o projeto.

### Nomenclatura

Utilize **SNAKE_CASE** em letras maiúsculas para o nome das constantes (como `SECTOR_INFO` e `OPERATIONAL_SECTORS`) para diferenciá-las visualmente de variáveis comuns e funções.

## Como adicionar uma nova constante

1. Identifique o domínio da constante.

   * Se já existir um arquivo correspondente (como `sectors.ts`), adicione a constante nele.
   * Caso contrário, crie um novo arquivo descritivo (ex.: `status.ts`, `permissions.ts`).

2. Defina os tipos (`type` ou `interface`) se a constante for um objeto ou array complexo.

3. Exporte a constante utilizando `export const`.

4. *(Opcional)* Se a pasta crescer muito, crie um arquivo `index.ts` na raiz da pasta realizando o re-export dos módulos para simplificar os imports.

## Quando criar uma constante vs. deixar no código

### Crie uma constante quando

* O valor é reutilizado em mais de um lugar.
* Define regras de negócio estáticas.
* Alimenta componentes de navegação, formulários ou seletores.
* Representa configurações globais da aplicação.

### Deixe no código quando

* O valor for estritamente local.
* Representar uma configuração temporária ou específica de um único componente.
* Fizer sentido apenas dentro de um método ou view específica.
