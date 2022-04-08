from threading import get_ident

from sqlalchemy import engine, orm
from sqlalchemy.orm.exc import UnmappedClassError


class _QueryProperty:
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, type):
        try:
            mapper = orm.class_mapper(type)
            if mapper:
                return type.query_class(mapper, session=self.sa.session())
        except UnmappedClassError:
            return None


class SQLAlchemyDB:
    '''
    Simple SQLAlchemy helper inspired by Flask-SQLAlchemy code.

    Allows the code to use a session bind to Flask context.
    '''

    def __init__(self, db_connection, base_model, session_options=None, **kwargs):
        self.engine = engine.create_engine(db_connection, **kwargs)
        self.Query = orm.Query
        self.session_options = session_options
        self.Model = self.extend_base_model(base_model)
        self._session = None

    def extend_base_model(self, base):
        if not getattr(base, 'query_class', None):
            base.query_class = self.Query

        base.query = _QueryProperty(self)
        return base

    @property
    def session(self):
        if self._session is None:
            self._session = self.create_scoped_session(self.session_options)
        return self._session

    @property
    def metadata(self):
        return self.Model.metadata

    def create_scoped_session(self, options=None):

        options = options or {}

        options.setdefault('query_cls', self.Query)

        return orm.scoped_session(
            self.create_session(options), scopefunc=get_ident)

    def create_session(self, options):
        kwargs = {
            "bind": self.engine,
            **options,
        }
        return orm.sessionmaker(**kwargs)

    def create_all_tables(self):
        self.metadata.create_all(bind=self.engine)

    def init_app(self, app):
        @app.teardown_appcontext
        def shutdown_session(response_or_exc):
            self.session.remove()
            return response_or_exc
