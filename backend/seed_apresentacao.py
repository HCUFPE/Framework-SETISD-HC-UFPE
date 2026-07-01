"""
seed_apresentacao.py — dataset realista e variado para a APRESENTAÇÃO FINAL.

Diferente de seed_dados.py (que usa a API e por isso produz tudo no mesmo dia e
só alcança até "Em Microscopia"), este script escreve DIRETO no banco (via os
models do backend). Isso é necessário porque:

  * a API define data_recebimento = now() → impossível variar os dias/SLA;
  * status como "Liberado", "Revisão Pendente" e "Em Congelamento" não têm
    caminho pela API (Microscopia é Fase 3).

O resultado cobre TODOS os status, com casos distribuídos em datas diferentes
(SLA variando de recente → em alerta → atrasado) e com a cadeia completa de
rastreabilidade coerente com cada status: paciente → exame → frasco → cassetes
→ macroscopia → lote → blocos → lâminas → histórico. Também ingere algumas
linhas do CSV real (data/vw_solicitacao.csv) para ilustrar que o back consome
os dados "de verdade" — que chegam bagunçados.

Uso (com a venv, a partir da pasta backend/):
  .venv\\Scripts\\python seed_apresentacao.py             # reseta e popula
  .venv\\Scripts\\python seed_apresentacao.py --no-reset   # apenas adiciona
"""
import argparse
import asyncio
import csv
import os
import sys
import uuid
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

from sqlalchemy import delete, func, select

from src.resources.database import Base, DatabaseManager
from src.models.paciente_local import PacienteLocal
from src.models.exame import Exame
from src.models.frasco import Frasco
from src.models.cassete import Cassete
from src.models.macroscopia import Macroscopia
from src.models.lote_processamento import LoteProcessamento
from src.models.bloco_parafina import BlocoParafina
from src.models.lamina import Lamina
from src.models.historico_movimentacao import HistoricoMovimentacao
from src.helpers.identificacao import (
    TIPO_EXAME_PREFIXO,
    formatar_numero_solicitacao,
    gerar_qr_code,
    gerar_codigo_interno_frasco,
    letra_fragmento,
)
from src.services.maquina_estados import (
    Etapa,
    StatusBloco,
    StatusCassete,
    StatusExame,
    StatusFrasco,
    StatusLamina,
)

NOW = datetime.now()

MACRO_RESP = ["Dra. Fernanda Lopes", "Dr. Marcelo Tavares", "Carlos Lima"]
TEC_RESP = ["Rafael Costa", "Beatriz Andrade", "Célia Ferreira"]
PATOL = ["Dr. André Meireles", "Dra. Sônia Prado", "Dr. Otávio Bastos"]
COLOR_ROTINA = "HE (Hematoxilina-Eosina) - Rotina"
COLOR_ESPECIAIS = ["Giemsa", "PAS (Ácido Periódico de Schiff)", "Ziehl-Neelsen"]


# ---------------------------------------------------------------------------
# Pacientes (mix de nomes "limpos" + alguns do padrão real, com iniciais)
# ---------------------------------------------------------------------------
PACIENTES = [
    # nome,                     cpf,           cns,             nasc,         origem
    ("Carla Dias Moreira",      "11111111111", None,            "1985-03-10", "SUS"),
    ("Fernanda Costa Silva",    "33333333333", None,            "2001-11-01", "SUS"),
    ("Lucas Almeida Rocha",     "44444444444", None,            "1988-02-18", "SUS"),
    ("Bruno Lima Tavares",      "22222222222", None,            "1991-07-22", "SUS"),
    ("Maria José dos Santos",   None,          "700000000000001", "1957-01-01", "HC"),
    ("José Carlos da Silva",    "66666666666", None,            "1962-09-15", "SUS"),
    ("Ana Paula Nogueira",      "77777777777", None,            "1979-04-22", "SUS"),
    ("Roberto Ferreira Alves",  None,          "700000000000002", "1955-11-03", "HC"),
    ("Cláudio de Farias Melo",  "88888888888", None,            "1980-06-30", "SUS"),
    ("Beatriz Helena Prado",    "99999999999", None,            "1972-12-12", "SUS"),
    ("João Batista Oliveira",   "10101010101", None,            "1948-08-08", "SUS"),
    ("Sônia Regina Campos",     None,          "700000000000003", "1965-05-19", "HC"),
    ("Rafael Duarte Nunes",     "12121212121", None,            "1993-03-03", "SUS"),
    ("Helena Martins Vieira",   "13131313131", None,            "1959-10-27", "SUS"),
    ("Otávio Ramalho Pinto",    "14141414141", None,            "1970-01-15", "SUS"),
    ("Luiza Andrade Barros",    "15151515151", None,            "1986-09-09", "SUS"),
]

