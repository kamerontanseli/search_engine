from django.conf.urls import url, include
from .views import *

urlpatterns = [
    url(r'^$', SearchFormView.as_view(), name="home"),
]