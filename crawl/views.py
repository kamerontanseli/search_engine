from django.shortcuts import render
from django.views.generic import TemplateView
from .crawl import Searcher
from .models import *
# Create your views here.

s = Searcher()

class SearchFormView(TemplateView):
    template_name = "crawl/search.html"
    def get_context_data(self, **kwargs):
        ctx = super(SearchFormView, self).get_context_data(**kwargs)

        if "query" in self.request.GET:
            ctx["results"] = s.query(self.request.GET["query"])
            ctx["results"] = [ UrlList.objects.get(id=row[1]) for row in ctx["results"] ]
        return ctx

