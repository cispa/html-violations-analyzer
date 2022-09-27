from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, create_engine
from sqlalchemy.orm import relationship, declarative_base, sessionmaker, scoped_session

# sorry for that BS

Base = declarative_base()
engine = create_engine("postgresql+psycopg2://crawl_user:secret@localhost/checker_database")

def create_my_engine(database_url):
    global engine
    engine = create_engine(database_url)

def get_session():
    engine.dispose()
    DatabaseSession = sessionmaker(bind=engine)
    database_session = scoped_session(DatabaseSession)
    return database_session

def create_database():
    Base.metadata.create_all(bind=engine)
    DatabaseSession = sessionmaker(bind=engine)
    session = DatabaseSession()
    session.commit()
    session.close()

class CheckerResult(Base):
    __tablename__ = 'checker_result'

    rule_id = Column(Integer, ForeignKey('checker_rule.id'), primary_key=True)
    website_id = Column(Integer, ForeignKey('website.id'), primary_key=True)
    result = Column(Boolean)

class CheckerRule(Base):
    __tablename__ = 'checker_rule'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    name_informal = Column(String)
    description = Column(String)
    websites = relationship('Website', secondary='checker_result', viewonly=True)

class Website(Base):
    __tablename__ = 'website'

    id = Column(Integer, primary_key=True)
    hostname = Column(String)
    domain = Column(String)
    path = Column(String)
    loaded = Column(Boolean)
    content = Column(String)
    content_hash = Column(String)
    timestamp = Column(DateTime)
    category = Column(String)
    country = Column(String)
    size = Column(Integer)
    error = Column(String)
    extra_info = Column(String)
    tranco_rank = Column(String)
    crawl = Column(String)
    rules = relationship('CheckerRule', secondary='checker_result', viewonly=True)
