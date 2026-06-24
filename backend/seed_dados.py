"""
Seed de dados para desenvolvimento.
Popula o banco com exames em diferentes etapas do fluxo para testar o frontend.

Rode com o servidor em pe:
  .venv\Scripts\python seed_dados.py [--url http://localhost:8001]
"""
import sys
import urllib.request
import urllib.error
import urllib.parse
import json

BASE = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--url" else "http://127.0.0.1:8000"


def req(method, path, body=None, token=None, form=False):
    url = BASE + path
    data, headers = None, {}
    if body is not None:
        if form:
            data = urllib.parse.urlencode(body).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_err = {}
        try:
            body_err = json.loads(e.read())
        except Exception:
            pass
        return e.code, body_err


def ok(label, s, b, expected=None):
    if expected and s != expected:
        print(f"  ERRO {label}: HTTP {s} - {b.get('detail', b)}")
        return False
    print(f"  OK   {label}")
    return True


# --- Login ---
print(f"\nConectando em {BASE} ...")
s, b = req("POST", "/api/login",
           {"username": "admin", "password": "admin", "grant_type": "password"},
           form=True)
if s != 200:
    print(f"Login falhou ({s}). Servidor esta rodando?")
    sys.exit(1)
token = b["access_token"]
print("  Login OK\n")


# --- Dados base ---
PACIENTES = [
    {"cpf": "111.111.111-11", "nome": "CARLA DIAS",            "data_nascimento": "1985-03-10", "origem": "SUS"},
    {"cpf": "333.333.333-33", "nome": "FERNANDA COSTA",        "data_nascimento": "2001-11-01", "origem": "SUS"},
    {"cpf": "444.444.444-44", "nome": "LUCAS ALMEIDA",         "data_nascimento": "1988-02-18", "origem": "SUS"},
    {"cpf": "222.222.222-22", "nome": "BRUNO LIMA",            "data_nascimento": "1991-07-22", "origem": "SUS"},
    {"cpf": "555.555.555-55", "nome": "MARIA JOSE MARIA JOSE", "data_nascimento": "1957-01-01", "origem": "HC"},
    {"cpf": "666.666.666-66", "nome": "JOSE CARLOS SILVA",     "data_nascimento": "1962-09-15", "origem": "SUS"},
    {"cpf": "777.777.777-77", "nome": "ANA PAULA SANTOS",      "data_nascimento": "1979-04-22", "origem": "SUS"},
    {"cpf": "888.888.888-88", "nome": "ROBERTO FERREIRA",      "data_nascimento": "1955-11-03", "origem": "HC"},
]

# (pac_idx, tipo_exame, tipo_peca, topografia, n_cassetes, estagio)
# estagio: 1=Na Recepcao, 2=aguardando_macro, 3=Em Processamento, 4=lote_iniciado, 5=Em Microscopia
EXAMES = [
    (4, "HP",     "Fragmentos de Endometrio",   "Utero",             4, 5),
    (0, "HP",     "Biopsia de Pele",            "Antebraco direito", 2, 3),
    (1, "HP",     "Peca de Colectomia",         "Colon Sigmoide",    6, 4),
    (2, "HP",     "Biopsia Gastrica",           "Estomago - Antro",  3, 2),
    (3, "HP",     "Biopsia de Prostata",        "Prostata",         12, 5),
    (5, "HP",     "Fragmentos de Vesicula",     "Vesicula Biliar",   2, 1),
    (6, "HPDerm", "Biopsia de Pele Eczema",     "Antebraco",         2, 3),
    (7, "HP",     "Peca de Gastrectomia",       "Estomago",          8, 2),
    (0, "HP",     "Biopsia Retal",              "Reto",              4, 1),
    (1, "IHQ",    "Biopsia Hepatica",           "Figado",            2, 4),
]

RESPONSAVEIS = ["Ana", "Carlos", "Beatriz", "Fernando"]

criados = []

print("Criando exames e populando etapas...\n")

