from django import forms

from app_mailing.models import Recipient


class AddNewRecipientForm(forms.ModelForm):
    """Форма для добавления пользователем нового Получателя рассылки на странице recipient_form_add_new.html"""

    class Meta:
        model = Recipient
        fields = "__all__"
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Введите email (обязательное поле)"}),
            "full_name": forms.TextInput(attrs={"placeholder": "Введите ФИО (опционально)"}),
            "comment": forms.Textarea(attrs={"placeholder": "Введите комментарий (опционально)"}),
        }

    def __init__(self, *args, **kwargs):
        """Стилизации полей формы с использованием виджета. Виджеты позволяют настроить внешний вид и поведение полей
        формы через атрибуты. Это делается с помощью метода attrs.
            - Добавляем CSS-классы ко всем полям формы.
            - Убираем параметр 'help_text' со всех полей, чтоб этого больше не было по умолчанию на html-странице."""
        super().__init__(*args, **kwargs)

        # ШАГ 1: Убираю отображение help_text на странице, так как help_text из model.py дублирует то, что мы
        # добавили в forms.ModelForm (параметры "placeholder" в widgets).
        for field_name, field in self.fields.items():
            field.help_text = None
            # ШАГ 2: Добавляю класс "form-control" для всех полей, кроме чекбоксов:
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-control text-muted-secondary"
            # ШАГ 3: Добавляю класс "form-check-input" для чекбоксов:
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
