import os

from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from app_mailing.models import Mailing


class Command(BaseCommand):
    """Команда для запуска Рассылки из командной строки."""

    help = "Запуск рассылки по ID"

    def add_arguments(self, parser):
        """Добавляем обязательный аргумент: ID рассылки."""
        parser.add_argument("mailing_id", type=int, help="ID рассылки")

    def handle(self, *args, **kwargs):
        """Основная логика команды: проверяет статус, запускает отправку, обновляет даты и выводит результат."""
        mailing_id = kwargs["mailing_id"]

        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            self.stdout.write(self.style.ERROR("Рассылка с таким ID не найдена."))
            return

        if mailing.status != "created":
            self.stdout.write(self.style.WARNING("Рассылка уже была запущена ранее."))
            return

        recipients = mailing.recipients.all()
        if not recipients.exists():
            self.stdout.write(self.style.WARNING("У этой рассылки нет получателей."))
            return

        subject = mailing.message.message_subject
        message = mailing.message.message_body
        from_email = os.getenv("YANDEX_EMAIL_HOST_USER")

        mailing.status = "launched"  # Меняю статус рассылки, что она запущена
        mailing.first_message_sending = timezone.now()  # Фиксирую дату начала
        mailing.save()

        success_count = 0

        for recipient in recipients:  # Запускаю рассылку по всем получателям
            try:
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=from_email,
                    recipient_list=[recipient.email],
                    fail_silently=False,
                )
                success_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка при отправке {recipient.email}: {e}'))

        mailing.end_message_sending = timezone.now()  # Фиксирую дату окончания
        mailing.status = "accomplished"  # Меняю статус рассылки после завершения
        mailing.save()

        self.stdout.write(self.style.SUCCESS(f'Рассылка успешно отправлена {success_count} получателям.'))
