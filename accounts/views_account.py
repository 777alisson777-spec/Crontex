# accounts/views_account.py
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from .models import Membership
from .permissions import require_account_context

def av(view_cls):
    """Auth + contexto de account obrigatório."""
    return method_decorator([login_required, require_account_context], name="dispatch")(view_cls)

@av
class AccountDashboardView(View):
    template_name = "accounts/account_dashboard.html"

    def get(self, request):
        # KPIs básicos do tenant
        members_total = Membership.objects.filter(account=request.account).count()
        members_by_role = (
            Membership.objects.filter(account=request.account)
            .values("role").annotate(qty=Count("id")).order_by("role")
        )

        ctx = {
            "account": request.account,
            "members_total": members_total,
            "members_by_role": list(members_by_role),
        }
        return render(request, self.template_name, ctx)
