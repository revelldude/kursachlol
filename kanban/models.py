from django.db import models
from django.contrib.auth.models import User

class Board(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    def __str__(self):
        return self.name

class Status(models.Model):
    board = models.ForeignKey(Board, on_delete=models.CASCADE, null=True, blank=True, related_name='statuses')
    name = models.CharField(max_length=50)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = ['board', 'name']

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.ForeignKey(Status, related_name='tasks', on_delete=models.CASCADE)
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='tasks')
    order = models.PositiveIntegerField(default=0)
    deadline = models.DateField(null=True, blank=True)
    color = models.CharField(max_length=7, blank=True, null=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

