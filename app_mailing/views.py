import os

from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from app_mailing.forms import AddNewMailingForm, AddNewMessageForm, AddNewRecipientForm
from app_mailing.models import Mailing, Message, Recipient


# 1. Контроллеры для "Управление клиентами"


class RecipientListView(generic.ListView):
    """Представление для отображения списка Получателей рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        """Сортировка по ФИО (в алфавитном порядке)."""
        return Recipient.objects.order_by("full_name")


class RecipientCreateView(generic.CreateView):
    """Представление для добавления нового Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном добавлении нового Получателя в список рассылки."""
        messages.success(self.request, "Новый получатель успешно добавлен")
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
        messages.success(self.request, "Новое сообщение успешно добавлено")
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

    def get_queryset(self):
        """Сортировка по статусу Рассылки: запущена → создана → завершена, внутри по дате окончания."""
        # Определяю порядок статусов
        status_order = {
            "launched": 0,
            "created": 1,
            "accomplished": 2,
        }

        all_mailings = Mailing.objects.all()

        def sort_key(mailing):
            # Получаю приоритет статуса (если статус не найден - ставлю 3, чтоб он был точно в самом конце списка)
            status_priority = status_order.get(mailing.status, 3)
            # Получаю timestamp окончания рассылки с преобразованием времени в секунды
            # для оптимизации процесса сравнения (если None - то ставлю 0)
            if mailing.end_message_sending:
                timestamp = mailing.end_message_sending.timestamp()
            else:
                timestamp = 0
            return (status_priority, -timestamp)  # Возвращаю кортеж: сначала статус, потом минус время (для убывания)

        # Сортирую с помощью созданного sort_key() и возвращаю отсортированный список
        sorted_mailings = sorted(all_mailings, key=sort_key)
        return sorted_mailings


class MailingCreateView(generic.CreateView):
    """Представление для добавления новой Рассылки в список."""

    model = Mailing
    form_class = AddNewMailingForm
    template_name = "app_mailing/mailing/mailing_add_update.html"
    success_url = reverse_lazy("app_mailing:mailing_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном добавлении новой Рассылки в список."""
        messages.success(self.request, "Новая рассылка успешно добавлена")
        return super().form_valid(form)


class MailingUpdateView(generic.UpdateView):
    """Представление для редактирования существующей Рассылки в списке."""

    model = Mailing
    form_class = AddNewMailingForm
    template_name = "app_mailing/mailing/mailing_add_update.html"
    success_url = reverse_lazy("app_mailing:mailing_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном редактировании данных Рассылки из списка."""
        messages.success(self.request, "Вы успешно обновили данные рассылки")
        return super().form_valid(form)


class MailingDeleteView(generic.DeleteView):
    """Представление для удаления Рассылки."""

    model = Mailing
    template_name = "app_mailing/mailing/mailing_delete.html"
    context_object_name = "mailing"
    success_url = reverse_lazy("app_mailing:mailing_list_page")

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном удалении Рассылки."""
        messages.success(self.request, "Вы удалили рассылку")
        return super().form_valid(form)


class SendMailingView(generic.View):
    """Представление для запуска выбранной пользователем Рассылки вручную через интерфейс."""

    def post(self, request, pk):
        """Отправка email всем получателям в выбранной Рассылке."""
        mailing = get_object_or_404(Mailing, pk=pk)

        if mailing.status != "created":
            messages.warning(request, "Эту рассылку нельзя повторно запустить.")
            return redirect("app_mailing:mailing_list_page")

        recipients = mailing.recipients.all()
        if not recipients.exists():
            messages.warning(request, "У этой рассылки нет получателей.")
            return redirect("app_mailing:mailing_list_page")

        subject = mailing.message.message_subject
        message = mailing.message.message_body
        from_email = os.getenv("YANDEX_EMAIL_HOST_USER")

        mailing.status = "launched"  # Меняю статус рассылки, что она запущена
        mailing.first_message_sending = timezone.now()  # Фиксирую дату начала
        mailing.save()

        success_count = 0

        for recipient in recipients:  # Запускаю рассылку по всем получателям
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                success_count += 1
            except Exception as e:
                print(f"Ошибка при отправке письма на {recipient.email}: {e}")

        mailing.end_message_sending = timezone.now()  # Фиксирую дату окончания
        mailing.status = "accomplished"  # Меняю статус рассылки после завершения
        mailing.save()

        messages.success(request, f"Рассылка успешно отправлена {success_count} получателям.")
        return redirect("app_mailing:mailing_list_page")
