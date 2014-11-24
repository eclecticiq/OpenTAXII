import sqlalchemy
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

DB_CONNECTION_STRING = "sqlite+pysqlite:///Users/traut/Work/tmp/park/park.db"

engine = create_engine(DB_CONNECTION_STRING, pool_size=10, convert_unicode=True)
Session = scoped_session(sessionmaker(autocommit=False, autoflush=True, bind=engine))

from models.services import *
from models.collections import *

Base.query = Session.query_property()
Base.metadata.create_all(bind=engine)

#print "instance", engine, Session

def drop_all():
    Base.metadata.drop_all(bind=engine)


def get_service(path):
    try:
        return models.InboxService.objects.get(path=path, enabled=True)
    except:
        pass

    try:
        return models.DiscoveryService.objects.get(path=path, enabled=True)
    except:
        pass

    try:
        return models.PollService.objects.get(path=path, enabled=True)
    except:
        pass

    try:
        return models.CollectionManagementService.objects.get(path=path, enabled=True)
    except:
        pass

    raise Http404("No TAXII service at specified path")

