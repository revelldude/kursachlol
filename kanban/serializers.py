from rest_framework import serializers
from .models import Status, Task, TaskFile

class StatusSerializer(serializers.ModelSerializer):
    tasks = serializers.SerializerMethodField()
    
    class Meta:
        model = Status
        fields = ['id', 'name', 'order', 'board', 'tasks']
    
    def get_tasks(self, obj):
        # Получаем задачи для этого статуса
        tasks = obj.tasks.all().order_by('order')
        return TaskSerializer(tasks, many=True).data

class TaskSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source='status.name', read_only=True)
    file_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'status_name', 
                  'order', 'color', 'deadline', 'board', 'created_at', 'file_count']
    
    def get_file_count(self, obj):
        return obj.files.count()

class TaskFileSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    name = serializers.CharField(source='original_filename')
    
    class Meta:
        model = TaskFile
        fields = ['id', 'name', 'url', 'file_size', 'uploaded_at', 'uploaded_by']
        read_only_fields = ['id', 'uploaded_at', 'uploaded_by']
    
    def get_url(self, obj):
        request = self.context.get('request')
        if request and obj.file:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None