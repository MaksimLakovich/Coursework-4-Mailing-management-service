import os

from django.contrib import messages
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.utils import timezone

from app_mailing.models import Attempt


def send_mailing(request, mailing):
    """Сервисная функция для запуска Рассылки:
    - Отправка email всем получателям в выбранной *Рассылке*.
    - Фиксация *Попыток рассылок* по каждому получателю.
    :param mailing: объект рассылки (Mailing), которую нужно запустить."""
    if mailing.status != "created":
        messages.warning(request, "Эту рассылку нельзя повторно запустить.")
        return redirect("app_mailing:mailing_list_page")

    recipients = mailing.recipients.all()

    if not recipients.exists():
        messages.warning(request, "У этой рассылки нет получателей.")
        return redirect("app_mailing:mailing_list_page")

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
            Attempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status="success",
                server_response="OK",
                owner=mailing.owner  # Важно!!! Чтоб автоматически во "owner попытки" записывался "owner рассылки"
            )
            success_count += 1
        except Exception as e:
            Attempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status="failed",
                server_response=str(e)
            )
            print(f"Ошибка при отправке письма на {recipient.email}: {e}")

    mailing.end_message_sending = timezone.now()  # Фиксирую дату окончания
    mailing.status = "accomplished"  # Меняю статус рассылки после завершения
    mailing.save()

    messages.success(request, f"Рассылка успешно отправлена {success_count} получателям.")


def send_mailing_cli(mailing):
    """CLI-версия сервисной функции для запуска Рассылки (Не требует request. Возвращает словарь с результатом
    рассылки (успешные, неудачные попытки).):
    - Отправка email всем получателям в выбранной *Рассылке*.
    - Фиксация *Попыток рассылок* по каждому получателю.
    :param mailing: объект рассылки (Mailing), которую нужно запустить."""
    if mailing.status != "created":
        return {
            "status": "error",
            "message": "Рассылка уже была запущена ранее.",
            "success": 0,
            "failed": 0,
        }

    recipients = mailing.recipients.all()

    if not recipients.exists():
        return {
            "status": "error",
            "message": "У этой рассылки нет получателей.",
            "success": 0,
            "failed": 0,
        }

    subject = mailing.message.message_subject
    message = mailing.message.message_body
    from_email = os.getenv("YANDEX_EMAIL_HOST_USER")

    mailing.status = "launched"  # Меняю статус рассылки, что она запущена
    mailing.first_message_sending = timezone.now()  # Фиксирую дату начала
    mailing.save()

    success_count = 0
    failed_count = 0

    for recipient in recipients:  # Запускаю рассылку по всем получателям
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=from_email,
                recipient_list=[recipient.email],
                fail_silently=False,
            )
            Attempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status="success",
                server_response="OK",
                owner=mailing.owner  # Важно!!! Чтоб автоматически во "owner попытки" записывался "owner рассылки"
            )
            success_count += 1
        except Exception as e:
            Attempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status="failed",
                server_response=str(e),
                owner=mailing.owner  # Важно!!! Чтоб автоматически во "owner попытки" записывался "owner рассылки"
            )
            failed_count += 1

    mailing.end_message_sending = timezone.now()  # Фиксирую дату окончания
    mailing.status = "accomplished"  # Меняю статус рассылки после завершения
    mailing.save()

    return {
        "status": "ok",
        "message": "Рассылка завершена",
        "success": success_count,
        "failed": failed_count,
    }


def stop_mailing(mailing, reason="Рассылка остановлена вручную"):
    """Сервисная функция для остановки Рассылки:
    - Устанавливает статус "accomplished".
    - Фиксирует время окончания рассылки.
    - Создает "failed" попытки рассылки по тем получателям, которым еще не отправлено сообщение.
    Используется:
    1) Пользователем сервиса в контроллере StopMailingView.
    2) Менеджером сервиса при блокировке пользователя.
    :param mailing: объект рассылки (Mailing), которую нужно остановить.
    :param reason: пояснение причины остановки (сохраняется в server_response)."""

    # ШАГ 1. Нахожу всех Получателей останавливаемой Рассылки
    all_recipients = mailing.recipients.all()

    # ШАГ 2. Получаю ID получателей, которым уже отправлено Сообщение (есть записи Attempt)
    sent_recipient_ids = set(
        mailing.attempts.values_list("recipient_id", flat=True)
    )

    # ШАГ 3. Создаю "failed" попытки по тем, кому еще не отправлено
    for recipient in all_recipients:
        if recipient.id not in sent_recipient_ids:
            Attempt.objects.create(
                mailing=mailing,
                recipient=recipient,
                status="failed",
                server_response=reason,
                owner=mailing.owner,
            )

    # ШАГ 4. Завершаю рассылку
    mailing.status = "accomplished"
    mailing.end_message_sending = timezone.now()
    mailing.save()
