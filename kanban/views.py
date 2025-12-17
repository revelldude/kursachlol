from django.shortcuts import render, redirect, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.conf import settings 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework import status 
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect, csrf_exempt
from datetime import date
from .models import Board, Status, Task, TaskFile, TaskTable, TaskColumn, TaskRow, TaskCell
from .serializers import StatusSerializer, TaskSerializer, TaskFileSerializer
from django.core import serializers
from datetime import datetime, timedelta
from django.utils import timezone
from django.db import transaction
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import json

# ===== АУТЕНТИФИКАЦИЯ =====

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Добро пожаловать, {username}!')
                return redirect('index')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'kanban/login.html', {'form': form})

def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('index')
        else:
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = UserCreationForm()
    
    return render(request, 'kanban/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы.')
    return redirect('login')

# ===== ЗАЩИЩЕННЫЕ ПРЕДСТАВЛЕНИЯ =====

@login_required
@ensure_csrf_cookie
def index(request):
    return render(request, 'kanban/index.html')

@login_required
def kanban_boards(request):
    return render(request, 'kanban/boards.html')

@login_required
def kanban_board(request):
    return redirect('boards_list')

@login_required
def boards_list(request):
    boards = Board.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'kanban/boards_list.html', {'boards': boards})

@login_required
def check_session_api(request):
    """API для проверки состояния сессии пользователя"""
    try:
        return JsonResponse({
            'authenticated': request.user.is_authenticated,
            'username': request.user.username if request.user.is_authenticated else None,
            'user_id': request.user.id if request.user.is_authenticated else None,
            'session_key': request.session.session_key,
            'session_expiry': request.session.get_expiry_age() if request.session.session_key else None,
        })
    except Exception as e:
        return JsonResponse({
            'authenticated': False,
            'error': str(e)
        }, status=500)

@login_required
def create_board(request):
    if request.method == 'POST':
        name = request.POST.get('name', 'Новая доска')
        description = request.POST.get('description', '')

        board = Board.objects.create(name=name, user=request.user)
        
        Status.objects.create(board=board, name='Ожидание', order=1)
        Status.objects.create(board=board, name='В работе', order=2)
        Status.objects.create(board=board, name='Выполнены', order=3)
        
        return redirect('board_view', board_id=board.id)
    
    return redirect('kanban-boards')

@login_required
def board_view(request, board_id):
    board = get_object_or_404(Board, id=board_id, user=request.user)
    return render(request, 'kanban/board.html', {'board': board})
    
