# Design

## Context

O estado local de recepção é persistido em SQLite por modelos SQLAlchemy em `src/models/ap_reception.py`; os agregados de caso e IHQ são montados pelo provider. A IHQ já possui código próprio em `ApExameIhq`, mas não constitui um `ApCaso`. A proposta mantém esse contrato e acrescenta casos de Revisão com identificação própria e relação com a origem. Ver [proposal.md](./proposal.md) e as capabilities descritas em `specs/`.

O modelo de negócio documentado define IHQ como complemento e contempla `caso_relacao` entre casos, inclusive para Revisão. A implementação deve manter essa distinção: auto-relação para casos de Revisão e projeção conjunta de IHQs e Revisões no detalhe da origem.

## Goals / Non-Goals

**Goals:**
- Persistir a origem e o tipo de derivação em casos derivados, com integridade referencial e consulta nos dois sentidos.
- Expor Revisões e IHQs em um contrato unificado para detalhe, preservando as entidades e os códigos próprios de cada tipo.
- Registrar vínculo nos históricos pertinentes e na auditoria dentro da transação da recepção.

**Non-Goals:**
- Transformar IHQ em caso principal ou alterar seu fluxo de execução técnica.
- Reescrever o fluxo completo de AGHU ou criar integração externa nova.
- Alterar o ciclo de vida ou os dados históricos dos casos de origem existentes.

## Decisions

### Relação persistida em `ApCaso` para casos de Revisão

Adicionar `caso_origem_numero` nullable como FK de `ap_casos.numero_interno`, indexada, e `tipo_derivacao` nullable. Registros existentes permanecem sem origem. Para Revisão, a relação aponta ao caso principal; o caso derivado recebe número interno próprio. IHQ continua em `ApExameIhq` apontando diretamente para a origem e aparece no mesmo payload de derivados por projeção.

Alternativa considerada: mover IHQ e Revisão para uma tabela polimórfica comum. Foi descartada nesta mudança porque aumentaria o risco de migração e romperia o modelo atual de IHQ e seus contratos.

### Validação centralizada na regra de recebimento

Validar origem existente, tipo elegível e estado não terminal antes de persistir. Recusar autorreferência, ciclo direto ou indireto e divergência de prontuário sem confirmação explícita. Reutilizar o provider e o controlador de recepção existentes para que API e chamadas de UI tenham a mesma regra.

Alternativa considerada: validar apenas no frontend. Foi descartada porque chamadas diretas poderiam criar relações inválidas.

### Sugestão automática sem remover seleção manual

Na conferência, sugerir como origem o caso principal elegível que corresponda à solicitação e ao prontuário. Manter busca manual por número interno, prontuário ou nome para pedidos posteriores ou quando a relação automática não puder ser concluída. A divergência exige confirmação explícita em ambos os fluxos.

### Projeção do detalhe sem duplicar IHQ

O payload de caso terá `casoOrigem` quando aplicável e `examesDerivados` quando o caso possuir IHQs ou casos derivados. A lista unifica os campos de apresentação (código, tipo, status e data), mas preserva a fonte e a identidade de cada registro. A IHQ mantém acesso ao detalhe do caso de origem; Revisões oferecem navegação ao próprio caso.

### Migração aditiva e compatível

Criar revisão de banco aditiva com colunas nullable, FK e índice, sem reclassificar linhas existentes. Confirmar o mecanismo de migrações efetivamente usado pelo projeto antes de criar a revisão; se Alembic estiver configurado, manter a revisão em `alembic/versions/`. A implantação deve aplicar a migração antes da versão que consome os campos.

## Risks / Trade-offs

- [Revisões ainda não possuem modalidade própria no catálogo de recepção] → Definir o tipo de derivação sem reclassificar IHQ ou os casos principais; ajustar os catálogos e a geração do número da Revisão apenas no limite necessário para identificá-la.
- [Dados legados podem conter vínculos apenas no payload JSON] → A migração não inferirá origens automaticamente; preservar os registros existentes e cobrir a compatibilidade na leitura.
- [Ciclos podem surgir por atualizações concorrentes] → Validar dentro da transação e assegurar a relação antes de confirmar a mutação.
- [A auditoria pode falhar após criar caso ou vínculo] → Executar persistência, histórico e auditoria na mesma transação e reverter tudo em caso de falha.

## Migration Plan

1. Aplicar a migração aditiva com campos nulos, FK e índice.
2. Publicar backend com validação e payload compatível com casos antigos; confirmar que registros sem origem continuam consultáveis.
3. Publicar frontend que consome `casoOrigem` e `examesDerivados` e envia os dados de vínculo para Revisão.
4. Em rollback, reverter a aplicação antes de remover colunas; não apagar vínculos ou histórico já gravados sem procedimento explícito de preservação.


### Origem obrigatória da IHQ quando a solicitação contém HP

A conferência identifica todos os grupos AGHU da solicitação antes de permitir o recebimento. Quando existe grupo HP próprio, a origem da IHQ é fixa: usa o caso HP já recebido ou o caso criado pelo recebimento do HP na conferência atual. Sem esse caso, a IHQ não pode ser recebida; a interface orienta a equipe a receber HP junto ou antes. Nesses dois estados, não há radio buttons, busca nem ação de troca.

A busca manual permanece exclusiva para solicitação IHQ sem grupo HP próprio. `ReceptionController` aplica a mesma regra consultando os grupos da solicitação e rejeita caso de outra solicitação, mesmo se o cliente enviar um número de origem válido. A validação também impede a recepção da IHQ enquanto o HP próprio continuar pendente.
