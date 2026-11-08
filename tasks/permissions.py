from functools import wraps

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


def _check_role(request, required_admin):
    if bool(request.user.usuario_administrador) != required_admin:
        raise PermissionDenied


def role_required(*, admin):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            _check_role(request, admin)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


specialist_required = role_required(admin=False)


class _RoleRequiredMixin(LoginRequiredMixin):
    required_admin = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            _check_role(request, self.required_admin)
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin(_RoleRequiredMixin):
    required_admin = True


class SpecialistRequiredMixin(_RoleRequiredMixin):
    required_admin = False
