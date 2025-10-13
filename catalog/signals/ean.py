# -*- coding: utf-8 -*-
from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver

from catalog.models import ProductVariant
from catalog.validators.ean import validate_ean13, normalize_n_digits


@receiver(pre_save, sender=ProductVariant)
def validate_and_enforce_unique_ean(sender, instance: ProductVariant, **kwargs):
    ean = getattr(instance, "ean13", None)
    if not ean:
        return

    s = normalize_n_digits(ean, 13)
    if len(s) != 13:
        raise ValidationError({"ean13": "EAN-13 deve ter 13 dígitos numéricos."})
    try:
        validate_ean13(s)
    except ValidationError as exc:
        raise ValidationError({"ean13": exc.messages[0]})

    instance.ean13 = s

    qs = ProductVariant.objects.filter(ean13=s)
    if instance.pk:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise ValidationError({"ean13": "EAN-13 já cadastrado em outra variante."})
