


def validate_body(body, debug=True):
    try:
        result = parse_tuple.validator.validate_string(request.body)
        if not result.valid:
            if debug:
                return 'Request was not schema valid: %s' % [err for err in result.error_log]
            else:
                return PV_ERR
    except XMLSyntaxError as e:
        if debug:
            return 'Request was not well-formed XML: %s' % str(e)
        else:
            return PV_ERR
