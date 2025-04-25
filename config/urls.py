from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # namespace="app_mailing" это заданное пространство имен в "app_mailing/urls.py" с помощью "CatalogConfig.name"
    path("mailing/", include("app_mailing.urls", namespace="app_mailing")),
    path("users/", include("users.urls", namespace="users"))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
