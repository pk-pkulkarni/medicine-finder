from django.urls import path

from . import views

urlpatterns = [
    path("patients/", views.patients, name="patients"),
    path("documents/", views.documents, name="documents"),
    path("documents/<int:document_id>/", views.document_detail, name="document-detail"),
    path("documents/<int:document_id>/file/", views.document_file, name="document-file"),
    path("search/", views.search, name="search"),
]
