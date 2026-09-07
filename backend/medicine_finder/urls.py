from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path, re_path
from django.views.generic import TemplateView
from django.views.static import serve

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("api/", include("records.urls")),
    re_path(r"^src/(?P<path>.*)$", serve, {"document_root": settings.ROOT_DIR / "src"}),
    path(".well-known/assetlinks.json", serve, {"document_root": settings.ROOT_DIR / ".well-known", "path": "assetlinks.json"}),
    path("manifest.webmanifest", serve, {"document_root": settings.ROOT_DIR, "path": "manifest.webmanifest"}),
    path("sw.js", serve, {"document_root": settings.ROOT_DIR, "path": "sw.js"}),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
