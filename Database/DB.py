from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import select, exists
from datetime import datetime

Base = declarative_base()

class DB:
    def __init__(self):
        engine = create_engine('sqlite:///files/mydb.db')  # 本地SQLite檔案
        Session = sessionmaker(bind=engine)
        self.session = Session()
        Base.metadata.create_all(engine)

    def checkNews(self, news: dict):
        srh = select(exists().where(News.title == news['title']))
        exists_result = self.session.execute(srh).scalar()
        if not exists_result:
            self.session.add(News(title=news['title'], link=news['url']))
            self.session.commit()
        
        return exists_result
    
    def checkReport(self, report: dict):
        srh = select(exists().where(Report.title == report['title']))
        exists_result = self.session.execute(srh).scalar()
        if not exists_result:
            self.session.add(Report(title=report['title'], link=report['url']))
            self.session.commit()
        
        return exists_result
    
    # add checkPodcast function
    def checkPodcast(self, podcast: dict):
        srh = select(exists().where((Podcast.host == podcast['host']) & (Podcast.title == podcast['title'])))
        exists_result = self.session.execute(srh).scalar()
        if not exists_result:
            self.session.add(Podcast(host=podcast['host'], title=podcast['title']))
            self.session.commit()
        
        return exists_result

########################DB table##########################
class News(Base):
    __tablename__ = 'news'  # 資料表名稱

    id = Column(Integer, primary_key=True)
    title = Column(String)
    link = Column(String)

class Report(Base):
    __tablename__ = 'report'  # 資料表名稱

    id = Column(Integer, primary_key=True)
    title = Column(String)
    link = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    
class Podcast(Base):
    __tablename__ = 'podcast'  # 資料表名稱

    id = Column(Integer, primary_key=True)
    host = Column(String)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.now)