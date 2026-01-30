from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from src.seedwork.database import Base


class IOLPortfolioRawSnapshot(Base):
    __tablename__ = "iol_portfolio_raw_snapshots"

    id = Column(Integer, primary_key=True)
    identity = Column(String)
    country = Column(String)
    status_code = Column(Integer)
    fetched_at = Column(DateTime, nullable=False)
    payload = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.now)
