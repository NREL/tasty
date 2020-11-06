from datetime import datetime


class TastyError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.when = datetime.now()


class TermNotFoundError(TastyError):
    def __init__(self, message):
        super().__init__(message)


class MultipleTermsFoundError(TastyError):
    def __init__(self, message):
        super().__init__(message)


class TemplateValidationError(TastyError):
    def __init__(self, message):
        super().__init__(message)
