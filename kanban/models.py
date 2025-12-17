# kanban/models.py
import os
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings 

def task_file_path(instance, filename):
    """Генерирует путь для файлов задач"""
    date_path = timezone.now().strftime('%Y/%m/%d')
    return os.path.join('task_files', date_path, filename)

class Board(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='boards')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class Status(models.Model):
    name = models.CharField(max_length=100)
    order = models.IntegerField(default=0)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='statuses')
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.name} (Board: {self.board.name})"

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='tasks')
    order = models.IntegerField(default=0)
    color = models.CharField(max_length=7, default='#008cff')
    deadline = models.DateField(blank=True, null=True)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='tasks')
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)  # Добавлено null=True, blank=True
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.id and not self.created_at:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to=task_file_path)
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.original_filename} ({self.task.title})"
    
class TaskTable(models.Model):
    """Модель для таблиц задач"""
    name = models.CharField(max_length=200, verbose_name="Название таблицы")
    description = models.TextField(blank=True, verbose_name="Описание")
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tables')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class TaskColumn(models.Model):
    """Колонка в таблице"""
    table = models.ForeignKey(TaskTable, on_delete=models.CASCADE, related_name='columns')
    name = models.CharField(max_length=100, verbose_name="Название колонки")
    width = models.IntegerField(default=200, verbose_name="Ширина (px)")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.table.name} - {self.name}"

class TaskRow(models.Model):
    """Строка в таблице"""
    table = models.ForeignKey(TaskTable, on_delete=models.CASCADE, related_name='rows')
    title = models.CharField(max_length=200, verbose_name="Название строки")
    order = models.IntegerField(default=0, verbose_name="Порядок")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.title

class TaskCell(models.Model):
    """Ячейка таблицы"""
    row = models.ForeignKey(TaskRow, on_delete=models.CASCADE, related_name='cells')
    column = models.ForeignKey(TaskColumn, on_delete=models.CASCADE, related_name='cells')
    content = models.TextField(blank=True, verbose_name="Содержимое")
    
    class Meta:
        unique_together = ['row', 'column']
    
    def __str__(self):
        return f"{self.row.title} - {self.column.name}"
    
    
