# Services — Regras de Domínio

Lógica de domínio que não pertence a um controller específico e é compartilhada por diferentes etapas do fluxo.

---

## `maquina_estados.py` — Máquina de Estados

Controla e audita todas as transições de status das entidades do sistema.

**Por que centralizar as transições?**
Sem uma máquina de estados, qualquer controller poderia mudar o `status` de um frasco para qualquer valor, incluindo transições inválidas (ex: pular de `Na Recepção` direto para `Processamento Completo`). Centralizar aqui garante que:
- Transições inválidas são rejeitadas com erro claro (409 Conflict)
- Todo estado passa obrigatoriamente pelo registro no histórico
- O código de auditoria não é duplicado por controller

---

### Estados por entidade

**Exame** (status visível no dashboard):
```
Na Recepção → Em Macroscopia → Em Processamento → Em Microscopia → Liberado
                                                 ↘ Em Congelamento
                    Revisão Pendente ←──────────────────────────────────────┐
                          └──────────────────────────────────────────────→ Liberado
```

**Frasco** (status operacional interno):
```
Na Recepção → Aguardando Macroscopia → Em Macroscopia → Processamento Completo
```

**Cassete** (status operacional interno):
```
Aguardando Processamento → Em Processamento → Processamento Completo
```

**Bloco de Parafina:**
```
Aguardando Corte → Aguardando Microscopia
```

---

### Funções

**`transicionar(session, entidade, novo_status, *, etapa, usuario, ip, observacoes)`**

Ponto de entrada principal. Recebe qualquer entidade (Exame, Frasco, Cassete, BlocoParafina) e:

1. Verifica se a transição `status_atual → novo_status` é permitida para o tipo de entidade
2. Rejeita com `409 Conflict` se a transição não existir no dicionário de transições válidas
3. Atualiza o campo `status` da entidade
4. Delega a criação do registro de histórico

**`registrar_historico(session, entidade, *, status_anterior, status_novo, etapa, usuario, ip, observacoes)`**

Cria um registro em `HistoricoMovimentacao`. O tipo da entidade determina qual FK é preenchida (`id_exame`, `id_frasco` ou `id_cassete`).

Retorna o objeto de histórico criado para que o controller possa incluí-lo na resposta se necessário.

---

### Invariantes garantidos por esta camada

- **Nenhum status é mudado sem registro no histórico.** As duas operações (mudar status + registrar) são executadas na mesma função, impossibilitando que um controller esqueça o histórico.
- **Transições inválidas falham imediatamente.** O erro ocorre antes de qualquer operação no banco.
- **O usuário responsável é sempre registrado.** O parâmetro `usuario` é obrigatório (vem do JWT decodificado).

---

### Como usar nos controllers

```python
from ..services.maquina_estados import transicionar, StatusFrasco, Etapa

await transicionar(
    session,
    frasco,
    StatusFrasco.EM_MACROSCOPIA,
    etapa=Etapa.MACROSCOPIA,
    usuario=current_user["username"],
    ip=ip_origem,
)
# A partir daqui frasco.status == "Em Macroscopia"
# e um registro de histórico foi adicionado à sessão
```

O commit é feito pelo controller após todas as transições necessárias, mantendo a atomicidade da operação completa.
