# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-02 12:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('crawl', '0003_auto_20161002_1132'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wordlist',
            name='word',
            field=models.CharField(default='', max_length=256, unique=True),
            preserve_default=False,
        ),
    ]
