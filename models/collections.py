
from .abstract import *


class ContentBlock(Timestamped):
    """
    Model for a Content Block
    """
    message = Column(Text, nullable=True)

    timestamp_label = Column(DateTime, default=datetime.now)

    inbox_message_id = Column(Integer, ForeignKey('inbox_messages.id'))
    inbox_message = relationship('InboxMessage', backref='content_blocks')

    content = Column(Text)
    padding = Column(Text, nullable=True)

    def __str__(self):
        return u'#%s: %s; %s' % (self.id, self.content_binding_and_subtype, self.timestamp_label.isoformat())


collection_to_content_block = Table('collection_to_content_block', Base.metadata,
    Column('collection_id', Integer, ForeignKey('data_collections.id')),
    Column('content_block_id', Integer, ForeignKey('content_block.id'))
)


class DataCollection(Timestamped):
    """
    Model for a TAXII Data Collection
    """
    name = Column(String(MAX_NAME_LENGTH), unique=True)
    description = Column(Text, nullable=True)
    type = Column(String(MAX_NAME_LENGTH))
    enabled = Column(Boolean, default=True)
    accept_all_content = Column(Boolean, default=False)

    #supported_content = models.ManyToManyField('ContentBindingAndSubtype', blank=True, null=True)

    content_blocks = relationship('ContentBlock', secondary=collection_to_content_block, nullable=True)

    def is_content_supported(self, cbas):
        """
        Takes an ContentBindingAndSubtype object and determines if
        this data collection supports it.

        Decision process is:
        1. If this accepts any content, return True
        2. If this supports binding ID > (All), return True
        3. If this supports binding ID and subtype ID, return True
        4. Otherwise, return False,
        """

        return self.accept_all_content or \
                len(self.supported_content.filter(content_binding=cbas.content_binding, subtype=None)) > 0 or \
                len(self.supported_content.filter(content_binding=cbas.content_binding, subtype=cbas.subtype)) > 0


    def __str__(self):
        return u'%s(%s, %s)' % (self.__class__.__name__, self.name, self.type)


class QueryScope(Timestamped):
    """
    Model for Query Scope
    """
    name = Column(String(MAX_NAME_LENGTH))
    description = Column(Text, nullable=True)

    supported_query_id = Column(Integer, ForeignKey('supported_query.id'))
    supported_query = relationship('SupportedQuery', backref='query_scopes')

    scope = Column(String(MAX_NAME_LENGTH))
    scope_type = Column(String(MAX_NAME_LENGTH))

    def __str__(self):
        return u'%s(%s=%s)' % (self.__class__.__name__, self.name, self.scope)
