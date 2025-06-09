from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
# gettext_lazy() - инструмент для поддержки многоязычности (i18n, internationalization) в Django.
# gettext_lazy() - это "ленивый перевод" строки. Он не переводит сразу, а откладывает перевод до момента отображения
# пользователю (например, в шаблоне или в форме).
# ✅ Когда использовать gettext_lazy? ОТВЕТ: всегда, когда ты нужно, чтобы строка:
# 1. Автоматически переводилась в зависимости от языка пользователя;
# 2. Была доступна для обработки в .po/.mo файлах (система перевода Django).**
# 3. Примеры таких строк: Ошибки форм; Названия полей (label); Help-тексты; Названия моделей (verbose_name);
# Любые надписи в шаблонах или сообщениях.
# ✅ Можно просто писать строки без gettext_lazy(), если:
# 1. Не используем систему перевода (наш проект только на русском или мы не планируем интернационализацию);
# 2. Не нужно, чтобы строка автоматически подстраивалась под язык.
from django.utils.translation import gettext_lazy as translation

from users.models import AppUser


class AppUserRegistrationForm(UserCreationForm):
    """Форма для регистрации пользователя в сервисе управления рассылками."""

    class Meta:
        model = AppUser
        fields = ("email", "password1", "password2")
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Введите email"}),
            "password1": forms.PasswordInput(attrs={"placeholder": "Введите пароль"}),
            "password2": forms.PasswordInput(attrs={"placeholder": "Введите пароль повторно"}),
        }

    def __init__(self, *args, **kwargs):
        """Настройка внешнего вида и поведения полей формы."""
        super().__init__(*args, **kwargs)

        # ШАГ 1: Убираю help_text из вывода на странице, так как help_text из model.py и дублирует то,
        # что и так уже автоматически создает class AppUser(AbstractUser).
        for field_name, field in self.fields.items():
            field.help_text = None
            # ШАГ 2: Применяю стили - добавляю класс "form-control" для всех полей.
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-control"
            # ШАГ 3: Устанавливаю placeholder вручную для наших полей формы регистрации.
            placeholders = {
                "email": "Введите email",
                "password1": "Введите пароль",
                "password2": "Введите пароль повторно",
            }
            if field_name in placeholders:
                field.widget.attrs["placeholder"] = placeholders[field_name]

            # ШАГ 4: Переопределяю label вручную вместо значений на английском
            self.fields["password1"].label = "Пароль"
            self.fields["password2"].label = "Подтвердить пароль"

    def clean_email(self):
        """Переопределяю clean_email() для явной проверки уникальности email.
        Функция clean_email() нужна, даже если email уже unique=True в модели как у нас потому что unique=True в
        модели выбрасывает ошибку на уровне БД, но не показывает ее в форме, а clean_email() помогает показать
        пользователю в форме, что такой email уже занят."""
        email = self.cleaned_data.get("email")
        if AppUser.objects.filter(email=email).exists():
            raise ValidationError(
                "Этот email уже используется. Пожалуйста, выберите другой."
            )
        return email


class AppUserLoginForm(AuthenticationForm):
    """Форма для входа ранее зарегистрированного пользователя в сервис управления рассылками."""

    def __init__(self, *args, **kwargs):
        """Настройка внешнего вида и поведения полей формы."""
        super().__init__(*args, **kwargs)

        # ШАГ 1: Django использует "username" как ключ, но у нас логин по email поэтому меняю username на email
        # ШАГ 2: Применяю стили - добавляю класс "form-control" для всех полей.
        # ШАГ 3: Устанавливаю placeholder вручную для наших полей формы регистрации.
        self.fields["username"].widget = forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "Введите email"}
        )
        self.fields["password"].widget = forms.PasswordInput(
            attrs={"class": "form-control", "placeholder": "Введите пароль"}
        )
        # ШАГ 4: Убираю help_text из вывода на странице, так как help_text из model.py и дублирует то,
        # что и так уже автоматически создает class AppUser(AbstractUser).
        for field_name, field in self.fields.items():
            field.help_text = None

            # ШАГ 5: Переопределяю label вручную вместо значений на английском
            self.fields["password"].label = "Пароль"

    def clean(self):
        """Переопределяю дефолтное сообщение Django об ошибке.
        БЫЛО: Please enter a correct Почта (username): and password. Note that both fields may be case-sensitive.
        СТАЛО: Пожалуйста, проверьте правильность введённых данных и повторите попытку.
        В реализации использую gettext_lazy() - инструмент для поддержки многоязычности (i18n, internationalization).
        gettext_lazy() - это "ленивый перевод" строки. Он не переводит сразу, а откладывает перевод до момента
        отображения пользователю (например, в шаблоне или в форме)."""
        try:
            return super().clean()
        except forms.ValidationError:
            raise forms.ValidationError(
                translation("Пожалуйста, проверьте правильность введённых данных и повторите попытку."),
                code="invalid_login"
            )
