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

# friend
class SelfRequestException(Exception):
    def __init__(self, message="자기 자신에게 친구 요청을 보낼 수 없습니다.", status=None):
        self.message = message
        super().__init__(self.message)
        self.status = status or 400

class AlreadyFriendsOrRequested(Exception):
    def __init__(self, message="이미 친구 요청을 보냈거나 이미 친구입니다.", status=None):
        self.message = message
        super().__init__(self.message)
        self.status = status or 400

# game
class InvalidGameModeException(Exception):
    def __init__(self, message="Invalid game mode.", status=None):
        self.message = message
        super().__init__(self.message)
        self.status = status or 400

class PlayerNotMatchedException(Exception):
    def __init__(self, message="Player1 is not matched.", status=None):
        self.message = message
        super().__init__(self.message)
        self.status = status or 400