# Materiais/topografias por tipo (para dar realismo aos casos)
MATERIAIS = {
    "HP": [
        ("Peça de colectomia", "Cólon sigmoide"),
        ("Biópsia gástrica", "Estômago - antro"),
        ("Biópsia de próstata", "Próstata"),
        ("Fragmentos de endométrio", "Útero"),
        ("Peça de gastrectomia", "Estômago"),
        ("Biópsia hepática", "Fígado"),
        ("Vesícula biliar", "Vesícula"),
        ("Nódulo mamário", "Mama esquerda"),
    ],
    "IHQ": [
        ("Painel imuno-histoquímico - mama", "Mama direita"),
        ("Imuno-histoquímica - linfonodo", "Linfonodo axilar"),
    ],
    "HPDerm": [
        ("Biópsia de pele - lesão pigmentada", "Antebraço direito"),
        ("Biópsia de pele - eczema", "Dorso"),
    ],
    "CG": [
        ("Esfregaço - punção de tireoide", "Tireoide - lobo direito"),
        ("Citologia de líquido pleural", "Cavidade pleural"),
    ],
    "CCV": [
        ("Esfregaço cérvico-vaginal", "Colo uterino"),
    ],
    "Congela": [
        ("Linfonodo sentinela - transoperatório", "Axila direita"),
        ("Margem cirúrgica - congelação", "Mama esquerda"),
    ],
}


class Contadores:
    """Sequencial por (tipo, ano, semestre), semeado do que já existe no banco."""

    def __init__(self):
        self._c = {}

    async def preparar(self, session):
        stmt = select(Exame.tipo_exame, Exame.ano, Exame.semestre, func.max(Exame.sequencial)).group_by(
            Exame.tipo_exame, Exame.ano, Exame.semestre
        )
        for tipo, ano, sem, mx in (await session.execute(stmt)).all():
            if tipo is not None and ano is not None and sem is not None:
                self._c[(tipo, ano, sem)] = mx or 0

    def proximo(self, tipo, entry):
        ano = entry.year
        sem = 1 if entry.month <= 6 else 2
        key = (tipo, ano, sem)
        self._c[key] = self._c.get(key, 0) + 1
        seq = self._c[key]
        return formatar_numero_solicitacao(tipo, seq, ano, sem), seq, ano, sem


def d(base, plus_days):
    return min(base + timedelta(days=plus_days), NOW)


def _hist(exame, etapa, anterior, novo, quando, usuario, obs=None):
    return HistoricoMovimentacao(
        id=str(uuid.uuid4()),
        id_exame=exame.id,
        etapa=etapa,
        status_anterior=anterior,
        status_novo=novo,
        usuario_responsavel=usuario,
        timestamp_transicao=quando,
        observacoes=obs,
    )


