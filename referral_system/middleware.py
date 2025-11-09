from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.db import close_old_connections
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


@database_sync_to_async
def _get_user(validated_token):
    jwt_auth = JWTAuthentication()
    return jwt_auth.get_user(validated_token)


class JWTAuthMiddleware:
    """
    Custom JWT authentication middleware for Channels.

    Expects the access token to be provided as a `token` query parameter.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        close_old_connections()
        query_string = scope.get('query_string', b'').decode()
        params = parse_qs(query_string)
        token_list = params.get('token')
        existing_user = scope.get('user', AnonymousUser())

        if token_list:
            token = token_list[0]
            jwt_auth = JWTAuthentication()
            try:
                validated_token = jwt_auth.get_validated_token(token)
                user = await _get_user(validated_token)
                scope['user'] = user
            except (InvalidToken, AuthenticationFailed, ValueError):
                scope['user'] = existing_user if getattr(existing_user, 'is_authenticated', False) else AnonymousUser()
        else:
            scope['user'] = existing_user if getattr(existing_user, 'is_authenticated', False) else AnonymousUser()

        return await self.inner(scope, receive, send)

