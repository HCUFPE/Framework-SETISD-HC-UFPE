# ADR-002 — Integração com o AGHU via Exportação Copy-Paste Estruturado

**Status:** Aceito  
**Data:** 2026-05  
**Autores:** Grupo 8 — Desafio 6

---

## Contexto

O AGHU (Sistema de Gestão Hospitalar) é a fonte primária de dados do HC/UFPE. Para que as consultas registradas no sistema pediátrico sejam incorporadas ao prontuário oficial, os dados precisam chegar ao AGHU. A API REST do AGHU está em processo de mapeamento pelo analista de TI do HC (Filipe) e não está disponível para integração direta no prazo do projeto.

**Alternativas consideradas:**
1. Integração direta via API REST do AGHU — bloqueada pela indisponibilidade do contrato
2. Integração via banco de dados do AGHU — inviável por restrições de acesso e risco de integridade
3. Exportação de texto estruturado para copy-paste — implementável imediatamente

## Decisão

O sistema gera automaticamente um **texto pré-formatado** ao finalizar a consulta, contendo todos os dados clínicos organizados por seção. O médico copia o texto e cola no campo de evolução do AGHU, realizando a assinatura digital via Certbr diretamente no AGHU.

A arquitetura já prevê a migração futura: o roteador declara `STRATEGY = "aghu"` e o `AGHUProvider` implementará a mesma interface — sem alteração no controller.

```python
# Migração futura: trocar uma linha no roteador
STRATEGY = "aghu"  # era "postgres"
```

## Consequências

**Positivas:**
- Entrega imediata de valor sem dependência de prazo externo
- Médico mantém o fluxo familiar de uso do AGHU
- Migração para API futura é transparente para a lógica de negócio

**Negativas:**
- Passo manual de copy-paste persiste enquanto a API não estiver disponível
- Sujeito a erro humano (médico pode esquecer de colar ou colar incompleto)
- Sem confirmação automática de que o dado chegou ao AGHU
