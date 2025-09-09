from django.contrib.auth.base_user import BaseUserManager


class AppUserManager(BaseUserManager):
    """Кастомный менеджер пользователей, использующий email вместо username."""

    def create_user(self, email, password=None, **extra_fields):
        """Создает обычного пользователя с указанным email и паролем.
        :param email: Email пользователя (используется как логин).
        :param password: Пароль пользователя (по умолчанию None).
        :param extra_fields: Дополнительные поля модели пользователя.
        :return: Объект созданного пользователя.
        :raises ValueError: Если email не указан."""
        if not email:
            raise ValueError("Email обязателен для создания пользователя.")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Создает суперпользователя с расширенными правами доступа.
        :param email: Email суперпользователя (используется как логин).
        :param password: Пароль суперпользователя.
        :param extra_fields: Дополнительные поля модели пользователя.
        :return: Объект созданного суперпользователя.
        :raises ValueError: Если is_staff или is_superuser не установлены в True."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
