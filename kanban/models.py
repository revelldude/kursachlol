from django.db import models

class Status(models.Model):
    name = models.CharField(max_length=50, unique=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.ForeignKey(Status, related_name='tasks', on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    deadline = models.DateField(null=True, blank=True) 
    color = models.CharField(max_length=7, blank=True, null=True)


    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title
