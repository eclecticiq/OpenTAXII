def sorted_dicts(obj):
    """
    sort all dicts contained in obj, for repeatable repr
    """
    if isinstance(obj, dict):
        response = {}
        for key, value in sorted(obj.items()):
            value = sorted_dicts(value)
            response[key] = value
    elif isinstance(obj, (list, tuple)):
        response = type(obj)(sorted_dicts(item) for item in obj)
    else:
        response = obj
    return response


class Entity:
    '''Abstract TAXII entity class.
    '''

    def __repr__(self):
        pairs = ["%s=%s" % (k, v) for k, v in sorted(sorted_dicts(self.__dict__).items())]
        return "%s(%s)" % (self.__class__.__name__, ", ".join(pairs))

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items()}

    def __eq__(self, other):
        return repr(self) == repr(other)