def construir_caso(objetos, contadores, pac, tipo, peca, topo, aghu, dias, alvo, ncas):
    """Cria o grafo de entidades coerente com `alvo` e agenda as datas."""
    entry = d(NOW, -dias)
    numero, seq, ano, sem = contadores.proximo(tipo, entry)
    macro_resp = MACRO_RESP[seq % len(MACRO_RESP)]
    tec_resp = TEC_RESP[seq % len(TEC_RESP)]
    patol = PATOL[seq % len(PATOL)]

    # Status do exame conforme o alvo
    status_exame = {
        "recepcao": StatusExame.NA_RECEPCAO,
        "em_macro": StatusExame.EM_MACROSCOPIA,
        "em_proc": StatusExame.EM_PROCESSAMENTO,
        "em_micro": StatusExame.EM_MICROSCOPIA,
        "liberado": StatusExame.LIBERADO,
        "revisao": StatusExame.REVISAO_PENDENTE,
        "congelamento": StatusExame.EM_CONGELAMENTO,
    }[alvo]

    data_conclusao = d(entry, 12) if alvo == "liberado" else None

    exame = Exame(
        id=str(uuid.uuid4()),
        numero_solicitacao=numero,
        tipo_exame=tipo,
        sequencial=seq,
        ano=ano,
        semestre=sem,
        id_paciente=pac.id,
        numero_exame_aghu=aghu,
        tipo_peca=peca,
        topografia=topo,
        status=status_exame,
        data_recebimento=entry,
        data_conclusao=data_conclusao,
        data_criacao=entry,
        criado_por="seed_apresentacao",
    )
    objetos.append(exame)
    objetos.append(_hist(exame, Etapa.TRIAGEM, None, StatusExame.NA_RECEPCAO, entry, "recepcao", "Exame criado na recepção"))

    # Status do frasco conforme o alvo
    status_frasco = {
        "recepcao": StatusFrasco.NA_RECEPCAO,
        "em_macro": StatusFrasco.EM_MACROSCOPIA,
        "congelamento": StatusFrasco.EM_MACROSCOPIA,
    }.get(alvo, StatusFrasco.PROCESSAMENTO_COMPLETO)

    tem_macro = alvo in ("em_proc", "em_micro", "liberado", "revisao")
    frasco = Frasco(
        id=str(uuid.uuid4()),
        id_exame=exame.id,
        codigo_interno=gerar_codigo_interno_frasco(numero),
        qr_code=gerar_qr_code("FRASCO", numero, identificador=str(uuid.uuid4())),
        status=status_frasco,
        descricao_macroscopia=(f"Peça recebida em formol; {peca.lower()}, clivada em {ncas} fragmento(s).") if tem_macro else None,
        numero_cassetes_gerados=ncas if tem_macro else 0,
        data_criacao=entry,
        criado_por="seed_apresentacao",
    )
    objetos.append(frasco)

    if alvo in ("em_macro", "em_proc", "em_micro", "liberado", "revisao"):
        objetos.append(_hist(exame, Etapa.TRIAGEM, None, StatusFrasco.AGUARDANDO_MACROSCOPIA, d(entry, 0), "recepcao", "Encaminhado para macroscopia"))

    if alvo in ("em_macro",):
        objetos.append(_hist(exame, Etapa.MACROSCOPIA, StatusExame.NA_RECEPCAO, StatusExame.EM_MACROSCOPIA, d(entry, 1), macro_resp, "Macroscopia iniciada"))

    # Sem cassetes ainda nesses status
    if alvo in ("recepcao", "em_macro", "congelamento"):
        return exame

    # --- macroscopia registrada (em_proc em diante) ---
    data_macro = d(entry, 1)
    objetos.append(
        Macroscopia(
            id=str(uuid.uuid4()),
            id_frasco=frasco.id,
            descricao=frasco.descricao_macroscopia,
            data_realizacao=data_macro,
            responsavel=macro_resp,
            numero_cassetes=ncas,
        )
    )
    objetos.append(_hist(exame, Etapa.MACROSCOPIA, StatusExame.NA_RECEPCAO, StatusExame.EM_MACROSCOPIA, data_macro, macro_resp))
    objetos.append(_hist(exame, Etapa.MACROSCOPIA, StatusExame.EM_MACROSCOPIA, StatusExame.EM_PROCESSAMENTO, data_macro, macro_resp, f"{ncas} cassete(s) gerado(s)"))

    processado = alvo in ("em_micro", "liberado", "revisao")

    lote = None
    if processado:
        lote_inicio = d(entry, 2)
        lote_fim = d(entry, 3)
        lote = LoteProcessamento(
            id=str(uuid.uuid4()),
            responsavel=tec_resp,
            status="Concluído",
            data_inicio=lote_inicio,
            data_fim=lote_fim,
            observacoes=f"Ciclo overnight — {tec_resp}",
            data_criacao=lote_inicio,
        )
        objetos.append(lote)

    cassetes = []
    for i in range(ncas):
        letra = letra_fragmento(i)
        cassete = Cassete(
            id=str(uuid.uuid4()),
            id_frasco=frasco.id,
            letra_fragmento=letra,
            qr_code=gerar_qr_code("CASSETE", numero, identificador=str(uuid.uuid4())),
            coloracao_padrao="HE",
            status=StatusCassete.PROCESSAMENTO_COMPLETO if processado else StatusCassete.AGUARDANDO_PROCESSAMENTO,
            id_lote_processamento=lote.id if (processado and lote) else None,
            data_criacao=data_macro,
            criado_por="seed_apresentacao",
        )
        objetos.append(cassete)
        cassetes.append((letra, cassete))

    if not processado:
        # em_proc: cassetes aguardando processamento (fila do técnico)
        return exame

    # --- blocos + lâminas (em_micro / liberado / revisao) ---
    data_bloco = d(entry, 3)
    for i, (letra, cassete) in enumerate(cassetes):
        codigo_bloco = f"{numero}-{letra}"
        bloco = BlocoParafina(
            id=str(uuid.uuid4()),
            id_cassete=cassete.id,
            id_lote=lote.id,
            codigo_bloco=codigo_bloco,
            qr_code=gerar_qr_code("BLOCO", numero, identificador=str(uuid.uuid4())),
            status=StatusBloco.AGUARDANDO_MICROSCOPIA,
            data_criacao=data_bloco,
            criado_por="seed_apresentacao",
        )
        objetos.append(bloco)

        # 1 lâmina de rotina (HE) + eventualmente 1 especial no primeiro cassete
        colors = [COLOR_ROTINA]
        if i == 0 and tipo in ("HP", "IHQ", "Congela"):
            colors.append(COLOR_ESPECIAIS[seq % len(COLOR_ESPECIAIS)])
        for n, cor in enumerate(colors, start=1):
            objetos.append(
                Lamina(
                    id=str(uuid.uuid4()),
                    id_bloco=bloco.id,
                    numero_lamina=n,
                    codigo_lamina=f"{codigo_bloco}-L{n}",
                    qr_code=gerar_qr_code("LAMINA", numero, identificador=str(uuid.uuid4())),
                    coloracao=cor,
                    status=StatusLamina.AGUARDANDO_LEITURA,
                    data_criacao=data_bloco,
                    criado_por="seed_apresentacao",
                )
            )

    objetos.append(_hist(exame, Etapa.PROCESSAMENTO, StatusExame.EM_PROCESSAMENTO, StatusExame.EM_MICROSCOPIA, data_bloco, tec_resp, "Blocos gerados; lâminas encaminhadas à microscopia"))

    if alvo == "liberado":
        objetos.append(_hist(exame, Etapa.MICROSCOPIA, StatusExame.EM_MICROSCOPIA, StatusExame.LIBERADO, data_conclusao, patol, "Laudo liberado"))
    elif alvo == "revisao":
        objetos.append(_hist(exame, Etapa.MICROSCOPIA, StatusExame.EM_MICROSCOPIA, StatusExame.REVISAO_PENDENTE, d(entry, 5), patol, "Caso encaminhado para revisão interna"))

    return exame


