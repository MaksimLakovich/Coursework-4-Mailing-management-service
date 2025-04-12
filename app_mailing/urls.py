from django.urls import path

from app_mailing.apps import AppMailingConfig

from . import views

app_name = AppMailingConfig.name

urlpatterns = [
    path("recipients/", views.RecipientListView.as_view(), name="recipient_list_page"),
    path("recipients/add/", views.RecipientCreateView.as_view(), name="recipient_add_page"),
    path("recipients/<int:pk>/update/", views.RecipientUpdateView.as_view(), name="recipient_update_page"),
    path("recipients/<int:pk>/delete/", views.RecipientDeleteView.as_view(), name="recipient_delete_page"),
    path("messages/", views.MessageListView.as_view(), name="message_list_page"),
    path("messages/add/", views.MessageCreateView.as_view(), name="message_add_page"),
    # path("contacts/", views.CatalogContactsView.as_view(), name="contacts_page"),
    # path("product/<int:pk>/publication/", views.CatalogPublicationView.as_view(), name="product_publication"),
    # path("unpublished_products/", views.CatalogUnpublishedListView.as_view(), name="unpublished_products_page"),
]
