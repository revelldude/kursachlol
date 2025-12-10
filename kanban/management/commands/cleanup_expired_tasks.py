from datetime import date

from django.core.management.base import BaseCommand
from kanban.models import Task


class Command(BaseCommand):
    help = "Удаляет задачи, чей дедлайн раньше сегодняшней даты"

    def handle(self, *args, **options):
        today = date.today()
        qs = Task.objects.filter(deadline__lt=today)
        count = qs.count()
        qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Удалено задач: {count}"))