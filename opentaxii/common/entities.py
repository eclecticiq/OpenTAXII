
class Entity(object):
    '''Abstract TAXII entity class.
    '''

    def __repr__(self):
        pairs = ["%s=%s" % (k, v) for k, v in sorted(self.__dict__.items())]
        return "%s(%s)" % (self.__class__.__name__, ", ".join(pairs))
