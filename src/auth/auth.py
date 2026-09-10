import os
import jwt
from ldap3 import Server, Connection, ALL, SUBTREE, SIMPLE
import re
import secrets
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from ..resources.database import get_app_db_session
from ..models.refresh_token import RefreshToken

load_dotenv()

# --- Configurações --- 
JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key-change-in-production")
JWT_EXP_HOURS = int(os.getenv("JWT_EXP_HOURS", 24))
REFRESH_TOKEN_EXP_DAYS = int(os.getenv("REFRESH_TOKEN_EXP_DAYS", 30))
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

# --- Interface e Implementações de Provedor de Autenticação ---

class AuthProviderInterface(ABC):
    """Interface para provedores de autenticação."""
    @abstractmethod
    def authenticate_user(self, username, password) -> dict:
        pass

    @abstractmethod
    def search_user(self, username: str) -> dict:
        pass

class MockAuthProvider(AuthProviderInterface):
    """Provedor de autenticação mock para desenvolvimento offline."""
    def authenticate_user(self, username, password) -> dict:
        print("--- Using Mock Authentication ---")
        if username == "admin" and password == "admin":
            print(f"Authentication successful for mock user: {username}")
            # O nome do grupo que o frontend usa para identificar administradores
            admin_group = "GLO-SEC-HCPE-SETISD"
            return {
                "username": "admin",
                "displayName": ["Mock Admin"],
                "groups": [admin_group, "Users"],
                "email": "admin@mock.com"
            }
        else:
            print(f"Authentication failed for mock user: {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid mock credentials"
            )

    def search_user(self, username: str) -> dict:
        """Busca simulada de usuário no AD para desenvolvimento/teste."""
        clean_username = username.strip().lower()
        mock_users = {
            "admin": {
                "exists": True,
                "username": "admin",
                "displayName": "Administrador do Sistema",
                "email": "admin@ebserh.gov.br",
                "department": "SETISD / HC-UFPE"
            },
            "joao.silva": {
                "exists": True,
                "username": "joao.silva",
                "displayName": "João da Silva",
                "email": "joao.silva@ebserh.gov.br",
                "department": "UTI Adulto / HC-UFPE"
            },
            "maria.souza": {
                "exists": True,
                "username": "maria.souza",
                "displayName": "Maria Souza",
                "email": "maria.souza@ebserh.gov.br",
                "department": "Bloco Cirúrgico / HC-UFPE"
            },
            "gestor.unidade": {
                "exists": True,
                "username": "gestor.unidade",
                "displayName": "Gestor da Unidade",
                "email": "gestor.unidade@ebserh.gov.br",
                "department": "Diretoria de Enfermagem / HC-UFPE"
            },
            "medico.exemplo": {
                "exists": True,
                "username": "medico.exemplo",
                "displayName": "Médico do Setor",
                "email": "medico.exemplo@ebserh.gov.br",
                "department": "Clínica Médica / HC-UFPE"
            },
            "enfermeiro.exemplo": {
                "exists": True,
                "username": "enfermeiro.exemplo",
                "displayName": "Enfermeiro do Setor",
                "email": "enfermeiro.exemplo@ebserh.gov.br",
                "department": "UTI Neonatal / HC-UFPE"
            },
            "farmaceutico.exemplo": {
                "exists": True,
                "username": "farmaceutico.exemplo",
                "displayName": "Farmacêutico do Setor",
                "email": "farmaceutico.exemplo@ebserh.gov.br",
                "department": "Farmácia Hospitalar / HC-UFPE"
            }
        }

        if clean_username in mock_users:
            return mock_users[clean_username]
        
        # Se for um formato 'nome.sobrenome', gera um mock dinâmico amigável
        if "." in clean_username:
            parts = clean_username.split(".")
            formatted_name = " ".join([p.capitalize() for p in parts])
            return {
                "exists": True,
                "username": clean_username,
                "displayName": formatted_name,
                "email": f"{clean_username}@ebserh.gov.br",
                "department": "Unidade Hospitalar / HC-UFPE"
            }
        
        return {
            "exists": False,
            "username": username,
            "displayName": "",
            "email": "",
            "department": ""
        }

