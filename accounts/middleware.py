# accounts/middleware.py
from django.http import HttpResponseForbidden
from .models import Account

class AccountMiddleware:
    """
    Injeta request.account quando a sessão tiver 'account_slug'.
    Bloqueia acesso a rotas que exigem contexto se o slug for inválido.
    Use em views da área da account (não no Global).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        slug = request.session.get("account_slug")
        request.account = None
        if slug:
            try:
                request.account = Account.objects.get(slug=slug, is_active=True)
            except Account.DoesNotExist:
                # limpa sessão inválida
                request.session.pop("account_slug", None)
        return self.get_response(request)
