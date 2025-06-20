from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.cache import _generate_cache_key
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.cache import cache_page

from app_mailing.forms import (AddNewMailingForm, AddNewMessageForm,
                               AddNewRecipientForm)
from app_mailing.models import Attempt, Mailing, Message, Recipient
from app_mailing.services import send_mailing, stop_mailing

# 1. Контроллеры для "Управление клиентами"


# Использую декоратор для создания кеша для всей страницы с параметром key_prefix, который потом нужен для
# сброса кэша страницы при добавлении/редактировании/удалении данных какого-либо объекта (получателя)
@method_decorator(cache_page(60 * 15, key_prefix="recipients_list"), name="dispatch")
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
        2) Автоматическое заполнение текущим пользователем поля 'owner' при создании нового *Получателя рассылки*.
        3) Сброс кэша при добавлении нового Получателя."""
        messages.success(self.request, "Новый получатель успешно добавлен")

        form.instance.owner = self.request.user  # Привязываю текущего пользователя как owner

        # Формирую новый объект запроса с путём до списка всех получателей "recipient_list_page".
        # Сейчас выполняя запрос CreateView мы находимся внутри формы создания нового получателя
        # (например: /recipients/add/), а значит: self.request.path  ➝  "/mailing/recipients/add/".
        # Но, необходимо сбросить кэш списка всех получателей (именно в "/mailing/recipients/"), поэтому подменяю путь:
        # ШАГ 1: Здесь я запрашиваю у Django URL для именованного пути "app_mailing:recipient_list_page", что вернёт
        # нужную строку "/mailing/recipients/":
        list_path = reverse("app_mailing:recipient_list_page")
        # ШАГ 2: Здесь делаю так, чтоб Django временно сделал вид, что текущий запрос был к списку получателей.
        # Это нужно только на момент вызова _generate_cache_key() - чтобы он сгенерировал правильный ключ кэша
        # именно для страницы списка, а не формы редактирования:
        self.request.path = list_path
        # Далее задача: получить точное имя ключа кэша, по которому Django сохранил страницу "/mailing/recipients/",
        # то есть список получателей.
        # Django кэширует не просто по URL, а использует внутренний алгоритм для генерации ключа.
        # Вызываю внутреннюю Django-функцию _generate_cache_key(), которая создаёт имя кэша, которое Django использует
        # при сохранении страницы:
        cache_key = _generate_cache_key(
            # Передаю наш request - чтобы Django знал, какой путь учитывать при удалении кэша (в этом request.path уже
            # подменён выше!)
            request=self.request,
            # Кэш всегда создаётся для GET-запросов (POST и другие - нет)
            method="GET",
            # Если бы у меня были какие-то особые заголовки (Vary: Header), я бы указал их тут. Но нет ничего такого,
            # поэтому просто передаю пустой список
            headerlist=[],
            # Это префикс, который указывал в @cache_page(...) на RecipientListView. Очень важно, чтобы здесь было
            # точно то же самое. Иначе ключ не совпадёт - и кэш не удалится
            key_prefix="recipients_list"
        )
        cache.delete(cache_key)

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
        """1) Отправка пользователю уведомления об успешном редактировании данных Получателя из списка рассылки.
        2) Сброс кэша при обновлении данных какого-либо Получателя из списка."""
        response = super().form_valid(form)

        # # ВАРИАНТ 1: через параметр самого объекта recipient с получением его через get_object():
        # recipient = self.get_object()
        # messages.success(self.request, f"Вы успешно обновили данные клиента: {recipient.email}")
        # ВАРИАНТ 2: обращаясь к параметру объекта через саму форму - form.instance.email:
        messages.success(self.request, f"Вы успешно обновили данные клиента: {form.instance.email}")

        # Формирую новый объект запроса с путём до списка всех получателей "recipient_list_page".
        # Сейчас выполняя запрос UpdateView мы находимся внутри формы редактирования какого-то одного получателя
        # (например: /mailing/recipients/24/update/), а значит: self.request.path  ➝  "/mailing/recipients/24/update/".
        # Но, необходимо сбросить кэш списка всех получателей (именно в "/mailing/recipients/"), поэтому подменяю путь:
        # ШАГ 1: Здесь я запрашиваю у Django URL для именованного пути "app_mailing:recipient_list_page", что вернёт
        # нужную строку "/mailing/recipients/":
        list_path = reverse("app_mailing:recipient_list_page")
        # ШАГ 2: Здесь делаю так, чтоб Django временно сделал вид, что текущий запрос был к списку получателей.
        # Это нужно только на момент вызова _generate_cache_key() - чтобы он сгенерировал правильный ключ кэша
        # именно для страницы списка, а не формы редактирования:
        self.request.path = list_path
        # Далее задача: получить точное имя ключа кэша, по которому Django сохранил страницу "/mailing/recipients/",
        # то есть список получателей.
        # Django кэширует не просто по URL, а использует внутренний алгоритм для генерации ключа.
        # Вызываю внутреннюю Django-функцию _generate_cache_key(), которая создаёт имя кэша, которое Django использует
        # при сохранении страницы:
        cache_key = _generate_cache_key(
            # Передаю наш request - чтобы Django знал, какой путь учитывать при удалении кэша (в этом request.path уже
            # подменён выше!)
            request=self.request,
            # Кэш всегда создаётся для GET-запросов (POST и другие - нет)
            method="GET",
            # Если бы у меня были какие-то особые заголовки (Vary: Header), я бы указал их тут. Но нет ничего такого,
            # поэтому просто передаю пустой список
            headerlist=[],
            # Это префикс, который указывал в @cache_page(...) на RecipientListView. Очень важно, чтобы здесь было
            # точно то же самое. Иначе ключ не совпадёт - и кэш не удалится
            key_prefix="recipients_list"
        )
        cache.delete(cache_key)

        return response


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
        """1) Отправка пользователю уведомления об успешном удалении Получателя из списка рассылки.
        2) Сброс кэша при удалении какого-либо Получателя из списка."""
        recipient = self.get_object()

        messages.success(self.request, f"Вы удалили клиента: {recipient.email}")

        list_path = reverse("app_mailing:recipient_list_page")
        self.request.path = list_path
        cache_key = _generate_cache_key(
            request=self.request,
            method="GET",
            headerlist=[],
            key_prefix="recipients_list"
        )
        cache.delete(cache_key)

        return super().form_valid(form)


# 2. Контроллеры для "Управление сообщениями"


# Использую декоратор для создания кеша для всей страницы с параметром key_prefix, который потом нужен для
# сброса кэша страницы при добавлении/редактировании/удалении данных какого-либо объекта (сообщения)
@method_decorator(cache_page(60 * 15, key_prefix="messages_list"), name="dispatch")
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
        2) Автоматическое заполнение текущим пользователем поля 'owner' при создании нового *Сообщения рассылки*.
        3) Сброс кэша при добавлении нового Сообщения."""
        messages.success(self.request, "Новое сообщение успешно добавлено")

        form.instance.owner = self.request.user  # Привязываю текущего пользователя как owner

        list_path = reverse("app_mailing:message_list_page")
        self.request.path = list_path
        cache_key = _generate_cache_key(
            request=self.request,
            method="GET",
            headerlist=[],
            key_prefix="messages_list"
        )
        cache.delete(cache_key)

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
        """1) Отправка пользователю уведомления об успешном редактировании данных Сообщения из списка рассылки.
        2) Сброс кэша при обновлении данных какого-либо Сообщения из списка."""
        response = super().form_valid(form)

        messages.success(self.request, f"Вы успешно обновили данные сообщения: {form.instance.id}")

        list_path = reverse("app_mailing:message_list_page")
        self.request.path = list_path
        cache_key = _generate_cache_key(
            request=self.request,
            method="GET",
            headerlist=[],
            key_prefix="messages_list"
        )
        cache.delete(cache_key)

        return response


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
        """1) Отправка пользователю уведомления об успешном удалении Сообщения из списка рассылки.
        2) Сброс кэша при удалении какого-либо Сообщения из списка."""
        messages.success(self.request, "Вы удалили сообщение.")

        list_path = reverse("app_mailing:message_list_page")
        self.request.path = list_path
        cache_key = _generate_cache_key(
            request=self.request,
            method="GET",
            headerlist=[],
            key_prefix="messages_list"
        )
        cache.delete(cache_key)

        return super().form_valid(form)


