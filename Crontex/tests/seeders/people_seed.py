# tests/seeders/people_seed.py
# Cria contatos mínimos e tenta vincular "papel" via:
#  - FK:  Contact.category (slug|key|name)
#  - M2M: Contact.categories (slug|key|name)
#  - CharField: Contact.role
#
# Uso em pytest:
#   from tests.seeders.people_seed import seed_people_min
#   @pytest.mark.django_db
#   def test_algo():
#       seed_people_min()  # cria/garante os contatos
#
# Uso no shell:
#   python manage.py shell
#   >>> from tests.seeders.people_seed import seed_people_min
#   >>> seed_people_min()

from django.db import transaction

def _role_binding_info(Contact):
    """Descobre como 'role' pode ser vinculado ao Contact."""
    # FK "category"
    if hasattr(Contact, 'category'):
        rel = Contact.category.field
        mdl = rel.related_model
        if mdl:
            fields = [f for f in ('slug','key','name') if hasattr(mdl, f)]
            if fields:
                return {"mode":"fk","model":mdl,"field":"category","fields":fields}
    # M2M "categories"
    if hasattr(Contact, 'categories'):
        rel = Contact._meta.get_field('categories')
        mdl = rel.remote_field.model
        if mdl:
            fields = [f for f in ('slug','key','name') if hasattr(mdl, f)]
            if fields:
                return {"mode":"m2m","model":mdl,"field":"categories","fields":fields}
    # Fallback: CharField "role"
    if hasattr(Contact, 'role'):
        return {"mode":"char","model":None,"field":"role","fields":[]}
    return {"mode":None,"model":None,"field":None,"fields":[]}

def _get_or_create_role_obj(info, role_key: str):
    """Cria/obtém objeto de categoria (quando existir tabela relacionada)."""
    if not info["model"]:
        return None
    mdl = info["model"]
    key_norm = (role_key or "").strip().lower()

    # tenta achar por qualquer campo suportado
    for f in info["fields"]:
        found = mdl.objects.filter(**{f"{f}__iexact": key_norm}).first()
        if found:
            return found

    # cria com melhor combinação possível
    kwargs = {}
    if 'name' in info["fields"]:
        kwargs['name'] = role_key.upper()
    if 'slug' in info["fields"]:
        kwargs['slug'] = key_norm
    if 'key' in info["fields"]:
        kwargs['key'] = key_norm
    return mdl.objects.create(**kwargs)

def _attach_role(Contact, contact, role_key: str):
    """Vincula o papel ao contato conforme o esquema detectado."""
    info = _role_binding_info(Contact)
    if info["mode"] == "fk":
        obj = _get_or_create_role_obj(info, role_key)
        contact.category = obj
        contact.save(update_fields=['category'])
        return
    if info["mode"] == "m2m":
        obj = _get_or_create_role_obj(info, role_key)
        contact.save()  # garante PK
        getattr(contact, 'categories').add(obj)
        return
    if info["mode"] == "char":
        contact.role = role_key.upper()
        contact.save(update_fields=['role'])
        return
    # sem suporte: ignora (a busca funcionará sem filtro)

@transaction.atomic
def seed_people_min():
    """Cria contatos mínimos para testar autocomplete por papel."""
    from people.models import Contact  # import local para evitar custos em test discovery

    dataset = [
        {"name": "Ana Reqs",   "email": "ana@example.com",   "role": "REQUISITANTE"},
        {"name": "Bruno Reqs", "email": "bruno@example.com", "role": "REQUISITANTE"},
        {"name": "Carla Cli",  "email": "carla@example.com", "role": "CLIENTE"},
        {"name": "Diego Cli",  "email": "diego@example.com", "role": "CLIENTE"},
    ]

    created = 0
    for row in dataset:
        obj, was_created = Contact.objects.get_or_create(
            name=row["name"],
            defaults={"email": row.get("email","")}
        )
        _attach_role(Contact, obj, row["role"])
        if was_created:
            created += 1
    return created
