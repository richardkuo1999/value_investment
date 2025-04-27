from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class DB:
    def __init__(self):
        engine = create_engine('sqlite:///files/mydb.db')  # 本地SQLite檔案
        self.session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)

########################DB table##########################
class News(Base):
    __tablename__ = 'news'  # 資料表名稱

    id = Column(Integer, primary_key=True)
    title = Column(String)
    link = Column(String)

class report(Base):
    __tablename__ = 'report'  # 資料表名稱

    id = Column(Integer, primary_key=True)
    title = Column(String)
    link = Column(String)