@login_required
def mini_calendar_api(request):
    """API для мини-календаря"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    from datetime import datetime
    now = datetime.now()
    year = int(year) if year else now.year
    month = int(month) if month else now.month
    
    # Получаем задачи на месяц
    from django.db.models import Q
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date()
    else:
        end_date = datetime(year, month + 1, 1).date()
    
    tasks = Task.objects.filter(
        board__user=request.user,
        deadline__isnull=False,
        deadline__gte=start_date,
        deadline__lt=end_date
    )
    
    # Группируем задачи по дням
    tasks_by_day = {}
    for task in tasks:
        day_key = task.deadline.strftime('%Y-%m-%d')
        if day_key not in tasks_by_day:
            tasks_by_day[day_key] = []
        tasks_by_day[day_key].append({
            'id': task.id,
            'title': task.title,
            'color': task.color,
        })
    
    return JsonResponse({
        'year': year,
        'month': month,
        'tasks_by_day': tasks_by_day,
    })
    
from django.http import JsonResponse
from datetime import datetime

@login_required
def mini_calendar_api(request):
    """API для мини-календаря (упрощенная версия)"""
    from datetime import datetime
    import calendar
    
    now = datetime.now()
    year = request.GET.get('year', now.year)
    month = request.GET.get('month', now.month)
    
    try:
        year = int(year)
        month = int(month)
        
        cal = calendar.monthcalendar(year, month)
        
        # Получаем задачи на месяц (простая версия)
        tasks = Task.objects.filter(
            board__user=request.user,
            deadline__isnull=False,
            deadline__year=year,
            deadline__month=month
        )
        
        # Группируем задачи по дням
        tasks_by_day = {}
        for task in tasks:
            day_key = task.deadline.strftime('%Y-%m-%d')
            if day_key not in tasks_by_day:
                tasks_by_day[day_key] = []
            tasks_by_day[day_key].append({
                'id': task.id,
                'title': task.title[:20] + '...' if len(task.title) > 20 else task.title,
            })
        
        return JsonResponse({
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'calendar': cal,
            'tasks_by_day': tasks_by_day,
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def tasks_by_date_api(request):
    """API для получения задач по дате"""
    date_str = request.GET.get('date')
    board_id = request.GET.get('board_id')
    
    if not date_str:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Фильтруем задачи пользователя
        tasks = Task.objects.filter(board__user=request.user)
        
        # Фильтр по дате
        tasks = tasks.filter(deadline=date_obj)
        
        # Фильтр по доске если указана
        if board_id:
            tasks = tasks.filter(board_id=board_id)
        
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else None,
                'color': task.color,
                'board_name': task.board.name if task.board else None,
                'status_name': task.status.name if task.status else None,
            })
        
        return JsonResponse(tasks_data, safe=False)
    
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)


@login_required
def board_mini_calendar_api(request):
    """API для мини-календаря доски (упрощенная версия)"""
    from datetime import datetime
    import calendar
    
    now = datetime.now()
    year = request.GET.get('year', now.year)
    month = request.GET.get('month', now.month)
    board_id = request.GET.get('board_id')
    
    try:
        year = int(year)
        month = int(month)
        
        cal = calendar.monthcalendar(year, month)
        
        # Пустой ответ для теста
        return JsonResponse({
            'year': year,
            'month': month,
            'month_name': calendar.month_name[month],
            'calendar': cal,
            'tasks_by_day': {},
        })
    
    except:
        return JsonResponse({'error': 'Invalid parameters'}, status=400)


@login_required
def upcoming_deadlines_api(request):

    return JsonResponse([], safe=False)

    board_id = request.GET.get('board_id')
    days = int(request.GET.get('days', 7))  # По умолчанию 7 дней
    
    try:
        board = Board.objects.get(id=board_id, user=request.user)
        
        today = timezone.now().date()
        end_date = today + timedelta(days=days)
        
        # Задачи с дедлайнами в указанном диапазоне
        tasks = Task.objects.filter(
            board=board,
            deadline__isnull=False,
            deadline__gte=today,
            deadline__lte=end_date
        ).select_related('status').order_by('deadline')
        
        tasks_data = []
        for task in tasks:
            days_left = (task.deadline - today).days
            
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'deadline': task.deadline.strftime('%Y-%m-%d'),
                'color': task.color,
                'status_name': task.status.name if task.status else None,
                'days_left': days_left,
            })
        
        return JsonResponse(tasks_data, safe=False)
        
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board not found or no access'}, status=404)
    


@login_required
def table_list(request):
    """Список всех таблиц пользователя"""
    tables = TaskTable.objects.filter(owner=request.user)
    return render(request, 'kanban/tables_list.html', {'tables': tables})

@login_required
def table_create(request):
    """Создание новой таблицы"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            table = TaskTable.objects.create(
                name=name,
                description=description,
                owner=request.user
            )
            
            # Создаем базовые колонки
            TaskColumn.objects.create(table=table, name='Задача', width=300, order=0)
            TaskColumn.objects.create(table=table, name='Статус', width=150, order=1)
            TaskColumn.objects.create(table=table, name='Срок', width=120, order=2)
            
            # Создаем первую строку-пример
            TaskRow.objects.create(table=table, title='Пример задачи', order=0)
            
            return redirect('table_detail', table_id=table.id)
    
    return render(request, 'kanban/table_create.html')

@login_required
def table_detail(request, table_id):
    # Используйте TaskTable вместо Table
    table = get_object_or_404(TaskTable, id=table_id, owner=request.user)
    columns = table.columns.all()
    rows = table.rows.all()
    
    # Получаем все ячейки для этой таблицы
    cells = TaskCell.objects.filter(row__table=table).select_related('row', 'column')
    
    # Преобразуем в словарь для удобства доступа в шаблоне
    cells_dict = {}
    for cell in cells:
        key = f"{cell.row.id}-{cell.column.id}"
        cells_dict[key] = cell.content
    
    return render(request, 'kanban/table_detail.html', {
        'table': table,
        'columns': columns,
        'rows': rows,
        'cells': cells_dict,
    })

