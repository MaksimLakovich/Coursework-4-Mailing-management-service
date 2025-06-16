from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
from django.utils.timezone import now
from django_apscheduler.jobstores import DjangoJobStore

from app_mailing.models import Mailing
from app_mailing.services import send_mailing_cli


# Планировщик существует как глобальный объект - один на всё приложение! ПОЭТОМУ создание Планировщика и подключение
# DjangoJobStore для хранения job'ов в базе данных ДОЛЖНО БЫТЬ НА УРОВНЕ МОДУЛЯ, а не внутри функции start()
mailing_scheduler = BackgroundScheduler(timezone=str(timezone.get_current_timezone()))
mailing_scheduler.add_jobstore(DjangoJobStore(), "default")


def my_scheduled_job():
    """Функция регулярно проверяет все рассылки, которые запланированы на "сейчас или раньше" но ещё не отправлены
    (status='created') и запускает их."""
    mailings_to_send = Mailing.objects.filter(
        status="created",
        first_message_sending__lte=now()  # означает "раньше или сейчас"
    )
    for mailing in mailings_to_send:
        send_mailing_cli(mailing)


def start():
    """Инициализация и запуск планировщика: регистрация события, добавление задачи на повторяющийся запуск и сам
    запуск планировщика в фоновом режиме."""
    # Добавляю задачу: каждую минуту проверять, есть ли задачи на отправку
    mailing_scheduler.add_job(
        my_scheduled_job,  # функция, которая будет вызываться
        trigger="interval",  # тип триггера
        minutes=1,  # интервал между вызовами
        id="tech_id",  # мой уникальный ID (оно должно быть чтоб все корректно работало, могу указать любое значение)
        replace_existing=True,  # перезаписываю, если уже есть задача с таким ID
    )
    mailing_scheduler.start()
    print("✅ APScheduler успешно запущен.")
