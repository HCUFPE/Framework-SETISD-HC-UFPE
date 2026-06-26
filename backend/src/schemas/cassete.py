from typing import Optional

from pydantic import BaseModel, ConfigDict


class CasseteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    id_frasco: str
    letra_fragmento: str
    qr_code: str
    coloracao_padrao: str
    status: str
