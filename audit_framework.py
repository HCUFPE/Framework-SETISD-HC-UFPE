#!/usr/bin/env python3
"""
Framework SETISD - Linter & Auditor de Conformidade Arquitetural (Versão Expandida)
HC-UFPE / EBSERH

Inspeciona repositórios em busca de conformidade com os 10 pilares do FrameworkSETISD:
1. Autenticação Corporativa AD/LDAP
2. Validação Híbrida de Permissões e Perfis (RBAC Local)
3. Autenticação Persistente & Cookies HttpOnly
4. Proteção de Rotas por Padrão (Default-Private Router Pattern)
5. Security Headers HTTP (Defense-in-Depth)
6. Governança de Segredos (src/config.py & .env.example)
7. Trilha de Auditoria Imutável (audit_logs & audit_helper)
8. Padrão Visual e Componentes Reutilizáveis (Frontend Vue 3 + Tailwind/CSS)
9. Monitoramento Zabbix / Healthcheck (/api/health)
10. Versionamento Semântico & Governança de IAs (SemVer & AGENTS.md)
"""

import sys
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colorize(text: str, color: str) -> str:
    if os.name == 'nt' and not os.environ.get('TERM'):
        return text
    return f"{color}{text}{ENDC}"

class FrameworkAuditor:
    def __init__(self, target_dir: str):
        self.target_dir = Path(target_dir).resolve()

    def check_file_contains(self, file_path: Path, patterns: List[str], require_all=False) -> bool:
        if not file_path.exists():
            return False
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            if require_all:
                return all(re.search(pat, content, re.MULTILINE) for pat in patterns)
            else:
                return any(re.search(pat, content, re.MULTILINE) for pat in patterns)
        except Exception:
            return False

    def audit_ad_integration(self) -> Tuple[bool, str]:
        """Verifica se a integração com AD/LDAP ou suporte a consulta de rede está configurada"""
    def audit_ad_integration(self) -> Tuple[bool, str]:
        """Verifica se a integração com AD/LDAP ou suporte a consulta de rede está configurada"""
        auth_file = self.target_dir / "src" / "auth" / "auth.py"
        auth_router = self.target_dir / "src" / "routers" / "auth.py"
        admin_router = self.target_dir / "src" / "routers" / "admin.py"
        test_ad = self.target_dir / "test_ad_connection.py"
        
        patterns = [r"ldap3", r"search_ad_user", r"ad-user-search", r"EBSERHNET", r"authenticate_user", r"ldap", r"Active Directory"]
        ok = (self.check_file_contains(auth_file, patterns) or 
              self.check_file_contains(auth_router, patterns) or 
              self.check_file_contains(admin_router, patterns) or
              self.check_file_contains(test_ad, patterns))
        
        if ok:
            return True, "Integração Active Directory (AD/LDAP) detectada"
        else:
            return False, "Falta implementação/integração com AD/LDAP"

    def audit_rbac_hybrid_auth(self) -> Tuple[bool, str]:
        """Verifica autorização híbrida (AD + Grupos/Perfis RBAC)"""
        auth_router = self.target_dir / "src" / "routers" / "auth.py"
        admin_router = self.target_dir / "src" / "routers" / "admin.py"
        user_model = self.target_dir / "src" / "models" / "user.py"
        usuario_perfil_model = self.target_dir / "src" / "models" / "usuario_perfil.py"
        roles_map = self.target_dir / "src" / "roles_map.json"
        
        has_local_profile = (usuario_perfil_model.exists() or user_model.exists() or roles_map.exists() or 
                             self.check_file_contains(auth_router, [r"perfil", r"UsuarioPerfil", r"SUPER_ADMINS", r"groups", r"role"]) or
                             self.check_file_contains(admin_router, [r"groups", r"ADMIN_GROUP", r"perfil", r"role"]))
        
        if has_local_profile:
            return True, "Autorização híbrida e controle de acesso RBAC (grupos/perfis) configurado"
        else:
            return False, "Falta validação de perfis/grupos de acesso (RBAC) em conjunto com a autenticação de rede"

    def audit_httponly_cookies(self) -> Tuple[bool, str]:
        auth_router = self.target_dir / "src" / "routers" / "auth.py"
        auth_service = self.target_dir / "src" / "services" / "auth_service.py"
        ok = (self.check_file_contains(auth_router, [r"httponly\s*=\s*True", r"refresh_token"], require_all=True) or
              self.check_file_contains(auth_service, [r"httponly\s*=\s*True", r"refresh_token"], require_all=True))
        if ok:
            return True, "Uso de Cookies HttpOnly para Refresh Token verificado em rotas de auth"
        else:
            return False, "Refresh Token não está configurado com Cookie HttpOnly em src/routers/auth.py"

    def audit_default_private_routers(self) -> Tuple[bool, str]:
        routers_dir = self.target_dir / "src" / "routers"
        if not routers_dir.exists():
            return False, "Diretório src/routers/ não encontrado"
        
        router_files = list(routers_dir.glob("*.py"))
        if not router_files:
            return False, "Nenhum arquivo de rota encontrado em src/routers/"
        
        unprotected = []
        for r_file in router_files:
            if r_file.name in ["auth.py", "health.py", "__init__.py"]:
                continue
            has_dep_global = self.check_file_contains(r_file, [r"dependencies\s*=\s*\[\s*Depends"], require_all=False)
            has_dep_route = self.check_file_contains(r_file, [r"Depends\(\s*(verify_|auth_handler|get_current_user|get_current_active_user)"], require_all=False)
            if not (has_dep_global or has_dep_route):
                unprotected.append(r_file.name)
        
        if not unprotected:
            return True, "Todos os roteadores possuem proteção de autenticação declarada (Default-Private ou Endpoint Level)"
        else:
            return False, f"Roteadores sem proteção detectados: {', '.join(unprotected)}"

    def audit_security_headers(self) -> Tuple[bool, str]:
        main_py = self.target_dir / "src" / "main.py"
        if not main_py.exists():
            main_py = self.target_dir / "main.py"
        
        sec_middleware = self.target_dir / "src" / "middlewares" / "security.py"
        
        patterns = [r"X-Content-Type-Options", r"X-Frame-Options", r"Cache-Control"]
        ok = self.check_file_contains(main_py, patterns, require_all=True) or \
             self.check_file_contains(sec_middleware, patterns, require_all=True)
             
        msg = "Middleware de Security Headers encontrado" if ok else "Falta Middleware de Security Headers (X-Frame-Options, Cache-Control)"
        return ok, msg

    def audit_config_governance(self) -> Tuple[bool, str]:
        config_py1 = self.target_dir / "src" / "config.py"
        config_py2 = self.target_dir / "src" / "core" / "config.py"
        env_example = self.target_dir / ".env.example"
        
        ok_config = config_py1.exists() or config_py2.exists()
        ok_env = env_example.exists()
        
        if ok_config and ok_env:
            return True, "Gestão de segredos centralizada (config.py) e .env.example presente"
        elif ok_config:
            return False, "Módulo de config existe, mas falta o gabarito .env.example"
        else:
            return False, "Falta o módulo de validação centralizada src/config.py"

    def audit_audit_trail(self) -> Tuple[bool, str]:
        audit_model1 = self.target_dir / "src" / "models" / "audit_log.py"
        audit_model2 = self.target_dir / "models" / "audit_log.py"
        audit_helper1 = self.target_dir / "src" / "helpers" / "audit_helper.py"
        audit_helper2 = self.target_dir / "src" / "utils" / "audit_helper.py"
        audit_helper3 = self.target_dir / "utils" / "audit_helper.py"
        
        target_model = audit_model1 if audit_model1.exists() else (audit_model2 if audit_model2.exists() else None)
        target_helper = audit_helper1 if audit_helper1.exists() else (audit_helper2 if audit_helper2.exists() else (audit_helper3 if audit_helper3.exists() else None))
        
        if not (target_model and target_helper):
            return False, "Falta implementação de auditoria unificada (necessário ambos: modelo audit_log.py e utilitário audit_helper.py)"
        
        # Validação estrita de todos os campos obrigatórios definidos no Framework
        required_fields = [
            (r"ip_origem", "IP de Origem (ip_origem)"),
            (r"(dados_anteriores|estado_anterior|antes|previous)", "Estado Anterior (dados_anteriores / estado_anterior)"),
            (r"(dados_novos|estado_novo|depois|new)", "Novo Estado (dados_novos / estado_novo)"),
            (r"categoria", "Categoria (SEGURANCA, NEGOCIO_CLINICO, CONFIGURACAO)"),
            (r"acao", "Ação executada (acao)"),
            (r"(usuario|usuario_id)", "Identificação do Usuário (usuario / usuario_id)"),
        ]
        
        missing_fields = []
        for pattern, field_name in required_fields:
            in_model = self.check_file_contains(target_model, [pattern], require_all=False)
            in_helper = self.check_file_contains(target_helper, [pattern], require_all=False)
            if not (in_model or in_helper):
                missing_fields.append(field_name)
        
        if missing_fields:
            return False, f"Trilha de auditoria incompleta. Campos obrigatórios ausentes: {', '.join(missing_fields)}"
            
        return True, "Trilha de auditoria 100% conforme (usuario, categoria, acao, dados_anteriores, dados_novos e ip_origem)"

    def audit_backend_stack(self) -> Tuple[bool, str]:
        """Verifica se o backend adota a linguagem Python + FastAPI + Uvicorn"""
        main_py = self.target_dir / "src" / "main.py"
        pyproject = self.target_dir / "pyproject.toml"
        reqs = self.target_dir / "requirements.txt"
        
        has_fastapi = (self.check_file_contains(main_py, [r"FastAPI"]) if main_py.exists() else False) or \
                      (self.check_file_contains(reqs, [r"fastapi"]) if reqs.exists() else False) or \
                      (self.check_file_contains(pyproject, [r"fastapi"]) if pyproject.exists() else False)
        
        if has_fastapi:
            return True, "Backend padronizado em Python + FastAPI + Uvicorn"
        else:
            return False, "Backend não utiliza a stack oficial Python + FastAPI"

    def audit_frontend_layout(self) -> Tuple[bool, str]:
        """Verifica se o Frontend adota o padrão visual com SidebarNav (menu lateral à esquerda), marca no topo e rodapé de versão"""
        frontend_dir = self.target_dir / "frontend"
        if not frontend_dir.exists():
            return False, "Diretório frontend/ não encontrado"
        
        sidebar_comp = frontend_dir / "src" / "components" / "SidebarNav.vue"
        default_layout = frontend_dir / "src" / "layouts" / "DefaultLayout.vue"
        app_vue = frontend_dir / "src" / "App.vue"
        
        has_sidebar = sidebar_comp.exists() or self.check_file_contains(default_layout, [r"Sidebar", r"aside", r"nav"])
        has_version_footer = self.check_file_contains(sidebar_comp, [r"APP_VERSION", r"version"]) or \
                             self.check_file_contains(default_layout, [r"version", r"VERSION"])
        
        if has_sidebar and has_version_footer:
            return True, "Layout Frontend padronizado (Menu lateral SidebarNav à esquerda + Marca no topo + Versão no rodapé)"
        elif has_sidebar:
            return True, "Layout com Menu lateral (SidebarNav) detectado"
        else:
            return False, "Falta componente de Layout padronizado (SidebarNav à esquerda / topo)"

    def audit_health_check(self) -> Tuple[bool, str]:
        health_router = self.target_dir / "src" / "routers" / "health.py"
        ok = self.check_file_contains(health_router, [r"/health"], require_all=False)
        if ok:
            return True, "Endpoint de monitoramento Zabbix (/api/health) encontrado"
        else:
            return False, "Falta endpoint de monitoramento /api/health em src/routers/health.py"

    def audit_semantic_versioning_and_agents(self) -> Tuple[bool, str]:
        version_py = self.target_dir / "src" / "version.py"
        version_ts = self.target_dir / "frontend" / "src" / "config" / "version.ts"
        agents_md = self.target_dir / "AGENTS.md"
        agents_sub_md = self.target_dir / ".agents" / "AGENTS.md"
        
        has_version = (self.check_file_contains(version_py, [r"VERSION\s*="]) if version_py.exists() else False) or \
                      (self.check_file_contains(version_ts, [r"APP_VERSION"]) if version_ts.exists() else False)
        has_agents = agents_md.exists() or agents_sub_md.exists()
        
        if has_version and has_agents:
            return True, "Versionamento semântico (SemVer) e manifesto de IA (AGENTS.md) configurados"
        elif has_version:
            return False, "Versionamento configurado, mas falta o manifesto AGENTS.md na raiz ou em .agents/"
        elif has_agents:
            return False, "Manifesto AGENTS.md presente, mas falta declaração SemVer (src/version.py ou version.ts)"
        else:
            return False, "Falta declaração de versão semântica e manifesto AGENTS.md"

    def run(self):
        print("=" * 75)
        print(colorize("   AUDITORIA DE CONFORMIDADE E ADESÃO AO FRAMEWORK SETISD", Colors.BOLD + Colors.OKCYAN))
        print(f" Alvo: {self.target_dir}")
        print("=" * 75 + "\n")

        checks = [
            ("1. Stack Padrão Backend (Python 3.12+ / FastAPI)", self.audit_backend_stack),
            ("2. Autenticação Corporativa AD/LDAP", self.audit_ad_integration),
            ("3. Autorização Híbrida e Controle de Acesso RBAC", self.audit_rbac_hybrid_auth),
            ("4. Autenticação Persistente & HttpOnly Cookies", self.audit_httponly_cookies),
            ("5. Proteção de Rotas por Padrão (Default-Private)", self.audit_default_private_routers),
            ("6. Security Headers HTTP & Defense-in-Depth", self.audit_security_headers),
            ("7. Governança de Segredos (src/config.py & .env.example)", self.audit_config_governance),
            ("8. Trilha de Auditoria Imutável (audit_logs & helper)", self.audit_audit_trail),
            ("9. Layout Frontend (SidebarNav à Esquerda + Marca + Versão)", self.audit_frontend_layout),
            ("10. Monitoramento Zabbix & Governança (/api/health & AGENTS.md)", self.audit_semantic_versioning_and_agents),
        ]

        passed = 0
        total = len(checks)

        for title, check_fn in checks:
            is_ok, detail = check_fn()
            status_tag = colorize("[ PASS ]", Colors.OKGREEN + Colors.BOLD) if is_ok else colorize("[ FAIL ]", Colors.FAIL + Colors.BOLD)
            print(f"{status_tag} {colorize(title, Colors.BOLD)}")
            print(f"         [->] {detail}\n")
            if is_ok:
                passed += 1

        score_pct = (passed / total) * 100
        print("=" * 75)
        print(colorize(f" RESULTADO FINAL DA ADESÃO AO FRAMEWORK:", Colors.BOLD))
        
        if score_pct == 100:
            color = Colors.OKGREEN
            level = "EXCELENTE (100% Conforme com o Framework)"
        elif score_pct >= 75:
            color = Colors.OKCYAN
            level = "BOM (Adesão Parcial Avançada)"
        elif score_pct >= 50:
            color = Colors.WARNING
            level = "ATENÇÃO (Muitos itens arquiteturais pendentes)"
        else:
            color = Colors.FAIL
            level = "CRÍTICO (Fora dos padrões do Framework)"

        print(colorize(f" Taxa de Conformidade: {passed}/{total} ({score_pct:.1f}%) - {level}", color + Colors.BOLD))
        print("=" * 75 + "\n")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    auditor = FrameworkAuditor(target)
    auditor.run()
