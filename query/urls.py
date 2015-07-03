from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='search'),
    url(r'^display/(?P<pageId>\S+)/$', views.display, name='display'),
    url(r'^page/(?P<pageNum>\S+)/$', views.page, name='page')
]