# people/views.py
from __future__ import annotations

import csv
import io
from typing import Any, Optional, cast, Iterable
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import ContactForm, build_address_formset, ContactImportForm
from .models import Contact, ContactStatus, Category  # Category deve existir no seu models (M2M de Contact)


def ping(request: HttpRequest) -> HttpResponse:
    return HttpResponse("people app: OK")

def index(request: HttpRequest) -> HttpResponse:
    return HttpResponse("people index")


class StaffRequiredMixin(UserPassesTestMixin):
    request_typed: HttpRequest
    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        self.request_typed = request
        return super().dispatch(request, *args, **kwargs)
    def test_func(self) -> bool:
        u = self.request_typed.user
        return u.is_authenticated and (u.is_staff or u.is_superuser)


class ContactListView(LoginRequiredMixin, ListView):
    model = Contact
    template_name = "people/contact_list.html"
    context_object_name = "contacts"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[Contact]:
        qs: QuerySet[Contact] = Contact.objects.filter(is_deleted=False).order_by("-created_at")
        q = (self.request.GET.get("q") or "").strip()
        status = (self.request.GET.get("status") or "").strip()

        # papéis via checkboxes (roles[] = cliente|fornecedor|colaborador|parceiro)
        roles: list[str] = self.request.GET.getlist("roles")

        # categorias via multiselect (categories[]=id)
        cat_ids: list[str] = [cid for cid in self.request.GET.getlist("categories") if cid.isdigit()]

        if q:
            qs = qs.filter(
                Q(name__icontains=q)
                | Q(email__icontains=q)
                | Q(cnpj__icontains=q)
                | Q(cpf__icontains=q)
            )

        if status in dict(ContactStatus.choices):
            qs = qs.filter(status=status)

        # Filtros de papéis (todos que vierem marcados)
        role_map = {
            "cliente": "is_cliente",
            "fornecedor": "is_fornecedor",
            "colaborador": "is_colaborador",
            "parceiro": "is_parceiro",
        }
        for r in roles:
            field = role_map.get(r)
            if field:
                qs = qs.filter(**{field: True})

        if cat_ids:
            qs = qs.filter(categories__in=cat_ids).distinct()

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["status_choices"] = ContactStatus.choices
        ctx["all_categories"] = Category.objects.order_by("name")
        ctx["selected_roles"] = set(self.request.GET.getlist("roles"))
        ctx["selected_categories"] = set(self.request.GET.getlist("categories"))
        return ctx


class ContactCreateView(StaffRequiredMixin, CreateView):
    model = Contact
    form_class = ContactForm
    template_name = "people/contact_form.html"
    success_url = reverse_lazy("people:list")

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        formset = build_address_formset(prefix="addr")
        return render(request, self.template_name, {"form": form, "formset": formset})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        form = self.get_form()
        formset = build_address_formset(data=request.POST, prefix="addr")
        if form.is_valid() and formset.is_valid():
            obj = cast(Contact, form.save())
            formset.instance = obj
            formset.save()
            messages.success(request, "Contato criado com sucesso.")
            return redirect(self.success_url)
        messages.error(request, "Não foi possível salvar. Verifique os campos destacados.")
        return render(request, self.template_name, {"form": form, "formset": formset})


