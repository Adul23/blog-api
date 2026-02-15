from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class RegisterThrottle(AnonRateThrottle):
    scope = 'register'

class RefreshThrottle(AnonRateThrottle):
    scope = 'refresh'

class PostUserThrottle(UserRateThrottle):
    scope = 'posts'