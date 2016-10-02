from __future__ import unicode_literals

from django.db import models

# Create your models here.

class UrlList(models.Model):
    url = models.URLField(unique=True, null=True)

class PageRank(models.Model):
    url = models.ForeignKey('UrlList', related_name="ranks")
    score = models.FloatField(default=1.0)

class WordList(models.Model):
    word = models.CharField(max_length=256, unique=True)

class WordLocation(models.Model):
    url = models.ForeignKey('UrlList', related_name="locations")
    word = models.ForeignKey('WordList', related_name="locations")
    location = models.CharField(max_length=256, null=True)

class Link(models.Model):
    source = models.ForeignKey('UrlList', related_name="links")
    to = models.ForeignKey('UrlList', related_name="links_from")

class LinkWord(models.Model):
    link = models.ForeignKey('Link', related_name="words")
    word = models.ForeignKey('WordList', related_name="links")

