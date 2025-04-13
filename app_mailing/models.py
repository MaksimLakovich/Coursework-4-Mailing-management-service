from django.db import models


class Recipient(models.Model):
    """Модель *Recipient* представляет "Получателя рассылки" в сервисе управления рассылками."""

    email = models.EmailField(
        unique=True,
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

    def __str__(self):
        """Метод определяет строковое представление объекта. Полезно для отображения объектов в админке/консоли."""
        return f"{self.email} ({self.full_name})"

    class Meta:
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ["email"]
        db_table = "tb_recipient"


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

    def __str__(self):
        """Метод определяет строковое представление объекта. Полезно для отображения объектов в админке/консоли."""
        return f"Рассылка {self.message} от {self.first_message_sending}"

    class Meta:
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["message"]
        db_table = "tb_mailing"
