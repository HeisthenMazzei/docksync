from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class GroupRequiredMixin(LoginRequiredMixin):
    group_required = []

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Superusuários têm acesso total, mesmo sem estar em um grupo
        if request.user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        
        user_groups = request.user.groups.values_list('name', flat=True)
        if not set(self.group_required).intersection(user_groups):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)