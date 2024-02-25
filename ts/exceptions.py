# 사용자 정의 에러


class TwoFactorException(Exception):
    def __init__(self, message, status=None):
        self.message = message
        super().__init__(self.message)
        self.status = status


class FTOauthException(Exception):
    def __init__(self, message, status=None):
        self.message = message
        super().__init__(self.message)
        self.status = status
