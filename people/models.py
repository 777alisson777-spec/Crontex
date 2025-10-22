from django.db import models

class CollaboratorRole(models.Model):
    id = models.BigAutoField(primary_key=True)  # <— NOVO: id explícito p/ Pylance
    key = models.SlugField("Chave do papel", max_length=50, unique=True)
    label = models.CharField("Nome do papel", max_length=80)
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        ordering = ["label"]
        verbose_name = "Papel de colaborador"
        verbose_name_plural = "Papéis de colaborador"
        # Se vier migrando de catalog: db_table = "catalog_collaboratorrole"

    def __str__(self) -> str:
        return f"{self.label} ({self.key})"


class Collaborator(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField("Nome", max_length=150)
    role = models.ForeignKey(CollaboratorRole, verbose_name="Função", on_delete=models.PROTECT, related_name="collaborators")
    email = models.EmailField("E-mail", blank=True)
    phone = models.CharField("Telefone", max_length=50, blank=True)
    is_active = models.BooleanField("Ativo", default=True)

    class Meta:
        indexes = [models.Index(fields=["is_active", "name"])]
        ordering = ["name"]
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"
        # Se vier migrando de catalog: db_table = "catalog_collaborator"

    def __str__(self) -> str:
        return f"{self.name} · {self.role.label}"
