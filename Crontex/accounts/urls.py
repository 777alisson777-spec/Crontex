from django.urls import path
from .views import (
    GlobalDashboardView,
    AccountListView,
    AccountCreateView,
    ImpersonateStartView,
    ImpersonateStopView,
    GlobalUsersListView,
    GlobalUserCreateView,
    GlobalUserUpdateView,
    GlobalUserDeactivateView,
)
from .views_membership import (
    MembershipListView,
    MembershipCreateView,
    MembershipUpdateView,
    MembershipDeleteView,
)
from .views_token import (
    ServiceTokenListView,
    ServiceTokenCreateView,
    ServiceTokenUpdateView,
    ServiceTokenRotateView,
    ServiceTokenDeactivateView,
)
from .views_account import AccountDashboardView

app_name = "accounts"

urlpatterns = [
    # Global
    path("global/", GlobalDashboardView.as_view(), name="global_dashboard"),
    path("global/users/", GlobalUsersListView.as_view(), name="global_users"),
    path("global/users/new/", GlobalUserCreateView.as_view(), name="global_user_create"),
    path("global/users/<int:user_id>/", GlobalUserUpdateView.as_view(), name="global_user_update"),
    path("global/users/<int:user_id>/deactivate/", GlobalUserDeactivateView.as_view(), name="global_user_deactivate"),

    path("global/accounts/", AccountListView.as_view(), name="account_list"),
    path("global/accounts/new/", AccountCreateView.as_view(), name="account_create"),

    path("global/tokens/", ServiceTokenListView.as_view(), name="token_list"),
    path("global/tokens/new/", ServiceTokenCreateView.as_view(), name="token_create"),
    path("global/tokens/<uuid:token_id>/", ServiceTokenUpdateView.as_view(), name="token_update"),
    path("global/tokens/<uuid:token_id>/rotate/", ServiceTokenRotateView.as_view(), name="token_rotate"),
    path("global/tokens/<uuid:token_id>/deactivate/", ServiceTokenDeactivateView.as_view(), name="token_deactivate"),

    path("global/impersonate/<slug:slug>/start/", ImpersonateStartView.as_view(), name="impersonate_start"),
    path("global/impersonate/stop/", ImpersonateStopView.as_view(), name="impersonate_stop"),

    # Account scope
    path("account/dashboard/", AccountDashboardView.as_view(), name="account_dashboard"),
    path("account/members/", MembershipListView.as_view(), name="member_list"),
    path("account/members/new/", MembershipCreateView.as_view(), name="member_create"),
    path("account/members/<int:member_id>/edit/", MembershipUpdateView.as_view(), name="member_update"),
    path("account/members/<int:member_id>/delete/", MembershipDeleteView.as_view(), name="member_delete"),
]
