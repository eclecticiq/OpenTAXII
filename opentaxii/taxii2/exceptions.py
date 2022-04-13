from marshmallow.exceptions import \
    ValidationError as MarshmallowValidationError


class ValidationError(MarshmallowValidationError):
    """
    Exception used when taxii2 envelope doesn't pass validation.
    """

    pass