# (pac_idx, tipo, dias_atras, alvo, n_cassetes)  — material/topografia sorteados por tipo
# Distribuição pensada para o dashboard: todos os status + SLA variando.
CENARIOS = [
    # recém-chegados (Na Recepção) — frasco ainda Na Recepção, prontos p/ encaminhar
    (0, "HP", 0, "recepcao", 3),
    (12, "HP", 1, "recepcao", 4),
    (5, "CG", 0, "recepcao", 1),
    (1, "HP", 1, "recepcao", 2),
    (9, "HPDerm", 2, "recepcao", 2),
    (14, "HP", 2, "recepcao", 5),
    # em macroscopia
    (2, "HP", 2, "em_macro", 6),
    (7, "IHQ", 3, "em_macro", 2),
    (15, "HP", 3, "em_macro", 3),
    # em processamento (fila do técnico: cassetes aguardando)
    (3, "HP", 3, "em_proc", 4),
    (10, "HP", 5, "em_proc", 8),
    (6, "CG", 4, "em_proc", 2),
    (13, "HPDerm", 6, "em_proc", 2),
    (8, "HP", 16, "em_proc", 3),   # em alerta (>15 dias)
    # em microscopia
    (4, "HP", 7, "em_micro", 4),
    (11, "IHQ", 9, "em_micro", 2),
    (0, "HP", 12, "em_micro", 6),
    (2, "HP", 22, "em_micro", 3),  # ATRASADO (>20 dias, ainda ativo)
    (13, "HP", 26, "em_micro", 5), # ATRASADO
    # liberados (concluídos, SLA saudável)
    (5, "HP", 8, "liberado", 3),
    (6, "CG", 10, "liberado", 1),
    (11, "HP", 13, "liberado", 2),
    (1, "HPDerm", 9, "liberado", 2),
    # revisão pendente (tipicamente casos mais longos)
    (8, "HP", 24, "revisao", 4),   # ATRASADO
    (14, "IHQ", 18, "revisao", 2), # alerta
    # congelação (intraoperatório, rápido)
    (4, "Congela", 0, "congelamento", 2),
    (7, "Congela", 1, "congelamento", 1),
]


