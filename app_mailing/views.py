from django.contrib import messages
from django.urls import reverse_lazy
from django.views import generic

from app_mailing.forms import AddNewRecipientForm, AddNewMessageForm
from app_mailing.models import Recipient, Message


class RecipientListView(generic.ListView):
    """Представление для отображения списка Получателей рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient_list.html"
    context_object_name = "recipients"


class RecipientCreateView(generic.CreateView):
    """Представление для добавления нового Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном добавлении нового Получателя в список рассылки."""
        messages.success(self.request, "Новый получатель успешно добавлен.")
        return super().form_valid(form)


class RecipientUpdateView(generic.UpdateView):
    """Представление для редактирования существующего Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном редактировании данных Получателя из списка рассылки."""
        recipient = self.get_object()
        messages.success(self.request, f"Вы успешно обновили данные клиента: {recipient.email}")
        return super().form_valid(form)


class RecipientDeleteView(generic.DeleteView):
    """Представление для удаления Получателя рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient_delete.html"
    context_object_name = "recipient"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном удалении Получателя из списка рассылки."""
        recipient = self.get_object()
        messages.success(self.request, f"Вы удалили клиента: {recipient.email}")
        return super().form_valid(form)


class MessageListView(generic.ListView):
    """Представление для отображения списка Сообщений для рассылок."""

    model = Message
    template_name = "app_mailing/message_list.html"
    context_object_name = "app_messages"


class MessageCreateView(generic.CreateView):
    """Представление для добавления нового Сообщения рассылки в список."""

    model = Message
    form_class = AddNewMessageForm
    template_name = "app_mailing/message_add_update.html"
    success_url = reverse_lazy("app_mailing:message_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном добавлении нового Сообщения в список рассылки."""
        messages.success(self.request, "Новое сообщение успешно добавлено.")
        return super().form_valid(form)


# class RecipientUpdateView(generic.UpdateView):
#     """Представление для редактирования существующего Получателя рассылки."""
#
#     model = Recipient
#     form_class = AddNewRecipientForm
#     template_name = "app_mailing/recipient_add_update.html"
#     success_url = reverse_lazy("app_mailing:recipient_list_page")
#
#     def form_valid(self, form):
#         """Отправка пользователю уведомления об успешном редактировании данных Получателя из списка рассылки."""
#         recipient = self.get_object()
#         messages.success(self.request, f"Вы успешно обновили данные клиента: {recipient.email}")
#         return super().form_valid(form)
#
#
# class RecipientDeleteView(generic.DeleteView):
#     """Представление для удаления Получателя рассылки."""
#
#     model = Recipient
#     template_name = "app_mailing/recipient_delete.html"
#     context_object_name = "recipient"
#     success_url = reverse_lazy("app_mailing:recipient_list_page")
#
#     def form_valid(self, form):
#         """Отправка пользователю уведомления об успешном удалении Получателя из списка рассылки."""
#         recipient = self.get_object()
#         messages.success(self.request, f"Вы удалили клиента: {recipient.email}")
#         return super().form_valid(form)
