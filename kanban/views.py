from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status as http_status
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import date
from .models import Board, Status, Task
from .serializers import StatusSerializer, TaskSerializer
from django.core import serializers
from datetime import datetime, timedelta
from django.utils import timezone

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
# ... остальной код views.py ...

@login_required
def calendar_view(request, year=None, month=None):
    # Получаем текущий год и месяц если не указаны
    from datetime import datetime
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    
    # Получаем все задачи пользователя с дедлайнами
    tasks = Task.objects.filter(
        board__user=request.user,
        deadline__isnull=False
    ).select_related('board', 'status')
    
    # Создаем структуру для календаря
    import calendar
    cal = calendar.monthcalendar(year, month)
    
    # Создаем словарь задач по дням
    tasks_by_day = {}
    for task in tasks:
        if task.deadline:
            day_key = task.deadline.strftime('%Y-%m-%d')
            if day_key not in tasks_by_day:
                tasks_by_day[day_key] = []
            tasks_by_day[day_key].append(task)
    
    # Получаем названия месяцев
    month_name = calendar.month_name[month]
    
    # Предыдущий и следующий месяц
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year
    
    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year
    
    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'calendar': cal,
        'tasks_by_day': tasks_by_day,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'today': now.date(),
    }
    
    return render(request, 'kanban/calendar.html', context)

@login_required
def tasks_by_date_api(request):
    """API для получения задач по дате"""
    date_str = request.GET.get('date')
    if not date_str:
        return JsonResponse({'error': 'Date parameter required'}, status=400)
    
    try:
        from datetime import datetime
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        tasks = Task.objects.filter(
            board__user=request.user,
            deadline=date_obj
        ).select_related('board', 'status')
        
        tasks_data = []
        for task in tasks:
            tasks_data.append({
                'id': task.id,
                'title': task.title,
                'description': task.description,
                'deadline': task.deadline.strftime('%Y-%m-%d') if task.deadline else None,
                'color': task.color,
                'board_name': task.board.name if task.board else None,
                'status_name': task.status.name if task.status else None,
                'status_color': '#4CAF50' if task.status and task.status.name == 'Выполнены' else 
                               '#FF9800' if task.status and task.status.name == 'В работе' else '#9E9E9E',
            })
        
        return JsonResponse(tasks_data, safe=False)
    
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
    
@login_required
def mini_calendar_api(request):
    """API для мини-календаря"""
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    from datetime import datetime
    now = datetime.now()
    year = int(year) if year else now.year
    month = int(month) if month else now.month
    
    import calendar
    cal = calendar.monthcalendar(year, month)
    
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
        'month_name': calendar.month_name[month],
        'calendar': cal,
        'tasks_by_day': tasks_by_day,
    })
    
@login_required
def board_mini_calendar_api(request):
    """API для мини-календаря конкретной доски"""
    board_id = request.GET.get('board_id')
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    now = datetime.now()
    year = int(year) if year else now.year
    month = int(month) if month else now.month
    
    import calendar
    cal = calendar.monthcalendar(year, month)
    
    try:
        board = Board.objects.get(id=board_id, user=request.user)
        
        # Получаем задачи этой доски на месяц
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        
        tasks = Task.objects.filter(
            board=board,
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
            'month_name': calendar.month_name[month],
            'calendar': cal,
            'tasks_by_day': tasks_by_day,
            'board_name': board.name,
        })
        
    except Board.DoesNotExist:
        return JsonResponse({'error': 'Board not found or no access'}, status=404)

@login_required
def upcoming_deadlines_api(request):
    """API для ближайших дедлайнов"""
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