def _amostras_reais(n=5):
    """Lê algumas linhas do CSV real (bagunçado) para ilustrar a ingestão."""
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "vw_solicitacao.csv")
    if not os.path.exists(caminho):
        return []
    sigla_para_tipo = {
        "APECR": "HP", "MBIOP": "HP", "COUT2": "HP", "COLUT": "HP",
        "HPDER": "HPDerm", "IMUHI": "IHQ", "CONGE": "Congela",
        "CCVM": "CCV", "CITOP": "CG", "CPMAM": "CG",
    }
    achados = []
    try:
        with open(caminho, encoding="utf-8", errors="replace") as f:
            for row in csv.DictReader(f):
                tipo = sigla_para_tipo.get((row.get("sigla_exame") or "").strip())
                if not tipo:
                    continue
                nome = (row.get("nome_iniciais") or "").strip() or "PACIENTE AGHU"
                pront = (row.get("prontuario") or "").strip() or None
                peca = ((row.get("descricao_material") or "").strip() or (row.get("nome_exame") or "").strip() or "Material não descrito")
                nasc = (row.get("data_nascimento") or "").strip()
                achados.append({"tipo": tipo, "nome": nome, "prontuario": pront, "peca": peca[:120], "nasc": nasc})
                if len(achados) >= n:
                    break
    except Exception as e:  # noqa: BLE001
        print(f"  (aviso) não foi possível ler o CSV real: {e}")
    return achados


def _parse_nasc(s):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except (ValueError, TypeError):
            continue
    return None


