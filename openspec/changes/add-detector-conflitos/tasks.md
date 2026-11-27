## 1. Estrutura do detector

- [ ] 1.1 Criar `src/controllers/alertas_controller.py` com `detectar_alertas`, filtragem de regras ativas/não excluídas e ordenação `(severidade, tipo, mensagem)`; verificar com teste que regra desativada não gera alerta e que duas execuções retornam a mesma lista

## 2. Alertas entre exames

- [ ] 2.1 Implementar `INCOMPATIBILIDADE` (matriz nas duas direções, `MEDIA` sem data, `ALTA` com intervalo violado, nada com intervalo respeitado, ignora cancelados/excluídos); verificar testes colonoscopia × hemograma pendentes, agendados com 1 dia, ressonância × oftalmo no mesmo dia e intervalo respeitado
- [ ] 2.2 Implementar `DUPLICIDADE` (status `DUPLICADA` ou mesmo prontuário + exame ativo); verificar teste de dois itens de USG abdome no mesmo prontuário

## 3. Alertas por regra do exame

- [ ] 3.1 Implementar `JANELA_RETORNO`; verificar testes espirometria 12 dias antes (`ALTA`), após o retorno (`ALTA`), INR 4 dias antes (`ALTA`), INR 2 dias antes (sem alerta) e sem data (`INFO`)
- [ ] 3.2 Implementar `ANTECEDENCIA_PREPARO`; verificar testes colonoscopia agendada para amanhã (`ALTA`) e sem data (`INFO`)
- [ ] 3.3 Implementar `JEJUM_CLINICO`; verificar testes diabético + hemograma (`MEDIA`) e não diabético (`INFO`)
- [ ] 3.4 Implementar `IDADE_MAMOGRAFIA`; verificar testes sem data de nascimento (`INFO`), abaixo de 40 (`MEDIA`) e acima (sem alerta)
- [ ] 3.5 Implementar `PRAZO_24H_VENCIDO`; verificar testes prazo vencido há 1h (`ALTA`) e em andamento (sem alerta)

## 4. Verificação

- [ ] 4.1 Rodar `.venv/bin/python -m pytest -q` e confirmar todos os testes passando
- [ ] 4.2 Rodar `python audit_framework.py .` e confirmar 100%