class ContactUpdateView(StaffRequiredMixin, UpdateView):
    model = Contact
    form_class = ContactForm
    template_name = "people/contact_form.html"
    success_url = reverse_lazy("people:list")

    def get_object(self, queryset: Optional[QuerySet[Contact]] = None) -> Contact:
        return cast(Contact, super().get_object(queryset))

    def get(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        obj: Contact = self.get_object()
        form = self.get_form()
        formset = build_address_formset(instance=obj, prefix="addr")
        return render(request, self.template_name, {"form": form, "formset": formset, "object": obj})

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        obj: Contact = self.get_object()
        form = self.get_form()
        formset = build_address_formset(data=request.POST, instance=obj, prefix="addr")
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Contato atualizado com sucesso.")
            return redirect(self.success_url)
        messages.error(request, "Não foi possível atualizar. Verifique os campos destacados.")
        return render(request, self.template_name, {"form": form, "formset": formset, "object": obj})


class ContactDetailView(LoginRequiredMixin, DetailView):
    model = Contact
    template_name = "people/contact_detail.html"
    context_object_name = "contact"


class ContactDeleteView(StaffRequiredMixin, DeleteView):
    model = Contact
    template_name = "people/contact_confirm_delete.html"
    success_url = reverse_lazy("people:list")

    def get_object(self, queryset: Optional[QuerySet[Contact]] = None) -> Contact:
        return cast(Contact, super().get_object(queryset))

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        obj: Contact = self.get_object()
        obj.is_deleted = True
        obj.status = ContactStatus.EXCLUIDO
        obj.save(update_fields=["is_deleted", "status"])
        messages.warning(request, f'Contato "{obj.name or obj.pk}" excluído (soft-delete).')
        return redirect(self.success_url)


# ---------- CSV: export ----------
def export_contacts_csv(request: HttpRequest) -> HttpResponse:
    """
    Exporta contatos (sem endereços) em ; (Excel-friendly). Se ?bom=1, inclui BOM UTF-8.
    """
    qs = Contact.objects.filter(is_deleted=False).order_by("name")
    delimiter = ";"
    add_bom = request.GET.get("bom") == "1"

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter)
    writer.writerow(["id","name","person_kind","email","phone","cpf","cnpj","status","roles","categories"])
    for c in qs:
        roles = ",".join([r for r, flag in {
            "cliente": c.is_cliente,
            "fornecedor": c.is_fornecedor,
            "colaborador": c.is_colaborador,
            "parceiro": c.is_parceiro,
        }.items() if flag])
        cats = ",".join(c.categories.values_list("name", flat=True))
        writer.writerow([c.id, c.name, c.person_kind, c.email, c.phone, c.cpf, c.cnpj, c.status, roles, cats])

    data = buf.getvalue()
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    if add_bom:
        resp.write("\ufeff")  # BOM
    resp.write(data)
    resp["Content-Disposition"] = 'attachment; filename="contatos.csv"'
    return resp


# ---------- CSV: template ----------
def download_import_template(request: HttpRequest) -> HttpResponse:
    """
    Baixa um CSV modelo para importação.
    """
    delimiter = ";"
    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=delimiter)
    writer.writerow([
        "name","person_kind","email","phone","cpf","cnpj",
        "roles (cliente|fornecedor|colaborador|parceiro separados por ,)",
        "categories (nomes separados por ,)"
    ])
    writer.writerow(["Ex.: Padaria do João","JURIDICA","contato@padaria.com","11999999999","","12345678000190","cliente,fornecedor","Alimentação,Varejo"])
    data = buf.getvalue()
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp.write("\ufeff")  # BOM para Excel
    resp.write(data)
    resp["Content-Disposition"] = 'attachment; filename="contatos_import_template.csv"'
    return resp


# ---------- CSV: import ----------
def _detect_delimiter(sample: str) -> str:
    return ";" if sample.count(";") >= sample.count(",") else ","

def _to_bool_roles(tokens: Iterable[str]) -> dict[str, bool]:
    t = {x.strip().lower() for x in tokens if x.strip()}
    return {
        "is_cliente": "cliente" in t,
        "is_fornecedor": "fornecedor" in t,
        "is_colaborador": "colaborador" in t,
        "is_parceiro": "parceiro" in t,
    }

