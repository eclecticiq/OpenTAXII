
class ResultsNotReady(Exception):
    pass


class DoesNotExistError(Exception):
    pass


class NoReadPermission(Exception):
    pass


class NoWritePermission(Exception):
    pass


class NoReadNoWritePermission(NoReadPermission, NoWritePermission):
    pass
