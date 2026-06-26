# `types/`

Definições de tipos e interfaces TypeScript globais que moldam as estruturas de dados do sistema. Esta pasta centraliza os contratos de dados compartilhados entre `views`, `components`, `stores` e `services`, garantindo consistência e prevenindo erros de tipagem em tempo de desenvolvimento.

---

## Estrutura de arquivos

Os arquivos de tipo devem ser organizados por domínio de negócio ou contextos bem delimitados da aplicação.

```text
types/
    └──exam.ts        # Tipagens do fluxo de exames e dados do AGHU
```

---

## Responsabilidade desta pasta

- Conter apenas definições puras do TypeScript (`interface`, `type` e `enum`).
- Representar os contratos de dados que trafegam pelo sistema, refletindo fielmente os payloads das APIs (`services/`) e as estruturas consumidas pela interface (`views/` e `components`).
- **Não conter código executável** (funções, variáveis ou lógica de negócio).

Caso um tipo necessite de um mapeamento estático associado (por exemplo, rótulos de exibição para tipos de exame), esse mapeamento deve ser colocado em `constants/`, e não nesta pasta.

---

## Convenção de tipagem

```ts
import type { ExamType } from '../constants/examTypes';

/** Contrato de dados estruturados para um domínio */
export interface ExemploData {
  id: string;
  criadoEm: Date;
  status: 'ativo' | 'inativo'; // Unions literais para valores discretos
  metadados?: Record<string, unknown>; // Objetos dinâmicos tipados de forma segura
}
```

### Boas práticas

- Utilize **`interface`** para representar entidades de negócio estruturadas.
- Utilize **`type`** para:
  - aliases de tipos;
  - unions (ex.: `'Internado' | 'Ambulatorial'`);
  - interseções e composições complexas.
- Sempre utilize **`import type`** ao importar apenas tipos, reduzindo código gerado no build.
- Adicione comentários em **JSDoc** quando o significado de uma propriedade não for imediatamente evidente.

---

## Arquivos existentes

### `exam.ts`

Centraliza as interfaces relacionadas ao ciclo de vida dos exames patológicos.

Inclui desde os dados brutos recebidos do hospital (`AghuData`), passando pelas etapas intermediárias do fluxo laboratorial:

- `RecepcaoData`
- `MacroscopiaData`
- `ProcessamentoData`
- `MicroscopiaData`

até consolidar a estrutura completa utilizada na visualização do caso:

- `ExamCaseDetail`

---

## Como adicionar um novo arquivo de tipos

1. Avalie se o tipo pertence a um domínio já existente.
   - Exemplo: se for relacionado a exames, adicione em `exam.ts`.
2. Caso represente um novo domínio, crie um arquivo com nome descritivo em letras minúsculas.

Exemplos:

```text
patient.ts
log.ts
notification.ts
```

3. Exporte explicitamente todas as interfaces e tipos.

```ts
export interface PatientData {}
export type PatientStatus = 'ativo' | 'inativo';
```

4. Importe os tipos diretamente onde forem utilizados.

```ts
import type { ExamCaseDetail } from '@/types/exam';
```

---

## Quando criar um tipo nesta pasta

Crie um tipo em `types/` quando ele:

- representar dados recebidos ou enviados por uma API (`services/`);
- for compartilhado entre Stores, Views e Components;
- representar uma entidade central do domínio da aplicação.

---

## Quando manter o tipo local

Mantenha a tipagem dentro do próprio componente quando ela for exclusivamente relacionada à interface daquele componente, como:

- `Props`;
- `Emits`;
- estados internos específicos;
- configurações de um modal ou botão que não são reutilizadas em outro lugar.

---

## Resumo

| Criar em `types/` | Manter no componente |
|-------------------|----------------------|
| Payloads de API | Props |
| Entidades de negócio | Emits |
| Tipos compartilhados | Estados visuais locais |
| Dados usados por Stores e Views | Tipagens exclusivas do componente |