def import_contacts_view(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        form = ContactImportForm()
        return render(request, "people/contact_import.html", {"form": form})

    # POST
    form = ContactImportForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, "Arquivo inválido.")
        return render(request, "people/contact_import.html", {"form": form})

    f = form.cleaned_data["file"]
    raw = f.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            text = raw.decode("latin1")
        except Exception:
            messages.error(request, "Não foi possível decodificar o arquivo (UTF-8 ou Latin-1).")
            return render(request, "people/contact_import.html", {"form": form})

    if not text.strip():
        messages.error(request, "Arquivo vazio.")
        return render(request, "people/contact_import.html", {"form": form})

    delim = _detect_delimiter(text.splitlines()[0])
    reader = csv.DictReader(io.StringIO(text), delimiter=delim)
    created, updated, errors = 0, 0, 0
    for i, row in enumerate(reader, start=2):  # header na linha 1
        try:
            name = (row.get("name") or "").strip()
            if not name:
                # MVP: pula linhas sem nome
                continue

            person_kind = (row.get("person_kind") or "").strip().upper() or None
            email = (row.get("email") or "").strip() or None
            phone = (row.get("phone") or "").strip() or None
            cpf = (row.get("cpf") or "").strip() or None
            cnpj = (row.get("cnpj") or "").strip() or None

            roles_tokens = (row.get("roles (cliente|fornecedor|colaborador|parceiro separados por ,)") or "").split(",")
            roles = _to_bool_roles(roles_tokens)

            cat_names = [x.strip() for x in (row.get("categories (nomes separados por ,)") or "").split(",") if x.strip()]

            obj, created_flag = Contact.objects.get_or_create(
                name=name,
                defaults={
                    "person_kind": person_kind,
                    "email": email,
                    "phone": phone,
                    "cpf": cpf,
                    "cnpj": cnpj,
                    **roles,
                },
            )
            if not created_flag:
                # Atualiza campos básicos se vierem preenchidos
                for field, val in {
                    "person_kind": person_kind,
                    "email": email,
                    "phone": phone,
                    "cpf": cpf,
                    "cnpj": cnpj,
                    **roles,
                }.items():
                    if val not in (None, ""):
                        setattr(obj, field, val)
                obj.save()
                updated += 1
            else:
                created += 1

            # Categorias por nome (cria se não existir)
            if cat_names:
                cat_objs = []
                for cn in cat_names:
                    cobj, _ = Category.objects.get_or_create(name=cn)
                    cat_objs.append(cobj)
                obj.categories.set(cat_objs)  # substitui conjunto
        except Exception as exc:
            errors += 1
            # Logaria erro linha a linha; por ora só segue.
            continue

    if errors:
        messages.warning(request, f"Importação concluída: {created} criados, {updated} atualizados, {errors} linhas com erro.")
    else:
        messages.success(request, f"Importação concluída: {created} criados, {updated} atualizados.")

    return redirect("people:list")

# --- [ADICIONAR AO FINAL DE people/views.py] ---------------------------------
# Mini-API de autocomplete para integrar com o módulo catalog (texto + hidden id).
# Rotas já mapeadas em people/urls.py como:
#   - name="api_search" -> /people/api/search/
#   - name="api_get"    -> /people/api/get/

from django.http import JsonResponse
from django.db.models import Q
from django.views.decorators.http import require_GET

from .models import Contact  # usa seu model real

def _safe_int(val, default=1):
    """
    Converte para int positivo; cai no default em caso de erro.
    """
    try:
        i = int(val)
        return i if i > 0 else default
    except Exception:
        return default

# people/views.py  — SUBSTITUIR SOMENTE ESTA FUNÇÃO

