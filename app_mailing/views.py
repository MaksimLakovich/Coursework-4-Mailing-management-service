from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from app_mailing.forms import (AddNewMailingForm, AddNewMessageForm,
                               AddNewRecipientForm)
from app_mailing.models import Attempt, Mailing, Message, Recipient
from app_mailing.services import send_mailing, stop_mailing

# 1. Контроллеры для "Управление клиентами"


class RecipientListView(LoginRequiredMixin, generic.ListView):
    """Представление для отображения списка Получателей рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient/recipient_list.html"
    context_object_name = "recipients"

    def get_queryset(self):
        """1) Сортировка по ФИО (в алфавитном порядке).
        2) Ограничение данных по owner, т.е. выводим только те данные, где user==owner.
        3) Если пользователь входит в группу 'Менеджер сервиса', то выводим абсолютно все данные из БД."""
        qs = Recipient.objects.all()

        # Если у пользователя НЕТ системного разрешения на просмотр всех объектов - показываем только его объекты.
        if not self.request.user.groups.filter(name="Менеджер сервиса").exists():
            qs = qs.filter(owner=self.request.user).order_by("full_name")
        # Иначе показываем все.
        return qs.order_by("full_name")


class RecipientCreateView(LoginRequiredMixin, generic.CreateView):
    """Представление для добавления нового Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def get_form_kwargs(self):
        """Метод для передачи в форму информации о текущем пользователе (владелец - owner), чтобы метод clean_email,
         который я добавил в самой форме (AddNewRecipientForm) мог корректно проверять уникальность email по владельцу.
         Без этого clean_email в форме (AddNewRecipientForm) не сможет определить, кому принадлежит объект."""
        kwargs = super().get_form_kwargs()
        kwargs["initial"] = {"owner": self.request.user}
        return kwargs

    def form_valid(self, form):
        """1) Отправка пользователю уведомления об успешном добавлении нового Получателя в список рассылки.
        2) Автоматическое заполнение текущим пользователем поля 'owner' при создании нового *Получателя рассылки*."""
        messages.success(self.request, "Новый получатель успешно добавлен")
        form.instance.owner = self.request.user  # Привязываю текущего пользователя как owner
        return super().form_valid(form)


class RecipientUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Представление для редактирования существующего Получателя рассылки."""

    model = Recipient
    form_class = AddNewRecipientForm
    template_name = "app_mailing/recipient/recipient_add_update.html"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def dispatch(self, request, *args, **kwargs):
        """Метод выполняет проверку прав пользователя на редактирование *Получателя рассылки* (создатель получателя),
        заранее до выполнения любого запроса (GET, POST и т.д.)."""
        recipient = get_object_or_404(Recipient, pk=self.kwargs["pk"])
        if not request.user == recipient.owner:
            return HttpResponseForbidden(
                f"У вас нет прав для редактирования Получателя рассылки. Обратитесь к владельцу: {recipient.owner}"
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном редактировании данных Получателя из списка рассылки."""
        recipient = self.get_object()
        messages.success(self.request, f"Вы успешно обновили данные клиента: {recipient.email}")
        return super().form_valid(form)


