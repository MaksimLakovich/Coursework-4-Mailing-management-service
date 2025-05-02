from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

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
        # что и так уже автоматически создает class UserCustomer(AbstractUser).
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

            # ✅ Переопределяем label вручную
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
