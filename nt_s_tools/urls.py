from django.conf.urls import url, include

urlpatterns = [
    url(r'^tools/api/', include('tools.urls')),
]
