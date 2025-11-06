# accounts/permissions.py
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from .models import Membership

ALLOWED_READ = {"OWNER", "ADMIN", "OPERATOR", "VIEWER"}
ALLOWED_WRITE = {"OWNER", "ADMIN"}

def require_account_context(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not hasattr(request, "account") or request.account is None:
            return HttpResponseForbidden("contexto de account ausente")
        return view_func(request, *args, **kwargs)
    return _wrapped

def require_roles(*roles):
    roles_set = set(roles)
    @wraps
    def deco(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect("/admin/login/?next=" + request.path)
            if not hasattr(request, "account") or request.account is None:
                return HttpResponseForbidden("account não definida")
            has = Membership.objects.filter(
                user=request.user, account=request.account, role__in=roles_set
            ).exists()
            if not has:
                return HttpResponseForbidden("sem permissão")
            return view_func(request, *args, **kwargs)
        return _wrapped
    return deco