class RecipientDeleteView(LoginRequiredMixin, generic.DeleteView):
    """Представление для удаления Получателя рассылки."""

    model = Recipient
    template_name = "app_mailing/recipient/recipient_delete.html"
    context_object_name = "recipient"
    success_url = reverse_lazy("app_mailing:recipient_list_page")

    def dispatch(self, request, *args, **kwargs):
        """Метод выполняет проверку прав пользователя на удаление *Получателя рассылки* (создатель получателя),
        заранее до выполнения любого запроса (GET, POST и т.д.)."""
        recipient = get_object_or_404(Recipient, pk=self.kwargs["pk"])
        if not request.user == recipient.owner:
            return HttpResponseForbidden(
                f"У вас нет прав для удаления Получателя рассылки. Обратитесь к владельцу: {recipient.owner}"
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном удалении Получателя из списка рассылки."""
        recipient = self.get_object()
        messages.success(self.request, f"Вы удалили клиента: {recipient.email}")
        return super().form_valid(form)


# 2. Контроллеры для "Управление сообщениями"


class MessageListView(LoginRequiredMixin, generic.ListView):
    """Представление для отображения списка Сообщений для рассылок."""

    model = Message
    template_name = "app_mailing/message/message_list.html"
    context_object_name = "app_messages"

    def get_queryset(self):
        """Ограничение данных по owner, т.е. выводим только те данные, где user==owner."""
        return Message.objects.filter(owner=self.request.user)


class MessageCreateView(LoginRequiredMixin, generic.CreateView):
    """Представление для добавления нового Сообщения рассылки в список."""

    model = Message
    form_class = AddNewMessageForm
    template_name = "app_mailing/message/message_add_update.html"
    success_url = reverse_lazy("app_mailing:message_list_page")

    def form_valid(self, form):
        """1) Отправка пользователю уведомления об успешном добавлении нового Сообщения в список рассылки.
        2) Автоматическое заполнение текущим пользователем поля 'owner' при создании нового *Сообщения рассылки*."""
        messages.success(self.request, "Новое сообщение успешно добавлено")
        form.instance.owner = self.request.user  # Привязываю текущего пользователя как owner
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Представление для редактирования существующего Сообщения рассылки."""

    model = Message
    form_class = AddNewMessageForm
    template_name = "app_mailing/message/message_add_update.html"
    success_url = reverse_lazy("app_mailing:message_list_page")

    def dispatch(self, request, *args, **kwargs):
        """Метод выполняет проверку прав пользователя на редактирование *Сообщения рассылки* (создатель сообщения),
        заранее до выполнения любого запроса (GET, POST и т.д.)."""
        message = get_object_or_404(Message, pk=self.kwargs["pk"])
        if not request.user == message.owner:
            return HttpResponseForbidden(
                f"У вас нет прав для редактирования Сообщения рассылки. Обратитесь к владельцу: {message.owner}"
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном редактировании данных Сообщения из списка рассылки."""
        messages.success(self.request, "Вы успешно обновили данные сообщения")
        return super().form_valid(form)


class MessageDeleteView(LoginRequiredMixin, generic.DeleteView):
    """Представление для удаления Сообщения рассылки."""

    model = Message
    template_name = "app_mailing/message/message_delete.html"
    context_object_name = "app_message"
    success_url = reverse_lazy("app_mailing:message_list_page")

    def dispatch(self, request, *args, **kwargs):
        """Метод выполняет проверку прав пользователя на удаление *Сообщения рассылки* (создатель сообщения),
        заранее до выполнения любого запроса (GET, POST и т.д.)."""
        message = get_object_or_404(Message, pk=self.kwargs["pk"])
        if not request.user == message.owner:
            return HttpResponseForbidden(
                f"У вас нет прав для удаления Сообщения рассылки. Обратитесь к владельцу: {message.owner}"
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном удалении Сообщения из списка рассылки."""
        messages.success(self.request, "Вы удалили сообщение")
        return super().form_valid(form)


# 3. Контроллеры для "Управление рассылками"


class MailingListView(LoginRequiredMixin, generic.ListView):
    """Представление для отображения списка Рассылок."""

    model = Mailing
    template_name = "app_mailing/mailing/mailing_list.html"
    context_object_name = "mailings"

    def get_queryset(self):
        """1) Сортировка по статусу Рассылки: запущена → создана → завершена, внутри по дате окончания.
        2) Ограничение данных по owner, т.е. выводим только те данные, где user==owner.
        3) Если пользователь входит в группу 'Менеджер сервиса', то выводим абсолютно все данные из БД."""
        # Определяю порядок статусов
        status_order = {
            "launched": 0,
            "created": 1,
            "accomplished": 2,
        }

        # Получаю весь объем данных из БД
        qs = Mailing.objects.all()

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

        # Если у пользователя НЕТ системного разрешения на просмотр всех объектов - показываем только его объекты.
        if not self.request.user.groups.filter(name="Менеджер сервиса").exists():
            # 1) Выбираю с помощью фильтра данные, где пользователь является владельцем (owner=self.request.user)
            # 2) Сортирую с помощью созданного sort_key() и возвращаю отсортированный список
            sorted_mailings = sorted(qs.filter(owner=self.request.user), key=sort_key)
            return sorted_mailings
            # Иначе показываем все с сортировкой с помощью созданного sort_key()
        sorted_mailings = sorted(qs, key=sort_key)
        return sorted_mailings


class MailingCreateView(LoginRequiredMixin, generic.CreateView):
    """Представление для добавления новой Рассылки в список."""

    model = Mailing
    form_class = AddNewMailingForm
    template_name = "app_mailing/mailing/mailing_add_update.html"
    success_url = reverse_lazy("app_mailing:mailing_list_page")

    def get_form_kwargs(self):
        """Метод для передачи request.user в форму для дальнейшего ограничения выбора доступных объектов из БД
        в выпадающих списках формы *AddNewMailingForm* так, чтобы пользователи видели только свои объекты."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """1) Отправка пользователю уведомления об успешном добавлении новой Рассылки в список.
        2) Автоматическое заполнение текущим пользователем поля 'owner' при создании нового *Рассылки*."""
        messages.success(self.request, "Новая рассылка успешно добавлена")
        form.instance.owner = self.request.user  # Привязываю текущего пользователя как owner
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Представление для редактирования существующей Рассылки в списке."""

    model = Mailing
    form_class = AddNewMailingForm
    template_name = "app_mailing/mailing/mailing_add_update.html"
    success_url = reverse_lazy("app_mailing:mailing_list_page")

    def dispatch(self, request, *args, **kwargs):
        """Метод выполняет проверку прав пользователя на редактирование *Рассылки* (создатель рассылки),
        заранее до выполнения любого запроса (GET, POST и т.д.)."""
        mailing = get_object_or_404(Mailing, pk=self.kwargs["pk"])
        if not request.user == mailing.owner:
            return HttpResponseForbidden(
                f"У вас нет прав для редактирования Рассылки. Обратитесь к владельцу: {mailing.owner}"
            )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Метод для передачи request.user в форму для дальнейшего ограничения выбора доступных объектов из БД
        в выпадающих списках формы *AddNewMailingForm* так, чтобы пользователи видели только свои объекты."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном редактировании данных Рассылки из списка."""
        messages.success(self.request, "Вы успешно обновили данные рассылки")
        return super().form_valid(form)