async def limpar(session):
    """Remove os dados de domínio (mantém refresh_tokens)."""
    for modelo in (Lamina, BlocoParafina, Macroscopia, Cassete, LoteProcessamento, HistoricoMovimentacao, Frasco, Exame, PacienteLocal):
        await session.execute(delete(modelo))
    await session.commit()


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-reset", action="store_true", help="Não apaga os dados existentes antes de semear.")
    args = parser.parse_args()

    dsn = os.getenv("SQLITE_DSN", "sqlite+aiosqlite:///app.db")
    print(f"\nBanco: {dsn}")
    mgr = DatabaseManager(dsn)

    async with mgr.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with mgr.async_session_maker() as session:
        if not args.no_reset:
            print("Limpando dados de domínio (exames, frascos, cassetes, ... — mantém refresh_tokens)...")
            await limpar(session)

        contadores = Contadores()
        await contadores.preparar(session)

        objetos = []

        # Pacientes
        pac_objs = []
        for nome, cpf, cns, nasc, origem in PACIENTES:
            p = PacienteLocal(
                id=str(uuid.uuid4()),
                nome=nome,
                cpf=cpf,
                cns=cns,
                data_nascimento=_parse_nasc(nasc),
                origem=origem,
                criado_por="seed_apresentacao",
            )
            pac_objs.append(p)
            objetos.append(p)

        # Casos curados (todos os status, datas variadas)
        contador_material = {}
        for pac_idx, tipo, dias, alvo, ncas in CENARIOS:
            mats = MATERIAIS.get(tipo, [("Material diverso", "Não especificado")])
            k = contador_material.get(tipo, 0)
            peca, topo = mats[k % len(mats)]
            contador_material[tipo] = k + 1
            # Todo exame recebe um nº de solicitação AGHU (inventado) — assim todos
            # podem ser abertos/validados na recepção.
            aghu = str(1370000 + len(objetos))
            construir_caso(objetos, contadores, pac_objs[pac_idx], tipo, peca, topo, aghu, dias, alvo, ncas)

        # Amostras reais do CSV (bagunçadas) — chegam "Na Recepção", prontas p/ encaminhar
        reais = _amostras_reais(6)
        for i, r in enumerate(reais):
            p = PacienteLocal(
                id=str(uuid.uuid4()),
                nome=r["nome"],
                cpf=None,
                # prefixo com o índice garante unicidade (o CSV real repete prontuários)
                cns=(f"RA{i:02d}{(r['prontuario'] or '')}")[:15],
                data_nascimento=_parse_nasc(r["nasc"]),
                origem="HC",
                criado_por="seed_apresentacao(AGHU)",
            )
            objetos.append(p)
            construir_caso(objetos, contadores, p, r["tipo"], r["peca"], "AGHU (importado)", f"{1380000 + i}", i % 3, "recepcao", 1)

        session.add_all(objetos)
        await session.commit()

        # --- Resumo ---
        exames = [o for o in objetos if isinstance(o, Exame)]
        por_status = {}
        atrasados = 0
        for e in exames:
            por_status[e.status] = por_status.get(e.status, 0) + 1
            if e.status != StatusExame.LIBERADO and (NOW - e.data_recebimento).days >= 20:
                atrasados += 1

    await mgr.close_connection()

    print("\n" + "=" * 60)
    print("SEED DE APRESENTAÇÃO CONCLUÍDO")
    print("=" * 60)
    print(f"  Pacientes:        {len([o for o in objetos if isinstance(o, PacienteLocal)])}")
    print(f"  Exames:           {len(exames)}")
    print(f"  Frascos:          {len([o for o in objetos if isinstance(o, Frasco)])}")
    print(f"  Cassetes:         {len([o for o in objetos if isinstance(o, Cassete)])}")
    print(f"  Blocos:           {len([o for o in objetos if isinstance(o, BlocoParafina)])}")
    print(f"  Lâminas:          {len([o for o in objetos if isinstance(o, Lamina)])}")
    print(f"  Amostras do CSV real ingeridas: {len(reais)}")
    print("\n  Exames por status:")
    for st in [
        StatusExame.NA_RECEPCAO, StatusExame.EM_MACROSCOPIA, StatusExame.EM_PROCESSAMENTO,
        StatusExame.EM_MICROSCOPIA, StatusExame.EM_CONGELAMENTO, StatusExame.REVISAO_PENDENTE,
        StatusExame.LIBERADO,
    ]:
        print(f"    {st:22s} {por_status.get(st, 0)}")
    print(f"\n  Casos ativos ATRASADOS (SLA > 20 dias): {atrasados}")

    # Cola prática para o demo: casos que ficam NA RECEPÇÃO (frasco Na Recepção),
    # prontos para serem abertos/encaminhados na tela de Recepção. A busca aceita
    # tanto o nº de solicitação (mostrado no dashboard) quanto o nº AGHU.
    pac_nome = {p.id: p.nome for p in objetos if isinstance(p, PacienteLocal)}
    na_recepcao = sorted(
        (e for e in exames if e.status == StatusExame.NA_RECEPCAO),
        key=lambda e: e.numero_solicitacao,
    )
    print(f"\n  Na Recepção (busque por estes números na tela de Recepção): {len(na_recepcao)}")
    for e in na_recepcao:
        print(f"    {e.numero_solicitacao:16s} AGHU {e.numero_exame_aghu or '—':8s} {pac_nome.get(e.id_paciente, '—')}")

    print("\n  Dashboard: GET /api/exames/dashboard")


if __name__ == "__main__":
    asyncio.run(main())
