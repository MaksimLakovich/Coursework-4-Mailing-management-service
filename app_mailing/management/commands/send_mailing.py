from django.core.management.base import BaseCommand

from app_mailing.models import Mailing
from app_mailing.services import send_mailing_cli


class Command(BaseCommand):
    """Команда для запуска *Рассылки* из командной строки и фиксации *Попыток рассылок*
    по каждому *Получателю* из рассылки."""

    help = "Запуск рассылки по ID"

    def add_arguments(self, parser):
        """Добавляем обязательный аргумент: ID рассылки."""
        parser.add_argument("mailing_id", type=int, help="ID рассылки")

    def handle(self, *args, **kwargs):
        """Основная логика команды: проверяет статус, запускает отправку, обновляет даты,
        фиксирует попытки рассылок и выводит результат."""
        mailing_id = kwargs["mailing_id"]

        try:
            mailing = Mailing.objects.get(pk=mailing_id)
        except Mailing.DoesNotExist:
            self.stdout.write(self.style.ERROR("Рассылка с таким ID не найдена."))
            return

        send_mailing_cli(mailing)
