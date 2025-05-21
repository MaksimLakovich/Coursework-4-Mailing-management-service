from django.utils import timezone

from app_mailing.models import Attempt


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

    if mailing.status != "launched":
        return  # Если рассылка не запущена, ничего не делаем

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
