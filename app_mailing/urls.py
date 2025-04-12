from django.urls import path

from app_mailing.apps import AppMailingConfig

from . import views

app_name = AppMailingConfig.name

urlpatterns = [
    path("recipients/", views.RecipientListView.as_view(), name="recipient_list_page"),
    # path("product/<int:pk>/detail/", views.CatalogDetailView.as_view(), name="product_detail_page"),
    path("recipients/add/", views.RecipientCreateView.as_view(), name="recipient_form_add_page"),
    # path("product/<int:pk>/update/", views.CatalogUpdateView.as_view(), name="update_product_page"),
    # path("product/<int:pk>/delete/", views.CatalogDeleteView.as_view(), name="product_confirm_delete_page"),
    # path("contacts/", views.CatalogContactsView.as_view(), name="contacts_page"),
    # path("product/<int:pk>/publication/", views.CatalogPublicationView.as_view(), name="product_publication"),
    # path("unpublished_products/", views.CatalogUnpublishedListView.as_view(), name="unpublished_products_page"),
    # path("category_products/", views.CatalogCategoryProductsView.as_view(), name="category_products_page"),
    # path("category_products/<int:category_id>/", views.CatalogCategoryProductsView.as_view(), name="category_products_page"),
]
