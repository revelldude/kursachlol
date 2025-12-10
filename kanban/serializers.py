from rest_framework import serializers
from .models import Status, Task

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'order', 'deadline']

class StatusSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Status
        fields = ['id', 'name', 'order', 'tasks']