@login_required
def add_column_ajax(request):
    """AJAX: Добавление колонки"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_id = data.get('table_id')
            name = data.get('name')
            width = data.get('width', 200)
            
            table = get_object_or_404(TaskTable, id=table_id, owner=request.user)
            
            # Определяем порядок
            last_column = table.columns.order_by('-order').first()
            order = (last_column.order + 1) if last_column else 0
            
            column = TaskColumn.objects.create(
                table=table,
                name=name,
                width=width,
                order=order
            )
            
            # Создаем ячейки для всех строк
            for row in table.rows.all():
                TaskCell.objects.create(row=row, column=column, content='')
            
            return JsonResponse({
                'success': True,
                'column': {
                    'id': column.id,
                    'name': column.name,
                    'width': column.width,
                    'order': column.order
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def add_row_ajax(request):
    """AJAX: Добавление строки"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            table_id = data.get('table_id')
            title = data.get('title')
            
            table = get_object_or_404(TaskTable, id=table_id, owner=request.user)
            
            # Определяем порядок
            last_row = table.rows.order_by('-order').first()
            order = (last_row.order + 1) if last_row else 0
            
            row = TaskRow.objects.create(
                table=table,
                title=title,
                order=order
            )
            
            # Создаем ячейки для всех колонок
            for column in table.columns.all():
                TaskCell.objects.create(row=row, column=column, content='')
            
            return JsonResponse({
                'success': True,
                'row': {
                    'id': row.id,
                    'title': row.title,
                    'order': row.order
                }
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def delete_row_ajax(request, row_id):
    """AJAX: Удаление строки"""
    if request.method == 'POST':
        try:
            row = get_object_or_404(TaskRow, id=row_id)
            if row.table.owner != request.user:
                return JsonResponse({'success': False, 'error': 'Нет доступа'})
            
            row.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def ajax_update_cell(request):
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            
            table_id = data.get('table_id')
            row_id = data.get('row_id')
            column_id = data.get('column_id')
            content = data.get('content', '')
            
            # Проверяем права доступа
            table = get_object_or_404(TaskTable, id=table_id, owner=request.user)
            row = get_object_or_404(TaskRow, id=row_id, table=table)
            column = get_object_or_404(TaskColumn, id=column_id, table=table)
            
            # Находим или создаем ячейку
            cell, created = TaskCell.objects.get_or_create(
                row=row,
                column=column,
                defaults={'content': content}
            )
            
            if not created:
                cell.content = content
                cell.save()
            
            return JsonResponse({
                'success': True,
                'cell_id': cell.id,
                'content': cell.content
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def delete_table_ajax(request, table_id):
    """AJAX: Удаление таблицы"""
    if request.method == 'POST':
        try:
            table = get_object_or_404(TaskTable, id=table_id, owner=request.user)
            table.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})



@login_required
def tasks_by_date_and_board_api(request):
    """API для задач по дате и доске"""
    date_str = request.GET.get('date')
    board_id = request.GET.get('board_id')
    
    if not date_str:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        tasks = Task.objects.filter(
            deadline=date_obj
        )
        
        if board_id:
            tasks = tasks.filter(board_id=board_id)
        
        tasks = tasks.filter(board__user=request.user).select_related('board', 'status')
        
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else None,
                'color': task.color,
                'board_name': task.board.name if task.board else None,
                'status_name': task.status.name if task.status else None,
            })
        
        return JsonResponse(tasks_data, safe=False)
    
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    
class StatusList(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        Task.objects.filter(deadline__lt=date.today()).delete()

        board_id = request.GET.get('board_id')
        if board_id:
            statuses = Status.objects.filter(
                board_id=board_id, 
                board__user=request.user
            ).order_by('order')
        else:
            statuses = Status.objects.filter(board__user=request.user).order_by('order')

        serializer = StatusSerializer(statuses, many=True)
        return Response(serializer.data, status=http_status.HTTP_200_OK)
    
@login_required
def board_delete(request, board_id):
    """Удаление доски"""
    if request.method == 'POST':
        board = get_object_or_404(Board, id=board_id, user=request.user)
        board.delete()
        return redirect('boards_list')
    
    # Если не POST запрос, показываем подтверждение
    board = get_object_or_404(Board, id=board_id, user=request.user)
    return render(request, 'kanban/board_delete.html', {'board': board})

class TaskCreate(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        print("\n" + "="*60)
        print("DEBUG TaskCreate - Начало")
        print(f"Пользователь: {request.user.username}")
        
        try:
            data = request.data
            print(f"Полученные данные: {data}")
            
            title = data.get('title')
            status_id = data.get('status')
            board_id = data.get('board')
            
            if not title:
                return Response({
                    'success': False,
                    'error': 'Название задачи обязательно'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            if not status_id:
                return Response({
                    'success': False,
                    'error': 'Статус обязателен'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            if not board_id:
                return Response({
                    'success': False,
                    'error': 'Доска обязательна'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            try:
                board = Board.objects.get(id=board_id, user=request.user)
                print(f"Доска найдена: {board.name} (ID: {board.id})")
            except Board.DoesNotExist:
                return Response({
                    'success': False,
                    'error': f'Доска с ID {board_id} не найдена или нет доступа'
                }, status=http_status.HTTP_400_BAD_REQUEST)
            
            try:
                status_obj = Status.objects.get(id=status_id, board=board)
                print(f"Статус найден: {status_obj.name} (ID: {status_obj.id})")
            except Status.DoesNotExist:
                print(f"Статус ID {status_id} не найден для доски {board_id}")
                
                alternative_status = Status.objects.filter(board=board).first()
                if alternative_status:
                    print(f"Используем альтернативный статус: {alternative_status.name} (ID: {alternative_status.id})")
                    status_obj = alternative_status
                    data['status'] = alternative_status.id
                else:
                    print(f"Создаем статусы для доски {board.name}")
                    status1 = Status.objects.create(board=board, name='Ожидание', order=1)
                    status2 = Status.objects.create(board=board, name='В работе', order=2)
                    status3 = Status.objects.create(board=board, name='Выполнены', order=3)
                    
                    status_obj = status1
                    data['status'] = status1.id
                    print(f"Созданы статусы. Используем: {status_obj.name} (ID: {status_obj.id})")
            
            serializer = TaskSerializer(data=data)
            
            if serializer.is_valid():
                task = serializer.save()
                print(f"Задача создана: {task.id} - {task.title}")
                
                return Response({
                    'success': True,
                    'id': task.id,
                    'title': task.title,
                    'status': task.status_id,
                    'board': task.board_id,
                    'message': 'Задача успешно создана'
                }, status=http_status.HTTP_201_CREATED)
            else:
                print(f"Ошибки сериализатора: {serializer.errors}")
                return Response({
                    'success': False,
                    'errors': serializer.errors
                }, status=http_status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            print(f"Неожиданная ошибка: {str(e)}")
            import traceback
            traceback.print_exc()
            
            return Response({
                'success': False,
                'error': str(e),
                'message': 'Внутренняя ошибка сервера'
            }, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR)

# ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЕ КЛАССЫ

class TaskUpdate(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            # Проверяем, что задача принадлежит пользователю
            task = Task.objects.get(pk=pk, board__user=request.user)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found or no access"},
                        status=http_status.HTTP_404_NOT_FOUND)
        
        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=http_status.HTTP_200_OK)
        
        return Response(serializer.errors, status=http_status.HTTP_400_BAD_REQUEST)

class TaskDelete(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            task = Task.objects.get(pk=pk, board__user=request.user)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found or no access"}, 
                          status=http_status.HTTP_404_NOT_FOUND)
        task.delete()
        return Response(status=http_status.HTTP_204_NO_CONTENT)
    
class FileUploadAPI(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id, board__user=request.user)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found or no access"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        if 'file' not in request.FILES:
            return Response({"detail": "No file provided"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Проверка типа файла
        if uploaded_file.content_type not in settings.ALLOWED_FILE_TYPES:
            return Response({"detail": "File type not allowed"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Проверка размера файла (макс 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:  # 10MB
            return Response({"detail": "File size exceeds 10MB limit"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Сохраняем файл
        try:
            task_file = TaskFile.objects.create(
                task=task,
                file=uploaded_file,
                original_filename=uploaded_file.name,
                file_size=uploaded_file.size,
                uploaded_by=request.user
            )
            
            serializer = TaskFileSerializer(task_file, context={'request': request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({"detail": str(e)}, 
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class FileDeleteAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, file_id):
        try:
            task_file = TaskFile.objects.get(id=file_id, task__board__user=request.user)
            
            # Удаляем файл
            task_file.delete()
            
            return Response({"detail": "File deleted successfully"}, 
                          status=status.HTTP_204_NO_CONTENT)
            
        except TaskFile.DoesNotExist:
            return Response({"detail": "File not found or no access"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        # ... предыдущий код views.py ...

class FileDeleteAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, file_id):
        try:
            task_file = TaskFile.objects.get(id=file_id, task__board__user=request.user)
            
            # Удаляем файл
            task_file.delete()
            
            return Response({"detail": "File deleted successfully"}, 
                          status=status.HTTP_204_NO_CONTENT)
            
        except TaskFile.DoesNotExist:
            return Response({"detail": "File not found or no access"}, 
                          status=status.HTTP_404_NOT_FOUND)

# Класс TaskFilesAPI должен быть на том же уровне отступа, что и другие классы
class TaskFilesAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, task_id):
        try:
            task = Task.objects.get(id=task_id, board__user=request.user)
            files = task.files.all()
            serializer = TaskFileSerializer(files, many=True, context={'request': request})
            return Response(serializer.data)
        except Task.DoesNotExist:
            return Response({"detail": "Task not found or no access"}, 
                          status=status.HTTP_404_NOT_FOUND)

# Конец файла - больше ничего после этого
