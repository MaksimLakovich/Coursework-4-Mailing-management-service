from django.contrib import messages
from django.urls import reverse_lazy
from django.views import generic

from app_mailing.forms import AddNewRecipientForm, AddNewMessageForm, AddNewMailingForm
from app_mailing.models import Recipient, Message, Mailing


# 1. Контроллеры для "Управление клиентами"


class RecipientListView(generic.ListView):
    """Представление для отображения списка Получателей рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient/recipient_list.html"
    context_object_name = "recipients"


class RecipientCreateView(generic.CreateView):
    """Представление для добавления нового Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном добавлении нового Получателя в список рассылки."""
        messages.success(self.request, "Новый получатель успешно добавлен.")
        return super().form_valid(form)


class RecipientUpdateView(generic.UpdateView):
    """Представление для редактирования существующего Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном редактировании данных Получателя из списка рассылки."""
        recipient = self.get_object()
        messages.success(self.request, f"Вы успешно обновили данные клиента: {recipient.email}")
        return super().form_valid(form)


class RecipientDeleteView(generic.DeleteView):
    """Представление для удаления Получателя рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient/recipient_delete.html"
    context_object_name = "recipient"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном удалении Получателя из списка рассылки."""
        recipient = self.get_object()
        messages.success(self.request, f"Вы удалили клиента: {recipient.email}")
        return super().form_valid(form)


# 2. Контроллеры для "Управление сообщениями"


class MessageListView(generic.ListView):
    """Представление для отображения списка Сообщений для рассылок."""

    model = Message
    template_name = "app_mailing/message/message_list.html"
    context_object_name = "app_messages"


class MessageCreateView(generic.CreateView):
    """Представление для добавления нового Сообщения рассылки в список."""

    model = Message
    form_class = AddNewMessageForm
    template_name = "app_mailing/message/message_add_update.html"
    success_url = reverse_lazy("app_mailing:message_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном добавлении нового Сообщения в список рассылки."""
        messages.success(self.request, "Новое сообщение успешно добавлено.")
        return super().form_valid(form)


class MessageUpdateView(generic.UpdateView):
    """Представление для редактирования существующего Сообщения рассылки."""

    model = Message
    form_class = AddNewMessageForm
    template_name = "app_mailing/message/message_add_update.html"
    success_url = reverse_lazy("app_mailing:message_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном редактировании данных Сообщения из списка рассылки."""
        messages.success(self.request, "Вы успешно обновили данные сообщения")
        return super().form_valid(form)


class MessageDeleteView(generic.DeleteView):
    """Представление для удаления Сообщения рассылки."""

    model = Message
    template_name = "app_mailing/message/message_delete.html"
    context_object_name = "app_message"
    success_url = reverse_lazy("app_mailing:message_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном удалении Сообщения из списка рассылки."""
        messages.success(self.request, "Вы удалили сообщение")
        return super().form_valid(form)


# 3. Контроллеры для "Управление рассылками"


class MailingListView(generic.ListView):
    """Представление для отображения списка Рассылок."""

    model = Mailing
    template_name = "app_mailing/mailing/mailing_list.html"
    context_object_name = "mailings"


class MailingCreateView(generic.CreateView):
    """Представление для добавления новой Рассылки в список."""

    model = Mailing
    form_class = AddNewMailingForm
    template_name = "app_mailing/mailing/mailing_add_update.html"
    success_url = reverse_lazy("app_mailing:mailing_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном добавлении новой Рассылки в список."""
        messages.success(self.request, "Новая рассылка успешно добавлена.")
        return super().form_valid(form)
