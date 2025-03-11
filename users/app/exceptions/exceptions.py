class AuthServiceError(Exception):
    default_message = "An error occurred in the auth service."

    def __init__(self, message=None):
        if message is None:
            message = self.default_message
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message
