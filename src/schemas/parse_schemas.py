from datetime import datetime

from pydantic import BaseModel


class SolscanResult(BaseModel):
    date: datetime = datetime.now()
    hash: str = "-"
    sol_count: str = "-"
    sol_usd: str = "-"
    spl_count: str = "-"
    spl_usd: str = "-"
