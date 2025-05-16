from django import forms

from app_mailing.models import Mailing, Message, Recipient


class AddNewRecipientForm(forms.ModelForm):
    """Форма для добавления пользователем нового Получателя рассылки на странице recipient_add_update.html"""

    class Meta:
        model = Recipient
        fields = "__all__"
        exclude = ["owner"]
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Введите email (обязательное поле)"}),
            "full_name": forms.TextInput(attrs={"placeholder": "Введите ФИО (опционально)"}),
            "comment": forms.Textarea(attrs={"placeholder": "Введите комментарий (опционально)"}),
        }

    def clean_email(self):
        """Метод для валидации email: проверяет, существует ли уже получатель с таким email у текущего
        пользователя (owner). Если да - не позволяет повторно добавить этого получателя.
        Это предотвращает дублирование одного и того же email в списке клиента приложения, но разрешает другим
        пользователям добавлять такого же получателя себе."""
        # Беру значение, которое пользователь ввёл в поле "Email" (после коробочной проверки, что email валидный).
        email = self.cleaned_data["email"]

        # Получаю владельца (того, кто создаёт или редактирует получателя):
        # 1) self.instance.owner - работает, если мы редактируем существующего получателя.
        # 2) self.initial.get("owner") - работает, если мы только создаём нового получателя.
        owner = self.instance.owner or self.initial.get("owner")

        # 1) Recipient.objects.filter(owner=owner, email=email) - тут ищу в БД, а есть ли у этого пользователя
        # получатель с таким email или нет?
        # 2) .exclude(pk=self.instance.pk) - тут исключаю из поиска сам объект, если он уже есть (например, если
        # пользователь редактирует получателя - сравнивать с самим собой не надо, иначе будет замкнутый круг при
        # редактировании любого получателя.
        if owner and Recipient.objects.filter(owner=owner, email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("У вас уже есть получатель с таким email.")
        return email

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


class AddNewMessageForm(forms.ModelForm):
    """Форма для добавления пользователем нового Сообщения рассылки на странице message_add_update.html"""

    class Meta:
        model = Message
        fields = "__all__"
        exclude = ["owner"]
        widgets = {
            "message_subject": forms.TextInput(attrs={"placeholder": "Введите тему письма"}),
            "message_body": forms.Textarea(attrs={"placeholder": "Введите тело письма"}),
        }

    def __init__(self, *args, **kwargs):
        """Стилизации полей формы с использованием виджета. Виджеты позволяют настроить внешний вид и поведение полей
        формы через атрибуты. Это делается с помощью метода attrs.
            - Добавляем CSS-классы ко всем полям формы.
            - Убираем параметр 'help_text' со всех полей, чтоб этого больше не было по умолчанию на html-странице."""
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.help_text = None
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-control text-muted-secondary"
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"


class AddNewMailingForm(forms.ModelForm):
    """Форма для добавления пользователем новой Рассылки на странице mailing_add_update.html"""

    class Meta:
        model = Mailing
        fields = ["message", "recipients"]
        exclude = ["owner"]
        widgets = {
            "message": forms.Select(
                attrs={"class": "form-select text-muted-secondary"}
            ),
            "recipients": forms.SelectMultiple(
                attrs={"class": "duallistbox form-control", "multiple": "multiple", }
            ),
        }

    def __init__(self, *args, **kwargs):
        """1) Ограничиваем queryset только объектами текущего пользователя (запрет на вывод всего подряд из БД).
        2) Стилизации полей формы с использованием виджета. Виджеты позволяют настроить внешний вид и поведение полей
        формы через атрибуты. Это делается с помощью метода attrs.
            - Переопределяю отображение объектов в select'е, чтоб не выводился из модели
            текст "Тема письма:" в f"Тема письма: {self.message_subject}"
            - Убираем параметр "help_text" со всех полей, чтоб этого больше не было по
            умолчанию на html-странице."""
        # Забираю пользователя из kwargs, чтоб потом по нему ограничить доступ только к его объектам из БД.
        user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        # ШАГ 1: Ограничиваю queryset только объектами текущего пользователя:
        if user:
            self.fields["message"].queryset = Message.objects.filter(owner=user)
            self.fields["recipients"].queryset = Recipient.objects.filter(owner=user)

        # ШАГ 2: Выполняю стилизацию формы
        def get_message_subject(obj):
            return obj.message_subject

        self.fields["message"].label_from_instance = get_message_subject

        for field_name, field in self.fields.items():
            field.help_text = None
