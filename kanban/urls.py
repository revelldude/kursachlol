from django.urls import path
from . import views
from .views import (
    StatusList, TaskUpdate, TaskCreate, TaskDelete, 
    FileUploadAPI, FileDeleteAPI, TaskFilesAPI, 
    index, kanban_board, kanban_boards,
    boards_list, create_board, board_view,
    login_view, register_view, logout_view,
    tasks_by_date_api, mini_calendar_api,
    board_mini_calendar_api, upcoming_deadlines_api, 
    tasks_by_date_and_board_api, check_session_api,
    table_list, table_create, table_detail,
    add_column_ajax, add_row_ajax, delete_row_ajax, 
    ajax_update_cell, delete_table_ajax
)

urlpatterns = [
    # Аутентификация
    path('login/', login_view, name='login'),
    path('register/', register_view, name='register'),
    path('logout/', logout_view, name='logout'),
    
    # Главная страница
    path('', index, name='index'),
    
    # Доски Kanban
    path('board/', kanban_board, name='kanban-board'),
    path('boards/', kanban_boards, name='kanban-boards'),
    path('boards/create/', create_board, name='create_board'),
    path('boards/list/', boards_list, name='boards_list'),
    path('board/<int:board_id>/', board_view, name='board_view'),
    path('board/<int:board_id>/delete/', views.board_delete, name='board_delete'), 
    
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
    path('api/tasks/<int:task_id>/files/', TaskFilesAPI.as_view(), name='task-files'),
    path('api/check-session/', check_session_api, name='check_session'),

    path('tables/', views.table_list, name='table_list'),
    path('tables/create/', views.table_create, name='table_create'),
    path('tables/<int:table_id>/', views.table_detail, name='table_detail'),
    path('tables/<int:table_id>/delete/', views.delete_table_ajax, name='delete_table'),
    
    # AJAX для таблиц
    path('tables/ajax/add-column/', views.add_column_ajax, name='add_column_ajax'),
    path('tables/ajax/add-row/', views.add_row_ajax, name='add_row_ajax'),
    path('tables/ajax/update-cell/', views.ajax_update_cell, name='ajax_update_cell'),
    path('tables/ajax/delete-row/<int:row_id>/', views.delete_row_ajax, name='delete_row_ajax'),
]
