"""Schemas Pydantic (request/response) da API."""

from .cassete import CasseteOut
from .etiqueta import EtiquetaOut
from .exame import ExameCreate, ExameOut
from .frasco import FrascoDetalhe, FrascoOut
from .historico import HistoricoOut
from .macroscopia import MacroscopiaCreate, MacroscopiaOut
from .paciente import PacienteInput, PacienteOut
from .resultados import MacroscopiaResult, TriagemResult

__all__ = [
    "CasseteOut",
    "EtiquetaOut",
    "ExameCreate",
    "ExameOut",
    "FrascoDetalhe",
    "FrascoOut",
    "HistoricoOut",
    "MacroscopiaCreate",
    "MacroscopiaOut",
    "PacienteInput",
    "PacienteOut",
    "MacroscopiaResult",
    "TriagemResult",
]
