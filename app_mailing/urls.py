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
    path("messages/<int:pk>/update/", views.MessageUpdateView.as_view(), name="message_update_page"),
    path("messages/<int:pk>/delete/", views.MessageDeleteView.as_view(), name="message_delete_page"),
    path("mailings/", views.MailingListView.as_view(), name="mailing_list_page"),
    path("mailings/add/", views.MailingCreateView.as_view(), name="mailing_add_page"),
    path("mailings/<int:pk>/update/", views.MailingUpdateView.as_view(), name="mailing_update_page"),
    path("mailings/<int:pk>/delete/", views.MailingDeleteView.as_view(), name="mailing_delete_page"),
    path("start_mailing/<int:pk>/", views.SendMailingView.as_view(), name="start_mailing_page"),
]