# 3. Контроллеры для "Управление рассылками"


# Использую декоратор для создания кеша для всей страницы с параметром key_prefix, который потом нужен для
# сброса кэша страницы при редактировании/изменении данных какого-либо объекта (рассылки)
@method_decorator(cache_page(60 * 15, key_prefix="mailings_list"), name="dispatch")
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

    def get_context_data(self, **kwargs):
        """Добавление в контекст шаблона текущую дату и время, чтобы потом
        использовать её в *min="{{now|date:'Y-m-d\TH:i'}}"* в шаблоне *mailing_list.html*"""
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()  # добавлено: текущая дата и время
        return context


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
        2) Автоматическое заполнение текущим пользователем поля 'owner' при создании нового *Рассылки*.
        3) Сброс кэша при добавлении новой Рассылки."""
        messages.success(self.request, "Новая рассылка успешно добавлена")

        form.instance.owner = self.request.user  # Привязываю текущего пользователя как owner

        list_path = reverse("app_mailing:mailing_list_page")
        self.request.path = list_path
        cache_key = _generate_cache_key(
            request=self.request,
            method="GET",
            headerlist=[],
            key_prefix="mailings_list"
        )
        cache.delete(cache_key)

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
        """1) Отправка пользователю уведомления об успешном редактировании данных Рассылки из списка.
        2) Сброс кэша при обновлении данных какой-либо Рассылки из списка."""
        response = super().form_valid(form)

        messages.success(self.request, f"Вы успешно обновили данные рассылки: {form.instance.id}")

        list_path = reverse("app_mailing:mailing_list_page")
        self.request.path = list_path
        cache_key = _generate_cache_key(
            request=self.request,
            method="GET",
            headerlist=[],
            key_prefix="mailings_list"
        )
        cache.delete(cache_key)

        return response


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
        """1) Отправка пользователю уведомления об успешном удалении Рассылки.
        2) Сброс кэша при удалении какой-либо Рассылки из списка."""
        messages.success(self.request, "Вы удалили рассылку")

        list_path = reverse("app_mailing:mailing_list_page")
        self.request.path = list_path
        cache_key = _generate_cache_key(
            request=self.request,
            method="GET",
            headerlist=[],
            key_prefix="mailings_list"
        )
        cache.delete(cache_key)

        return super().form_valid(form)


class SendMailingView(LoginRequiredMixin, generic.View):
    """Представление для запуска выбранной пользователем *Рассылки* вручную через интерфейс
    и фиксации *Попыток рассылок* по каждому *Получателю* из рассылки."""

    def post(self, request, pk):
        """1) Метод запускает сервисную функцию *send_mailing()* из services.py, которая:
            - отправляет email всем получателям в выбранной *Рассылке*.
            - фиксирует *Попытки рассылок* по каждому получателю.
        2) Сброс кэша при запуске какой-либо Рассылки из списка.
        3) Информирование пользователя об успешном запуске Рассылки."""
        mailing = get_object_or_404(Mailing, pk=pk)
        send_mailing(request, mailing)

        list_path = reverse("app_mailing:mailing_list_page")
        request.path = list_path
        cache_key = _generate_cache_key(
            request=request,
            method="GET",
            headerlist=[],
            key_prefix="mailings_list"
        )
        cache.delete(cache_key)

        messages.success(request, "Рассылка была успешно запущена.")
        return redirect("app_mailing:mailing_list_page")


class StopMailingView(LoginRequiredMixin, generic.View):
    """Представление для остановки выбранной пользователем *Рассылки* вручную через интерфейс
    и фиксации остановки *Попыток рассылок* по каждому *Получателю* из рассылки, которые еще не были отправлены."""

    def post(self, request, pk):
        """1) POST-запрос инициирует остановку рассылки:
            - завершает рассылку.
            - фиксирует "неудачные" попытки рассылки по оставшимся получателям.
            - возвращает пользователя на список рассылок.
        2) Сброс кэша при остановке какой-либо Рассылки из списка.
        3) Информирование пользователя об успешной остановке запущенной ранее Рассылки."""
        mailing = get_object_or_404(Mailing, pk=pk)
        if request.user != mailing.owner:
            return HttpResponseForbidden("Вы не можете останавливать чужую рассылку.")
        stop_mailing(mailing, reason="Пользователь вручную остановил рассылку")

        list_path = reverse("app_mailing:mailing_list_page")
        request.path = list_path
        cache_key = _generate_cache_key(
            request=request,
            method="GET",
            headerlist=[],
            key_prefix="mailings_list"
        )
        cache.delete(cache_key)

        messages.success(request, "Рассылка была успешно остановлена.")
        return redirect("app_mailing:mailing_list_page")


class ScheduleMailingModalView(LoginRequiredMixin, generic.View):
    """Представление для планирования запуска *Рассылки* через модальное окно."""

    def post(self, request, pk):
        """- Устанавливает дату и время первого запуска (first_message_sending).
        - Переводит рассылку в статус "created" (готова к отправке).
        - Планировщик APScheduler обработает эту рассылку в нужный момент.
        - Выполняется проверка прав (только владелец рассылки может её планировать).
        - Очищает кеш списка рассылок для мгновенного отображения изменений.
        - Показывает пользователю уведомление об успехе или ошибке."""
        mailing = get_object_or_404(Mailing, pk=pk)

        # Проверка прав
        if mailing.owner != request.user:
            return HttpResponseForbidden("Вы не можете запланировать чужую рассылку.")

        # Получение даты из формы
        first_message_sending = request.POST.get("first_message_sending")

        if first_message_sending:
            mailing.first_message_sending = first_message_sending
            mailing.status = "created"
            mailing.save()

            list_path = reverse("app_mailing:mailing_list_page")
            request.path = list_path
            cache_key = _generate_cache_key(
                request=request,
                method="GET",
                headerlist=[],
                key_prefix="mailings_list"
            )
            cache.delete(cache_key)

            messages.success(
                request,
                f"Рассылка успешно запланирована на {mailing.first_message_sending}"
            )
        else:
            messages.error(request, "Не указана дата и время!")

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
