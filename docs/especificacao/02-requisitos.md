# Especificação de Requisitos

## 1. Requisitos Funcionais (RF)
| ID | Título | Descrição | Prioridade |
| :--- | :--- | :--- | :--- |
| RF001 | Autenticação | Login via LDAP/AD do hospital. | Essencial |
| RF002 | Cadastro | Registro de pacientes com CNS/CPF. | Essencial |

## 2. Requisitos Não Funcionais (RNF)
| ID | Categoria | Descrição |
| :--- | :--- | :--- |
| RNF001 | Segurança | Criptografia AES-256. |
| RNF002 | LGPD | Auditoria de acesso a dados sensíveis. |

## 3. Detalhamento SDD (CARE)
Para cada requisito, a implementação deve seguir o padrão:

### [CARE-RF001] Autenticação LDAP
* **Context (Contexto)**: Servidor LDAP configurado e credenciais de serviço disponíveis.
* **Action (Ação)**: Criar middleware de autenticação que consulte o AD.
* **Result (Resultado)**: Token JWT gerado após sucesso; Código 401 em falha.
* **Evaluation (Avaliação)**: Executar `npm test tests/auth.spec.ts` (deve passar com 100% de sucesso).

### [CARE-RF002] Cadastro de Pacientes
* **Context (Contexto)**: Esquema de banco de dados 'PACIENTE' criado.
* **Action (Ação)**: Criar endpoint POST `/api/pacientes` com validação de CPF e CNS.
* **Result (Resultado)**: Registro persistido no banco; Log de auditoria criado.
* **Evaluation (Avaliação)**: Validar contra JSON Schema definido em `04-modelo-dados.md`.