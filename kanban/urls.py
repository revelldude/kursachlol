from django.urls import path
from .views import (
    StatusList, TaskUpdate, TaskCreate, TaskDelete, 
    FileUploadAPI, FileDeleteAPI, TaskFilesAPI, 
    index, kanban_board, kanban_boards,
    boards_list, create_board, board_view,
    login_view, register_view, logout_view,
    # calendar_view,  # УДАЛИТЬ ЭТУ СТРОКУ
    tasks_by_date_api, mini_calendar_api,
    board_mini_calendar_api, upcoming_deadlines_api, tasks_by_date_and_board_api 
)

urlpatterns = [
    # Аутентификация
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Защищенные маршруты
    path('', index, name='index'),
    path('board/', kanban_board, name='kanban-board'),
    path('boards/', kanban_boards, name='kanban-boards'),
    path('boards/create/', create_board, name='create_board'),
    path('boards/list/', boards_list, name='boards_list'),
    path('board/<int:board_id>/', board_view, name='board_view'),
    
    # API эндпоинты
    path('api/statuses/', StatusList.as_view(), name='status-list'),
    path('api/tasks/<int:pk>/update/', TaskUpdate.as_view(), name='task-update'),
    path('api/tasks/create/', TaskCreate.as_view(), name='task-create'),
    path('api/tasks/<int:pk>/delete/', TaskDelete.as_view(), name='task-delete'),
    path('api/tasks/by_date/', tasks_by_date_api, name='tasks_by_date'),
    path('api/mini_calendar/', mini_calendar_api, name='mini_calendar_api'),
    path('api/tasks/by_date_and_board/', tasks_by_date_and_board_api, name='tasks_by_date_and_board_api'),
    path('api/tasks/<int:task_id>/upload/', FileUploadAPI.as_view(), name='file-upload'),
    path('api/files/<int:file_id>/delete/', FileDeleteAPI.as_view(), name='file-delete'),
    path('api/tasks/<int:task_id>/files/', TaskFilesAPI.as_view(), name='task-files'),  # Добавьте эту строку
]