class MailingDeleteView(LoginRequiredMixin, generic.DeleteView):
    """Представление для удаления Рассылки."""

    model = Mailing
    template_name = "app_mailing/mailing/mailing_delete.html"
    context_object_name = "mailing"
    success_url = reverse_lazy("app_mailing:mailing_list_page")

    def dispatch(self, request, *args, **kwargs):
        """Метод выполняет проверку прав пользователя на удаление *Рассылки* (создатель рассылки),
        заранее до выполнения любого запроса (GET, POST и т.д.)."""
        mailing = get_object_or_404(Mailing, pk=self.kwargs["pk"])
        if not request.user == mailing.owner:
            return HttpResponseForbidden(
                f"У вас нет прав для удаления Рассылки. Обратитесь к владельцу: {mailing.owner}"
            )
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Отправка пользователю уведомления об успешном удалении Рассылки."""
        messages.success(self.request, "Вы удалили рассылку")
        return super().form_valid(form)


class SendMailingView(LoginRequiredMixin, generic.View):
    """Представление для запуска выбранной пользователем *Рассылки* вручную через интерфейс
    и фиксации *Попыток рассылок* по каждому *Получателю* из рассылки."""

    def post(self, request, pk):
        """Метод запускает сервисную функцию *send_mailing()* из services.py, которая:
        1) Отправляет email всем получателям в выбранной *Рассылке*.
        2) Фиксирует *Попытки рассылок* по каждому получателю."""
        mailing = get_object_or_404(Mailing, pk=pk)
        send_mailing(request, mailing)
        return redirect("app_mailing:mailing_list_page")


class StopMailingView(LoginRequiredMixin, generic.View):
    """Представление для остановки выбранной пользователем *Рассылки* вручную через интерфейс
    и фиксации остановки *Попыток рассылок* по каждому *Получателю* из рассылки, которые еще не были отправлены."""

    def post(self, request, pk):
        """POST-запрос инициирует остановку рассылки:
        - Завершает рассылку.
        - Фиксирует "неудачные" попытки рассылки по оставшимся получателям.
        - Возвращает пользователя на список рассылок."""
        mailing = get_object_or_404(Mailing, pk=pk)

        if request.user != mailing.owner:
            return HttpResponseForbidden("Вы не можете останавливать чужую рассылку.")

        stop_mailing(mailing, reason="Пользователь вручную остановил рассылку")

        messages.success(request, "Рассылка была успешно остановлена.")
        return redirect("app_mailing:mailing_list_page")


# 4. Контроллеры для "Главная страница"


class MainPageView(LoginRequiredMixin, generic.TemplateView):
    """Представление для отображения *Главной страницы* со статистикой рассылок."""

    template_name = "app_mailing/main/main.html"

    def get_context_data(self, **kwargs):
        """Добавляем в контекст данные для отображения на *Главной странице*.
        ЧАСТЬ 1: Основная статистика по рассылкам из Mailing и получателям из Recipient:
            - Общее количество рассылок.
            - Количество активных рассылок (статус 'Запущена') + количество получателей именно по активным рассылкам.
            - Общее количество уникальных получателей.
        ЧАСТЬ 2: Статистика по отправкам из Attempt:
            - Количество успешных попыток рассылок.
            - Количество неуспешных попыток рассылок.
            - Общее количество отправленных сообщений + сколько из них именно уникальных текстов сообщений."""
        context = super().get_context_data(**kwargs)

        user = self.request.user  # Определил в переменную нашего владельца, чтоб ниже просто указывать "owner=user"

        # ЧАСТЬ 1: Основная статистика по рассылкам из Mailing и получателям из Recipient
        launched_mailings = Mailing.objects.filter(status="launched", owner=user)
        # Кол-во всех существующих рассылок во всех статусах
        context["total_mailings"] = Mailing.objects.filter(owner=user).count()
        # Кол-во активных рассылок + подсчет итогового кол-ва получателей именно по активным рассылкам
        context["active_mailings"] = launched_mailings.count()
        context["active_recipients_count"] = sum(m.recipients.count() for m in launched_mailings)
        # Кол-во всех получателей
        context["unique_recipients"] = Recipient.objects.filter(owner=user).count()

        # ЧАСТЬ 2: Статистика по отправкам из Attempt
        successful_attempts = Attempt.objects.filter(status="success", owner=user).count()
        failed_attempts = Attempt.objects.filter(status="failed", owner=user).count()
        # Кол-во успешных попыток рассылок
        context["successful_attempts"] = successful_attempts
        # Кол-во неуспешных попыток рассылок
        context["failed_attempts"] = failed_attempts
        # Кол-во отправленных сообщений + сколько из них именно уникальных текстов сообщений (например, мы можем
        # отправить 25 сообщений, но эти сообщения только по двум тематикам из "Сообщения")
        # !!!! Технически для подсчета уникальных сообщений можно использовать distinct("mailing_id"), но это работает
        # !!!! только в PostgreSQL. ЛУЧШЕ АЛЬТЕРНАТИВНОЕ РЕШЕНИЕ: использовать .values("mailing").distinct().count()
        # !!!! потому что это работает во всех БД, что важно для поддержания кросс-базовой совместимости:
        context["total_sent_messages"] = successful_attempts + failed_attempts
        context["unique_sent_messages"] = (Attempt.objects
                                           .filter(owner=user)
                                           .values("mailing")
                                           .distinct()
                                           .count()
                                           )

        return context
