class RequestProcessError(Exception):
    """
    Exception raised when an error occurs during the request processing.
    """
    pass


class InvalidSearchType(ValueError):
    """
    Exception raised when an invalid search type is provided.
    """
    pass
