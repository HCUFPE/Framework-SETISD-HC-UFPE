"""
Reexportação dos modelos de contato/endereço do paciente.

As tabelas são definidas em `src/models/agendamento.py` para manter a migração
`e7c1a9d4b3f2` em um único lugar; este módulo oferece o caminho de import
previsto para o domínio de contatos.
"""

from .agendamento import ContatoPaciente, PacienteEndereco

__all__ = ["ContatoPaciente", "PacienteEndereco"]
