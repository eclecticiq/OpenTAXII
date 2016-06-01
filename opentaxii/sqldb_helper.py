from flask import _app_ctx_stack

from sqlalchemy import orm, engine
from sqlalchemy.orm.exc import UnmappedClassError


class _QueryProperty(object):
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, type):
        try:
            mapper = orm.class_mapper(type)
            if mapper:
                return type.query_class(mapper, session=self.sa.session())
        except UnmappedClassError:
            return None


class SQLAlchemyDB(object):
    '''
    Simple SQLAlchemy helper inspired by Flask-SQLAlchemy code.

    Allows the code to use a session bind to Flask context.
    '''

    def __init__(self, db_connection, base_model, session_options=None):

        self.engine = engine.create_engine(db_connection, convert_unicode=True)

        self.Query = orm.Query
        self.session = self.create_scoped_session(session_options)
        self.Model = self.extend_base_model(base_model)

    def extend_base_model(self, base):
        if not getattr(base, 'query_class', None):
            base.query_class = self.Query

        base.query = _QueryProperty(self)
        return base

    @property
    def metadata(self):
        return self.Model.metadata

    def create_scoped_session(self, options=None):

        options = options or {}

        scopefunc = _app_ctx_stack.__ident_func__
        options.setdefault('query_cls', self.Query)

        return orm.scoped_session(
            self.create_session(options), scopefunc=scopefunc)

    def create_session(self, options):
        return orm.sessionmaker(bind=self.engine, **options)

    def create_all_tables(self):
        self.metadata.create_all(bind=self.engine)

    def init_app(self, app):
        @app.teardown_appcontext
        def shutdown_session(response_or_exc):
            self.session.remove()
            return response_or_exc
