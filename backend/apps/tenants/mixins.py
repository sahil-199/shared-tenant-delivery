from apps.tenants.models import Store


class TenantViewSetMixin:
    """
    Mixin for all tenant-scoped DRF ViewSets.
    Reads tenant_id from JWT payload, filters querysets, injects on create.
    """

    def get_tenant(self) -> Store:
        tenant_id = self.request.auth.get('tenant_id')
        if not tenant_id:
            raise ValueError("No tenant_id in token")
        return Store.objects.get(id=tenant_id)

    def get_queryset(self):
        tenant_id = self.request.auth.get('tenant_id')
        return super().get_queryset().filter(tenant_id=tenant_id)

    def perform_create(self, serializer):
        tenant = self.get_tenant()
        serializer.save(tenant=tenant)
