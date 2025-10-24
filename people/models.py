from django.db import models
from django.core.validators import EmailValidator, RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

# --- Helpers/validators ---
def only_digits(value: str) -> str:
    return ''.join(ch for ch in (value or '') if ch.isdigit())

def validate_cpf(value):
    v = only_digits(value)
    if not v:
        return
    if len(v) != 11 or len(set(v)) == 1:
        raise ValidationError(_("CPF inválido."))
    def dv(nums, mult_start):
        s = sum(int(d)*m for d, m in zip(nums, range(mult_start, 1, -1)))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    if int(v[9]) != dv(v[:9], 10) or int(v[10]) != dv(v[:10], 11):
        raise ValidationError(_("CPF inválido."))

def validate_cnpj(value):
    v = only_digits(value)
    if not v:
        return
    if len(v) != 14 or len(set(v)) == 1:
        raise ValidationError(_("CNPJ inválido."))
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6] + pesos1
    def dv(nums, pesos):
        s = sum(int(n)*p for n,p in zip(nums, pesos))
        r = s % 11
        return '0' if r < 2 else str(11 - r)
    if v[12] != dv(v[:12], pesos1) or v[13] != dv(v[:13], pesos2):
        raise ValidationError(_("CNPJ inválido."))

cep_validator = RegexValidator(
    regex=r'^\d{5}-?\d{3}$',
    message=_("CEP deve ser 00000-000 ou 00000000.")
)
phone_validator = RegexValidator(
    regex=r'^\+?\d{10,15}$',
    message=_("Telefone deve conter apenas dígitos (DDI opcional), ex: +5511999999999.")
)
ie_validator = RegexValidator(regex=r'^[0-9A-Za-z\.-/]*$', message=_("IE inválida."))
rg_validator = RegexValidator(regex=r'^[0-9A-Za-z\.-/]*$', message=_("RG inválido."))

# --- Choices ---
class PersonKind(models.TextChoices):
    FISICA = 'F', _("Física")
    JURIDICA = 'J', _("Jurídica")

class ContactStatus(models.TextChoices):
    ATIVO = 'AT', _("Ativo")
    INATIVO = 'IN', _("Inativo")
    EXCLUIDO = 'EX', _("Excluído (soft-delete)")
    SEM_MOV = 'SM', _("Sem movimentação")

# --- Categorias dinâmicas ---
class Category(models.Model):
    name = models.CharField(_("Nome"), max_length=100, unique=True)
    slug = models.SlugField(_("Slug"), max_length=120, unique=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        verbose_name = _("Categoria de pessoa")
        verbose_name_plural = _("Categorias de pessoas")
        ordering = ["name"]

    def __str__(self):
        return self.name

# --- Contato ---
class Contact(models.Model):
    # papéis
    is_cliente = models.BooleanField(default=False, verbose_name=_("Cliente"))
    is_fornecedor = models.BooleanField(default=False, verbose_name=_("Fornecedor"))
    is_colaborador = models.BooleanField(default=False, verbose_name=_("Colaborador"))
    is_parceiro = models.BooleanField(default=False, verbose_name=_("Parceiro"))

    categories = models.ManyToManyField(
        Category, blank=True, related_name="contacts", verbose_name=_("Categorias")
    )

    person_kind = models.CharField(
        _("Tipo de pessoa"), max_length=1, choices=PersonKind.choices, blank=True
    )

    name = models.CharField(_("Nome / Razão social"), max_length=200, blank=True)
    fantasy_name = models.CharField(_("Nome fantasia"), max_length=200, blank=True)

    # documentos (todos opcionais, mas validados se informados)
    cpf = models.CharField(_("CPF"), max_length=14, blank=True, validators=[validate_cpf])
    cnpj = models.CharField(_("CNPJ"), max_length=18, blank=True, validators=[validate_cnpj])
    ie = models.CharField(_("Inscrição Estadual"), max_length=30, blank=True, validators=[ie_validator])
    ie_isento = models.BooleanField(_("IE Isento"), default=False)
    rg = models.CharField(_("RG"), max_length=30, blank=True, validators=[rg_validator])

    # contato
    email = models.EmailField(_("E-mail"), blank=True, validators=[EmailValidator()])
    phone = models.CharField(_("Telefone principal"), max_length=16, blank=True, validators=[phone_validator])
    phone_alt = models.CharField(_("Telefone alternativo"), max_length=16, blank=True, validators=[phone_validator])

    # status/observações
    status = models.CharField(_("Status"), max_length=2, choices=ContactStatus.choices, default=ContactStatus.ATIVO)
    notes = models.TextField(_("Observações"), blank=True)

    # auditoria / soft-delete
    is_deleted = models.BooleanField(default=False, help_text=_("Soft-delete para lixeira."))
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Contato")
        verbose_name_plural = _("Contatos")
        ordering = ["-created_at", "name"]

    def __str__(self):
        return self.name or (self.cnpj or self.cpf) or str(self.pk)

# --- Endereço (múltiplos por contato) ---
class Address(models.Model):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(_("Rótulo"), max_length=60, blank=True, help_text=_("Ex.: Cobrança, Entrega, Matriz..."))
    cep = models.CharField(_("CEP"), max_length=9, blank=True, validators=[cep_validator])
    street = models.CharField(_("Logradouro"), max_length=200, blank=True)
    number = models.CharField(_("Número"), max_length=20, blank=True)
    complement = models.CharField(_("Complemento"), max_length=100, blank=True)
    district = models.CharField(_("Bairro"), max_length=100, blank=True)
    city = models.CharField(_("Cidade"), max_length=100, blank=True)
    uf = models.CharField(_("UF"), max_length=2, blank=True)
    country = models.CharField(_("País"), max_length=60, blank=True, default="Brasil")

    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Endereço")
        verbose_name_plural = _("Endereços")
        ordering = ["contact", "label", "created_at"]

    def __str__(self):
        return f"{self.label or 'Endereço'} • {self.city or ''}/{self.uf or ''}"
