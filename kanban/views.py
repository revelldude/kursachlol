from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Status, Task
from .serializers import StatusSerializer, TaskSerializer
from django.shortcuts import render
from datetime import date
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def kanban_board(request):
    return render(request, 'kanban/board.html')

class StatusList(APIView):
    def get(self, request):
        Task.objects.filter(deadline__lt=date.today()).delete()
        statuses = Status.objects.all().order_by('order')
        serializer = StatusSerializer(statuses, many=True)
        return Response(serializer.data)

class TaskUpdate(APIView):
    def post(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found"},
                        status=status.HTTP_404_NOT_FOUND
                        )
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
class TaskCreate(APIView):
    def post(self, request):
        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class TaskDelete(APIView):
    def post(self, request, pk):
        try:
            task = Task.objects.get(pk=pk)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found"}, status=status.HTTP_404_NOT_FOUND)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)