for i, (pac_idx, tipo_exame, tipo, topo, n_cassetes, estagio) in enumerate(EXAMES):
    pac = dict(PACIENTES[pac_idx])

    label = f"[{i+1}/{len(EXAMES)}] {pac['nome'][:25]} | {tipo[:30]}"
    print(f"{label}")

    # 1. Criar exame
    s, b = req("POST", "/api/exames", {
        "paciente": pac,
        "tipo_exame": tipo_exame,
        "tipo_peca": tipo,
        "topografia": topo,
        "numero_exame_aghu": str(9865468 + i) if pac.get("origem") == "HC" else None,
    }, token=token)
    if not ok("  Triagem (criar exame)", s, b, 201):
        continue

    frasco_id = b["frasco"]["id"]
    exame_id = b["exame"]["id"]
    num_sol = b["exame"]["numero_solicitacao"]
    cassete_ids = []

    if estagio == 1:
        print(f"       Status: Na Recepcao  ({num_sol})")
        criados.append({"num": num_sol, "estagio": "Na Recepcao"})
        continue

    # 2. Encaminhar para macroscopia (so muda status do Frasco)
    s, b = req("POST", f"/api/frascos/{frasco_id}/encaminhar-macroscopia", {}, token=token)
    ok("  Encaminhar macroscopia", s, b)

    if estagio == 2:
        print(f"       Status: Na Recepcao (frasco aguardando macro)  ({num_sol})")
        criados.append({"num": num_sol, "estagio": "Na Recepcao"})
        continue

    # 3. Iniciar + registrar macroscopia
    resp = req("POST", f"/api/frascos/{frasco_id}/iniciar-macroscopia", {}, token=token)
    ok("  Iniciar macroscopia", resp[0], resp[1])

    responsavel = RESPONSAVEIS[i % len(RESPONSAVEIS)]
    s, b = req("POST", "/api/macroscopia", {
        "id_frasco": frasco_id,
        "descricao": f"Material {tipo.lower()}, {n_cassetes} fragmento(s) identificado(s). Tecido de aspecto pardo-acinzentado.",
        "numero_cassetes": n_cassetes,
    }, token=token)
    ok("  Registrar macroscopia", s, b, 201)

    if s == 201:
        cassete_ids = [c["id"] for c in b["cassetes"]]
        letras = [c["letra_fragmento"] for c in b["cassetes"]]
        print(f"       Cassetes: {letras}")

    if estagio == 3:
        print(f"       Status: Em Processamento  ({num_sol})")
        criados.append({"num": num_sol, "estagio": "Em Processamento"})
        continue

    if not cassete_ids:
        continue

    # 4. Iniciar lote de processamento
    s, b = req("POST", "/api/processamento/lote", {
        "cassete_ids": cassete_ids,
        "observacoes": f"Ciclo {responsavel}",
    }, token=token)
    ok("  Iniciar lote", s, b, 201)
    lote_id = b.get("lote", {}).get("id", "")

    if estagio == 4:
        print(f"       Status: Em Processamento (lote ativo)  ({num_sol})")
        criados.append({"num": num_sol, "estagio": "Em Processamento"})
        continue

    # 5. Concluir lote + gerar laminas
    s, b = req("POST", f"/api/processamento/lote/{lote_id}/concluir",
               {"observacoes": "OK"}, token=token)
    ok("  Concluir lote", s, b)
    blocos = b.get("blocos", [])

    s2, b2 = None, {}
    for bloco in blocos:
        s2, b2 = req("POST", f"/api/processamento/blocos/{bloco['id']}/laminas",
                     {"quantidade": 1, "coloracao": "HE"}, token=token)
    if s2:
        ok("  Gerar laminas", s2, b2, 201)
    print(f"       Status: Em Microscopia - {len(blocos)} blocos  ({num_sol})")
    criados.append({"num": num_sol, "estagio": "Em Microscopia"})

# --- Resumo ---
print("\n" + "="*55)
print("SEED CONCLUIDO")
print("="*55)
for e in criados:
    print(f"  {e['num']}  ->  {e['estagio']}")

print(f"\nTotal: {len(criados)} exames criados")
print(f"\nAcesse: {BASE}/docs para explorar via Swagger")
print(f"Dashboard: GET {BASE}/api/exames/dashboard")
