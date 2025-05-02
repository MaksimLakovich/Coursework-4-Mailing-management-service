from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from users.forms import AppUserRegistrationForm


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
    """Представление для отображения страницы регистрации нового пользователя (register.html)."""

    form_class = AppUserRegistrationForm
    template_name = "users/register.html"
    success_url = reverse_lazy("app_mailing:main_page")  # Редирект после регистрации

    def form_valid(self, form):
        """Сохранение нового пользователя и автоматический вход после регистрации."""
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
