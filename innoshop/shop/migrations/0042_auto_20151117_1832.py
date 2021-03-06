# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models, migrations


def up(apps, schema_editor):
    Store = apps.get_model("shop", "Store")
    store = Store(name="Coffee")
    store.save()

    Category = apps.get_model("shop", "Category")
    Category(name="Кофе, чай, какао", store=store).save()
    Category(name="Шоколад, печенье", store=store).save()
    Category(name="Сиропы, дополнительные вкусности", store=store).save()


def down():
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('shop', '0041_auto_20151117_1730'),
    ]

    operations = [
        migrations.RunPython(up, down),
    ]
