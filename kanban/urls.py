from django.urls import path
from .views import StatusList, TaskUpdate, TaskCreate, TaskDelete, kanban_board

urlpatterns = [
    path('', kanban_board, name='kanban-board'),
    path('api/statuses/', StatusList.as_view(), name='status-list'),
    path('api/tasks/<int:pk>/update/', TaskUpdate.as_view(), name='task-update'),
    path('api/tasks/create/', TaskCreate.as_view(), name='task-create'),
    path('api/tasks/<int:pk>/delete/', TaskDelete.as_view(), name='task-delete'),
]