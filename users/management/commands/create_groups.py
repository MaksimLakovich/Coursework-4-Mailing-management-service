from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Создаёт группу 'Менеджер сервиса' с view-доступом ко всем моделям рассылки"

    def handle(self, *args, **options):
        # ШАГ 1: Создаю или получаю, если уже есть, группу "Менеджер сервиса".
        group_name = "Менеджер сервиса"
        group, created = Group.objects.get_or_create(name=group_name)

        if created:
            self.stdout.write(self.style.SUCCESS(f"Группа '{group_name}' успешно создана."))
        else:
            self.stdout.write(self.style.WARNING(f"Группа '{group_name}' уже существует."))

        # ШАГ 2: Добавляю в ГРУППУ view-разрешения по моделям.
        model_names = ["recipient", "message", "mailing", "attempt"]  # Список имен моделей, на которые надо разрешения

        for model_name in model_names:  # Для каждой из моделей получаю разрешение вида: "view_modelname"
            codename = f"view_{model_name}"
            try:
                permission = Permission.objects.get(codename=codename)
                group.permissions.add(permission)
                self.stdout.write(self.style.SUCCESS(f"Добавлено разрешение: {codename}"))
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Разрешение {codename} не найдено."))

        # ШАГ 3: Добавляю в ГРУППУ кастомные права
        can_see_list_user = Permission.objects.get(codename="can_see_list_user")
        can_block_user = Permission.objects.get(codename="can_block_user")
        group.permissions.add(can_see_list_user, can_block_user)

        self.stdout.write(self.style.SUCCESS("Назначение разрешений завершено."))
