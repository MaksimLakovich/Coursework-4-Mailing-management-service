from django.contrib.auth.models import AbstractUser
from django.db import models

from users.managers import AppUserManager


class AppUser(AbstractUser):
    """Модель AppUser представляет пользователя приложения."""

    username = None

    email = models.EmailField(
        unique=True,
        verbose_name="Почта (username):",
        help_text="Введите email",
    )

    avatar = models.ImageField(
        upload_to="user_avatar/",
        blank=True,
        null=True,
        verbose_name="Аватар:",
        help_text="Загрузите аватар",
    )

    is_blocked = models.BooleanField(
        default=False,
        verbose_name="Статус блокировки пользователя:",
        help_text="Укажите заблокирован или нет пользователь",
    )

    objects = AppUserManager()  # Указываю кастомный менеджер для пользователя без поля username.

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def __str__(self):
        """Метод определяет строковое представление объекта. Полезно для отображения объектов в админке/консоли."""
        return f"{self.email}"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]
        db_table = "tb_app_users"
        permissions = [
            ("can_see_list_user", "Может видеть список пользователей сервиса"),
            ("can_block_user", "Может блокировать пользователей сервиса"),
        ]
