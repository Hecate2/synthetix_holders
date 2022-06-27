import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

db_url = 'sqlite:///balance.sqlite.db'
engine = create_engine(db_url)
Base = declarative_base(engine)
meta = Base.metadata


class Balance(Base):
    __tablename__ = 'balance'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    contract_decimals = sqlalchemy.Column(sqlalchemy.Integer)
    contract_name = sqlalchemy.Column(sqlalchemy.String)
    contract_ticker_symbol = sqlalchemy.Column(sqlalchemy.String)
    contract_address = sqlalchemy.Column(sqlalchemy.String)
    supports_erc = sqlalchemy.Column(sqlalchemy.String)
    logo_url = sqlalchemy.Column(sqlalchemy.String)
    address = sqlalchemy.Column(sqlalchemy.String)  # contract address 0x...
    balance = sqlalchemy.Column(sqlalchemy.BigInteger)
    total_supply = sqlalchemy.Column(sqlalchemy.BigInteger)
    block_height = sqlalchemy.Column(sqlalchemy.BigInteger)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime)


meta.create_all(engine)
