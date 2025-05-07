import os

# messages - для отображения сообщений пользователю:
from django.contrib import messages
# login - логин пользователя после активации, а get_user_model - получение нашей кастомной модели пользователя
from django.contrib.auth import get_user_model, login
# default_token_generator - генератор безопасных токенов Django для подтверждения email:
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView
# get_current_site - получает текущий домен сайта (например, "mailforge.com"), используется в письме:
from django.contrib.sites.shortcuts import get_current_site
# send_mail - отправка email через системный smtp/email backend:
from django.core.mail import send_mail
from django.shortcuts import redirect
# render_to_string - загружаю HTML-шаблон письма и заменяю в нем переменные:
from django.template.loader import render_to_string
from django.urls import reverse_lazy
# force_bytes - преобразует ID пользователя в байты (нужно для кодирования в urlsafe_base64_encode):
from django.utils.encoding import force_bytes
# urlsafe_base64_encode - преобразует числовой ID пользователя в безопасный текст base64 (нужно для ссылки).
# urlsafe_base64_decode - декодирует UID из ссылки обратно в ID:
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
# Для подтверждения email нам нужен базовый класс представления - View (не FormView)
from django.views import View
from django.views.generic import FormView, TemplateView

from users.forms import AppUserLoginForm, AppUserRegistrationForm


class UserStartView(TemplateView):
    """Представление для стартовой страницы (start.html) с кнопками "Войти" и "Зарегистрироваться"."""

    template_name = "users/start.html"

    def dispatch(self, request, *args, **kwargs):
        """Добавлен редирект авторизованного пользователя, чтобы он, когда переходит на /start/
        (например, по прямой ссылке), не попадал туда, а автоматически перенаправлялся на главную страницу
        авторизованного пользователя."""
        if self.request.user.is_authenticated:
            return redirect("app_mailing:main_page")
        return super().dispatch(request, *args, **kwargs)


class UserRegisterView(FormView):
    """Представление для отображения страницы регистрации нового пользователя (register.html)
    с последующей отправкой письма для подтверждения email."""

    form_class = AppUserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("app_mailing:main_page")  # Редирект после регистрации

    def form_valid(self, form):
        """Обработка валидной формы регистрации:
        - 1) Если пользователь с таким email уже существует и активен - регистрация невозможна.
        - 2) Если пользователь существует, но не активен - повторно отправляем письмо с подтверждением.
        - 3) Если пользователь не существует - создаём нового, отправляем письмо."""
        User = get_user_model()  # Получаю нашу кастомную модель пользователя (AppUser или другую)
        email = form.cleaned_data["email"]  # Можно через .get("email"), но мы уверены что такой ключ есть в БД
        existing_user = User.objects.filter(email=email).first()

        # ВЕТКА 1 (повторно отправляем письмо): активный/неактивный пользователь, но уже существующий в БД
        if existing_user:
            if existing_user.is_active:
                form.add_error("email", "Пользователь с таким email уже зарегистрирован и активен.")
                return self.form_invalid(form)
            user = existing_user
        # ВЕТКА 2 (записываем в БД и отправляем письмо): новый пользов., первая попытка подтвердить
        else:
            user = form.save(commit=False)  # Создаем пользователя, но не сохраняем его пока что в БД (commit=False)
            user.is_active = False  # Деактивирую пользователя - он не сможет войти до подтверждения email
            user.save()  # Теперь сохраняю пользователя в БД

        current_site = get_current_site(self.request)  # Получаю домен тек.сайта, нужен для генерации полной ссылки
        subject = "Подтвердите регистрацию на MailForge"
        uid = urlsafe_base64_encode(force_bytes(user.pk))  # Генерирую зашифрованный ID пользователя
        # Генерирую уникальный токен для подтверждения (работает как пароль на одноразовую ссылку)
        token = default_token_generator.make_token(user)

        # Строю полный абсолютный путь к ссылке активации (например: https://mailforge.com/activate/MjMyNA/token12345/)
        activation_link = self.request.build_absolute_uri(
            reverse_lazy("users:activate_account", kwargs={"uidb64": uid, "token": token})
        )

        # Загружаю HTML-шаблон письма и передаю в него данные
        message = render_to_string(
            "users/email_confirmation.html",
            {
                "user": user,
                "domain": current_site.domain,
                "activation_link": activation_link,
            })

        # Отправляю письмо пользователю
        send_mail(
            subject,
            message,
            from_email=os.getenv("YANDEX_EMAIL_HOST_USER"),
            recipient_list=[user.email],
            fail_silently=False,  # Выбросить ошибку, если не удалось отправить
        )

        # После успешной отправки письма делаю редирек на страницу "Письмо отправлено"
        return redirect("users:email_confirmation_sent_page")


class ActivateAccountView(View):  # Для подтверждения email нужен базовый класс представления - View (не FormView)
    """Представление для активации учетной записи пользователя по email-ссылке."""

    def get(self, request, uidb64, token):
        """Обработка GET-запроса по ссылке из email:
        - Расшифровка uid пользователя.
        - Проверка токена.
        - Активация пользователя и логинит его в приложении.
        - Перенаправление на главную страницу."""
        User = get_user_model()  # Получаю нашу кастомную модель пользователя (AppUser или другую)

        try:
            uid = urlsafe_base64_decode(uidb64).decode()  # Преобразую uid из ссылки обратно в ID
            user = User.objects.get(pk=uid)  # Получаю пользователя из БД
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None  # Если что-то пошло не так и пользователь не найден

        # Проверяю, что пользователь существует и токен действителен с последующей итоговой его активацией
        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)  # Логиним пользователя (автоматически)

            # Показываю сообщение об успехе и редирект на главную страницу
            messages.success(request, "Вы подтвердили почту. Добро пожаловать!")
            return redirect("app_mailing:main_page")
        else:
            # Токен невалиден или пользователь не найден
            messages.error(request, "Ссылка недействительна или устарела.")
            return redirect("users:start_page")


class UserEmailConfirmationSentView(TemplateView):
    """Представление для промежуточной страницы после регистрации с инструкцией по подтверждению email."""

    template_name = "users/email_confirmation_sent.html"

    def dispatch(self, request, *args, **kwargs):
        """Проверяет, авторизован ли пользователь. Если да, то он уже подтвердил email
        и не должен видеть эту страницу. В таком случае происходит перенаправление
        на главную страницу приложения. Если пользователь не авторизован, продолжается
        обычная обработка запроса."""
        if self.request.user.is_authenticated:
            return redirect("app_mailing:main_page")
        return super().dispatch(request, *args, **kwargs)


class UserLoginView(LoginView):
    """Представление для входа пользователя (login.html)."""

    # Явно указываю кастомную форму для входа пользователя, без этого не подтягиваются определенные в
    # форме AppUserLoginForm стили (наверное, потому что по умолчанию LoginView использует стандартную
    # форму Django → AuthenticationForm.)
    authentication_form = AppUserLoginForm
    template_name = "users/login.html"

    def get_success_url(self):
        """Метод get_success_url() в LoginView - это предпочтительный для Django способ указания редиректа после
        успешной аутентификации. Если просто указать в контроллере "success_url = reverse_lazy(
        'app_mailing:main_page'", то это не будет работать."""
        return reverse_lazy("app_mailing:main_page")

    def form_valid(self, form):
        """Автоматический вход пользователя после успешной аутентификации."""
        login(self.request, form.get_user())
        return super().form_valid(form)