class ActiveDirectoryAuthProvider(AuthProviderInterface):
    """Provedor de autenticação real usando LDAP/Active Directory (ldap3)."""
    def __init__(self):
        self.ad_url = os.getenv("AD_URL")
        self.ad_basedn = os.getenv("AD_BASEDN")
        self.ad_bind_user = os.getenv("AD_BIND_USER")
        self.ad_bind_password = os.getenv("AD_BIND_PASSWORD")
        if not self.ad_url or not self.ad_basedn:
            raise RuntimeError("Active Directory is not configured. Check .env file.")

    def authenticate_user(self, username, password) -> dict:
        print(f"--- Starting AD Authentication (ldap3) for user: {username} ---")
        try:
            server = Server(self.ad_url, get_info=ALL)
            user_bind_dn = f"EBSERHNET\\{username}"
            
            # Autenticação inicial (Bind)
            conn = Connection(server, user=user_bind_dn, password=password, authentication=SIMPLE, check_names=True, raise_exceptions=True)
            conn.bind()

            # Se chegamos aqui, o bind foi bem sucedido.
            # Agora buscamos informações do usuário e seus grupos.
            search_conn = conn
            if self.ad_bind_user and self.ad_bind_password:
                # Opcional: usar um usuário de serviço para buscas se o usuário logado tiver restrições
                search_conn = Connection(server, user=self.ad_bind_user, password=self.ad_bind_password, authentication=SIMPLE, check_names=True, raise_exceptions=True)
                search_conn.bind()

            search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
            search_conn.search(self.ad_basedn, search_filter, search_scope=SUBTREE, attributes=['*'])

            if not search_conn.entries:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User found during bind but search returned no data.")

            user_entry = search_conn.entries[0]
            user_info = {"username": username}
            groups = []

            # Extração de atributos selecionados para evitar problemas de serialização (como datetime)
            allowed_attrs = {
                'displayName': 'displayName',
                'mail': 'email',
                'title': 'title',
                'department': 'department',
                'employeeNumber': 'employeeNumber',
                'givenName': 'givenName',
                'userPrincipalName': 'userPrincipalName'
            }
            
            for attr_name in user_entry.entry_attributes:
                value = user_entry[attr_name].value
                attr_lower = attr_name.lower()
                
                if attr_lower == 'memberof':
                    raw_groups = value if isinstance(value, list) else [value]
                    for group_dn in raw_groups:
                        match = re.match(r'CN=([^,]+)', group_dn)
                        if match:
                            groups.append(match.group(1))
                    user_info['groups'] = groups
                elif attr_name in allowed_attrs:
                    # Garante que o valor seja SEMPRE uma lista de strings para o frontend
                    if isinstance(value, list):
                        user_info[allowed_attrs[attr_name]] = [str(v) for v in value]
                    else:
                        user_info[allowed_attrs[attr_name]] = [str(value)] if value is not None else []

            # Garante que groups sempre exista
            if 'groups' not in user_info:
                user_info['groups'] = []

            # Limpeza das conexões
            if search_conn != conn:
                search_conn.unbind()
            conn.unbind()
            
            print(f"--- AD Authentication successful for user: {username}. ---")
            return user_info

        except Exception as e:
            # Tratamento de erros específicos do ldap3 ou genéricos
            error_str = str(e)
            if "invalidCredentials" in error_str:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
            elif "server not available" in error_str.lower():
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="AD server is down or unreachable")
            else:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AD error: {e}")

    def search_user(self, username: str) -> dict:
        """Busca dados de um usuário no AD pelo login (sAMAccountName) sem efetuar login dele."""
        print(f"--- Searching AD User info (ldap3) for: {username} ---")
        try:
            server = Server(self.ad_url, get_info=ALL)
            if self.ad_bind_user and self.ad_bind_password:
                conn = Connection(server, user=self.ad_bind_user, password=self.ad_bind_password, authentication=SIMPLE, check_names=True, raise_exceptions=True)
            else:
                conn = Connection(server, authentication=SIMPLE, check_names=True, raise_exceptions=True)
            
            conn.bind()
            search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
            conn.search(self.ad_basedn, search_filter, search_scope=SUBTREE, attributes=['displayName', 'mail', 'department', 'title', 'sAMAccountName'])

            if not conn.entries:
                conn.unbind()
                return {
                    "exists": False,
                    "username": username,
                    "displayName": "",
                    "email": "",
                    "department": ""
                }

            entry = conn.entries[0]
            display_name = str(entry.displayName.value) if 'displayName' in entry and entry.displayName.value else username
            email = str(entry.mail.value) if 'mail' in entry and entry.mail.value else ""
            department = str(entry.department.value) if 'department' in entry and entry.department.value else "HC-UFPE / EBSERH"

            conn.unbind()
            return {
                "exists": True,
                "username": username,
                "displayName": display_name,
                "email": email,
                "department": department
            }
        except Exception as e:
            print(f"Error searching AD for user {username}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Falha ao consultar Active Directory: {e}"
            )

# --- AuthHandler Principal ---

class AuthHandler:
    def __init__(self):
        # Lógica de troca: decide qual provedor usar na inicialização
        ad_url = os.getenv("AD_URL")
        if ad_url and "ad.domain.local" not in ad_url:
            print("INFO: Using Active Directory authentication.")
            self.provider: AuthProviderInterface = ActiveDirectoryAuthProvider()
        else:
            print("WARNING: AD environment variables not found or template default. Using Mock authentication.")
            self.provider: AuthProviderInterface = MockAuthProvider()

    def authenticate_user(self, username, password):
        return self.provider.authenticate_user(username, password)

    def search_ad_user(self, username: str) -> dict:
        return self.provider.search_user(username)

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None):
        to_encode = data.copy()
        if 'username' in to_encode:
            to_encode['sub'] = to_encode['username']
        
        # Use o tempo Unix (timestamp) para garantir serialização JSON
        expire = datetime.utcnow() + (expires_delta or timedelta(hours=JWT_EXP_HOURS))
        to_encode.update({"exp": int(expire.timestamp())})
        
        if not JWT_SECRET:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET not configured")
        return jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")

    async def create_refresh_token(self, user_id: str, groups: list, db: AsyncSession) -> str:
        refresh_token_string = secrets.token_urlsafe(64)
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXP_DAYS)
        new_refresh_token = RefreshToken(user_id=user_id, token=refresh_token_string, groups=groups, expires_at=expires_at)
        db.add(new_refresh_token)
        await db.commit()
        return refresh_token_string

    async def verify_refresh_token(self, refresh_token: str, db: AsyncSession):
        stmt = select(RefreshToken).where(RefreshToken.token == refresh_token)
        result = await db.execute(stmt)
        token_obj = result.scalar_one_or_none()
        if not token_obj or token_obj.expires_at < datetime.utcnow():
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")
        return token_obj

    async def invalidate_refresh_token(self, refresh_token: str, db: AsyncSession):
        stmt = delete(RefreshToken).where(RefreshToken.token == refresh_token)
        await db.execute(stmt)
        await db.commit()

    def decode_token(self, token: str = Depends(oauth2_scheme)):
        try:
            if not JWT_SECRET:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT_SECRET not configured")
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# Instância única que será usada em toda a aplicação
auth_handler = AuthHandler()