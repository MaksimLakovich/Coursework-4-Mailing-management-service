from django.db import models

from config import settings


class Recipient(models.Model):
    """Модель *Recipient* представляет "Получателя рассылки" в сервисе управления рассылками."""

    email = models.EmailField(
        blank=False,
        null=False,
        verbose_name="Почта получателя:",
        help_text="Укажите почту получателя",
    )
    full_name = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Ф.И.О. получателя:",
        help_text="Укажите Ф.И.О. получателя",
    )
    comment = models.TextField(
        blank=True,
        null=True,
        verbose_name="Комментарий:",
        help_text="Укажите комментарий о получателе",
    )
    owner = models.ForeignKey(
        null=True,  # Разрешаем пустые значения в БД
        blank=True,  # Разрешаем пустое поле в формах
        default=None,  # По умолчанию None
        # Динамически подставляю текущую user модель, чего не делает такой простой вариант как "to=users.models.UserCustomer".
        # Если мы когда-нибудь изменим AUTH_USER_MODEL в settings.py, модель Recipient автоматически обновится.
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="recipients",
        verbose_name="Создатель получателя рассылки:",
        help_text="Пользователь, создавший этого получателя рассылки"
    )

    def __str__(self):
        """Метод определяет строковое представление объекта. Полезно для отображения объектов в админке/консоли."""
        return f"{self.email} ({self.full_name})"

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ["email"]
        db_table = "tb_recipient"
        # Добавляю уникальный "together constraint" - теперь Django будет следить за тем,
        # чтобы у каждого пользователя email был уникальным, но другие пользователи могут добавить такой же email себе.
        constraints = [
            models.UniqueConstraint(fields=["owner", "email"], name="unique_recipient_per_owner")
        ]


class Message(models.Model):
    """Модель *Message* представляет "Сообщение рассылки" в сервисе управления рассылками."""

    message_subject = models.CharField(
        max_length=250,
        blank=False,
        null=False,
        verbose_name="Тема письма:",
        help_text="Введите тему письма",
    )
    message_body = models.TextField(
        blank=False,
        null=False,
        verbose_name="Тело письма:",
        help_text="Введите суть письма",
    )
    owner = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name="Создатель сообщения для рассылки:",
        help_text="Пользователь, создавший это сообщение для рассылки"
    )

    def __str__(self):
        """Метод определяет строковое представление объекта. Полезно для отображения объектов в админке/консоли."""
        return f"Тема письма: {self.message_subject}"

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["message_subject"]
        db_table = "tb_message"


class Mailing(models.Model):
    """Модель *Mailing* представляет "Рассылку" в сервисе управления рассылками.
    Статусы рассылки:
        Создана - рассылка была создана, но еще ни разу не была отправлена.
        Запущена - рассылка активна и была отправлена хотя бы один раз.
        Завершена - время окончания отправки рассылки прошло."""

    MAILING_STATUS = [
        ("created", "Создана"),
        ("launched", "Запущена"),
        ("accomplished", "Завершена"),
    ]

    first_message_sending = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата и время первой отправки:",
        help_text="Укажите дату и время первой отправки",
    )
    end_message_sending = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата и время окончания отправки:",
        help_text="Укажите дату и время окончания отправки",
    )
    status = models.CharField(
        max_length=50,
        null=False,
        blank=False,
        choices=MAILING_STATUS,
        default="created",
        verbose_name="Статус рассылки:",
        help_text="Укажите статус рассылки",
    )
    message = models.ForeignKey(
        to=Message,
        on_delete=models.CASCADE,
        null=False,  # В Django ForeignKey по умолчанию null=False, и blank=False (я оставил явно для читаемости).
        blank=False,
        related_name="mailings",  # "message.mailings.all()" - все рассылки по этому сообщению.
        verbose_name="Сообщение для рассылки:",
        help_text="Укажите сообщение для рассылки",
    )
    recipients = models.ManyToManyField(
        to=Recipient,
        blank=True,  # В Django null=True для ManyToManyField не используется. Django его игнорирует.
        related_name="mailings",  # "recipient.mailings.all()" - все рассылки, в которых участвует данный получатель.
        verbose_name="Получатели для рассылки:",
        help_text="Укажите получателей для рассылки",
    )
    owner = models.ForeignKey(
        null=True,
        blank=True,
        default=None,
        to=settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Создатель рассылки:",
        help_text="Пользователь, запустивший эту рассылку"
    )

    def __str__(self):
        """Метод определяет строковое представление объекта. Полезно для отображения объектов в админке/консоли."""
        return f"Рассылка {self.message} от {self.first_message_sending}"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["message"]
        db_table = "tb_mailing"


class Attempt(models.Model):
    """Модель *Attempt* представляет "Попытка рассылки" в сервисе управления рассылками.
    Статусы попытки: успешно / не успешно."""

    ATTEMPT_STATUS = [
        ("success", "Успешно"),
        ("failed", "Не успешно"),
    ]

    attempt_time = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время попытки рассылки:",
        help_text="Укажите дату и время попытки рассылки",
    )
    status = models.CharField(
        max_length=15,
        choices=ATTEMPT_STATUS,
        verbose_name="Статус попытки рассылки:",
        help_text="Укажите статус попытки рассылки",
    )
    server_response = models.TextField(
        blank=True,
        null=True,
        verbose_name="Ответ почтового сервера:",
        help_text="Укажите ответ почтового сервера",
    )
    mailing = models.ForeignKey(
        to=Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка:",
        help_text="Укажите рассылку",
    )
    recipient = models.ForeignKey(
        to=Recipient,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Получатель:",
        help_text="Укажите получателя, которому была отправлена рассылка",
    )
    owner = models.ForeignKey(
        to=settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        default=None,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Создатель попытки рассылки:",
        help_text="Пользователь, которому принадлежит эта попытка"
    )

    def __str__(self):
        """Метод определяет строковое представление объекта. Полезно для отображения объектов в админке/консоли."""
        return f"{self.attempt_time:%d.%m.%Y %H:%M} | {self.recipient.email} | {self.get_status_display()}"

    class Meta:
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ["-attempt_time"]
        db_table = "tb_attempt"
