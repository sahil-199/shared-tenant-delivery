from rest_framework_simplejwt.tokens import RefreshToken


class TenantRefreshToken(RefreshToken):
    @classmethod
    def for_user_and_store(cls, user, store):
        token = cls.for_user(user)
        token['tenant_id'] = store.id
        token['phone'] = user.phone
        token['is_store_owner'] = user.is_store_owner
        # propagate to access token
        token.access_token['tenant_id'] = store.id
        token.access_token['phone'] = user.phone
        token.access_token['is_store_owner'] = user.is_store_owner
        return token