@require_GET
def contact_search_api(request):
    """
    GET /people/api/search/?q=<termo>&page=1&page_size=20[&type=supplier][&role=CLIENTE]

    - 'q'     : termo de busca (name/email/phone, se existirem)
    - 'page'  : página (1-based)
    - 'type'  : filtro opcional por Contact.type (se o model tiver esse campo)
    - 'role'  : filtro compatível com seu front (data-role); tenta filtrar por:
                * FK   : category.slug | category.key | category.name
                * M2M  : categories.slug | categories.key | categories.name
                * Char : role (campo texto simples)
              Se nada disso existir no model, o filtro é ignorado (retorna todos).
    Retorna:
      {
        "results": [{"id":<int>,"text":"Nome","subtitle":"email/phone"}],
        "pagination": {"more": <bool>}
      }
    """
    q = (request.GET.get('q') or '').strip()
    page = _safe_int(request.GET.get('page'), 1)
    page_size = min(_safe_int(request.GET.get('page_size'), 20), 50)
    ctype = (request.GET.get('type') or '').strip().lower()
    role  = (request.GET.get('role') or '').strip()

    qs = Contact.objects.all().order_by('name')

    # --- filtro por 'type' (se existir no model) ---
    if ctype and hasattr(Contact, 'type'):
        qs = qs.filter(type=ctype)

    # --- filtro por 'role' (compat com seu front) ---
    if role:
        role_norm = role.strip().lower()

        # 1) FK 'category'
        if hasattr(Contact, 'category'):
            rel = Contact.category.field
            mdl = rel.related_model
            if hasattr(mdl, 'slug'):
                qs = qs.filter(category__slug__iexact=role_norm)
            elif hasattr(mdl, 'key'):
                qs = qs.filter(category__key__iexact=role_norm)
            elif hasattr(mdl, 'name'):
                qs = qs.filter(category__name__iexact=role_norm)

        # 2) M2M 'categories'
        elif hasattr(Contact, 'categories'):
            rel = Contact._meta.get_field('categories')
            mdl = rel.remote_field.model
            if hasattr(mdl, 'slug'):
                qs = qs.filter(categories__slug__iexact=role_norm)
            elif hasattr(mdl, 'key'):
                qs = qs.filter(categories__key__iexact=role_norm)
            elif hasattr(mdl, 'name'):
                qs = qs.filter(categories__name__iexact=role_norm)

        # 3) CharField simples 'role'
        elif hasattr(Contact, 'role'):
            qs = qs.filter(role__iexact=role)

    # --- busca textual básica ---
    if q:
        name_field = 'name'
        email_field = 'email' if hasattr(Contact, 'email') else None
        phone_field = 'phone' if hasattr(Contact, 'phone') else None

        filt = Q(**{f"{name_field}__icontains": q})
        if email_field:
            filt |= Q(**{f"{email_field}__icontains": q})
        if phone_field:
            filt |= Q(**{f"{phone_field}__icontains": q})
        qs = qs.filter(filt)

    # --- paginação ---
    start = (page - 1) * page_size
    end = start + page_size
    total = qs.count()

    results = []
    for c in qs[start:end]:
        subtitle = ''
        if hasattr(c, 'email') and getattr(c, 'email', ''):
            subtitle = c.email
        elif hasattr(c, 'phone') and getattr(c, 'phone', ''):
            subtitle = c.phone

        results.append({
            "id": c.pk,
            "text": getattr(c, 'name', str(c)),
            "subtitle": subtitle,
        })

    return JsonResponse({
        "results": results,
        "pagination": {"more": total > end}
    })


@require_GET
def contact_get_api(request):
    """
    GET /people/api/get/?id=<pk>
    Retorna dados mínimos para hidratar o rótulo do campo quando já existe um ID salvo.
    {
      "id": 1, "text": "Nome", "subtitle": "email/phone"
    }
    """
    cid = _safe_int(request.GET.get('id'), 0)
    if not cid:
        return JsonResponse({"detail": "Missing id"}, status=400)

    try:
        c = Contact.objects.get(pk=cid)
    except Contact.DoesNotExist:
        return JsonResponse({"detail": "Not Found"}, status=404)

    subtitle = ''
    if hasattr(c, 'email') and getattr(c, 'email', ''):
        subtitle = c.email
    elif hasattr(c, 'phone') and getattr(c, 'phone', ''):
        subtitle = c.phone

    return JsonResponse({
        "id": c.pk,
        "text": getattr(c, 'name', str(c)),
        "subtitle": subtitle,
    })
# --- [FIM DAS ADIÇÕES] -------------------------------------------------------

