from django.apps import AppConfig


class AppMailingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_mailing'

    # def ready(self):
    #     """Метод ready() запускается Django при старте приложения. Здесь мы импортируем модуль scheduler.py и
    #     запускаем из него планировщик mailing_scheduler, который существует как глобальный объект (то есть на
    #     уровне модуля, а значит mailing_scheduler запустится в фоновом режиме сразу же при обращении к модулю)."""
    #     from . import scheduler
    #     scheduler.start()  # запускаю функцию start() из app_mailing/scheduler.py

    def ready(self):
        import os
        if os.environ.get("RUN_MAIN") == "true":  # защита от двойного запуска Gunicorn/Runserver
            from . import scheduler
            try:
                scheduler.start()
            except Exception as e:
                print(f"⚠️ APScheduler не запущен: {e}")
