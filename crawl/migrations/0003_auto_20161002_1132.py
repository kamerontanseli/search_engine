# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-10-02 11:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('crawl', '0002_auto_20161002_1129'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='link',
            unique_together=set([]),
        ),
    ]
