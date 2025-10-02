# accounts/models.py
import uuid
import secrets
from django.conf import settings
from django.db import models
from django.db.models import UniqueConstraint
from django.contrib.auth.hashers import make_password, check_password

# ---------------- Tenancy ----------------
class Account(models.Model):
    """Tenant: empresa assinante do Crontex."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)  # ex.: acme, patrickhf
    plan = models.CharField(max_length=40, default="basic")  # basic|pro|enterprise (MVP)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class Membership(models.Model):
    """Vínculo User x Account com papel por tenant."""
    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        ADMIN = "ADMIN", "Admin"
        OPERATOR = "OPERATOR", "Operator"
        VIEWER = "VIEWER", "Viewer"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.OPERATOR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("user", "account")]
        constraints = [
            UniqueConstraint(fields=["user", "account"], name="uix_membership_user_account")
        ]

    def __str__(self) -> str:
        return f"{self.user} @ {self.account} ({self.role})"


# ---------------- Global Roles (nível plataforma) ----------------
class GlobalUserRole(models.Model):
    """
    Papel no nível PLATAFORMA (dashboard global).
    - ADMIN: gestão completa no global.
    - SYSREAD: leitura global total (read-only).
    - AUDITOR: leitura focada em auditoria/compliance.
    Superuser é tratado via is_superuser no auth.
    """
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Global Admin"
        SYSREAD = "SYSREAD", "Global Read-only"
        AUDITOR = "AUDITOR", "Auditor"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="global_role")
    role = models.CharField(max_length=16, choices=Role.choices, default=Role.SYSREAD)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.user} · {self.role}"


# ---------------- Service/Integration Token ----------------
class ServiceToken(models.Model):
    """
    Credencial técnica para integrações e jobs.
    Boas práticas:
      - NUNCA armazenar a chave em texto puro (usar hash).
      - Escopos mínimos.
      - Opcionalmente vincular a uma Account para limitar o alcance.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # Opcional: token global (None) ou escopado a uma account específica
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True, related_name="service_tokens")
    name = models.CharField(max_length=120)
    key_hash = models.CharField(max_length=128, unique=True)  # hash da chave, não o valor bruto
    scopes = models.JSONField(default=list)                   # ex.: ["accounts:read", "products:write"]
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["account", "is_active"]),
        ]

    def __str__(self) -> str:
        scope = "global" if self.account is None else f"acct:{self.account.pk}"
        return f"{self.name} · {scope} · {'active' if self.is_active else 'inactive'}"

    # ---------- helpers de segurança ----------
    @staticmethod
    def generate_key() -> str:
        """Gera uma chave segura para exibir UMA ÚNICA VEZ ao criador."""
        # ~43 caracteres URL-safe, ~256 bits
        return secrets.token_urlsafe(32)

    def set_key(self, raw_key: str) -> None:
        """Armazena o hash da chave."""
        self.key_hash = make_password(raw_key)

    def check_key(self, raw_key: str) -> bool:
        """Verifica a chave enviada."""
        return check_password(raw_key, self.key_hash)

    def masked(self) -> str:
        """Representação mascarada p/ logs e UI."""
        return f"***{self.key_hash[-6:]}"
