class PixivoBaseException(Exception):

    def __init__(self, message):
        super().__init__(message)


class PixivoAuthException(PixivoBaseException):

    def __init__(self, message):
        super().__init__(message)


class PixivoSpiderException(PixivoBaseException):

    def __init__(self, message):
        super().__init__(message)


class PixivoDBException(PixivoBaseException):

    def __init__(self, message):
        super().__init__(message)
