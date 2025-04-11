from django.contrib import admin

from app_mailing.models import Mailing, Message, Recipient


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    """Настройка отображения данных "Получатель рассылки" в админке (модель *Recipient*)."""
    list_display = ("id", "email", "full_name", "comment",)
    list_filter = ("email", "full_name",)
    search_fields = ("email", "full_name",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Настройка отображения данных "Сообщение рассылки" в админке (модель *Message*)."""
    list_display = ("id", "message_subject", "message_body",)
    list_filter = ("message_subject",)
    search_fields = ("message_subject", "message_body",)


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    """Настройка отображения данных "Рассылка" в админке (модель *Mailing*)."""
    list_display = ("id", "first_message_sending", "end_message_sending", "status", "message",)
    list_filter = ("first_message_sending", "end_message_sending", "status", "message",)
    search_fields = ("first_message_sending", "end_message_sending", "status", "message",)
