from rest_framework import serializers
from .models import Status, Task

class TaskSerializer(serializers.ModelSerializer):
    deadline = serializers.DateField(required=False, allow_null=True)
    color = serializers.CharField(required=False, allow_null=True, max_length=7)
    description = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'order', 'deadline', 'color', 'board']
        read_only_fields = ['id']

    def validate_status(self, value):
        # Проверяем, что статус существует
        if not Status.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Указанный статус не существует")
        return value
        
    def validate_board(self, value):
        # Проверяем, что доска существует
        from .models import Board
        if not Board.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Указанная доска не существует")
        return value
    
class StatusSerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True, read_only=True)

    class Meta:
        model = Status
        fields = ['id', 'name', 'order', 'tasks']