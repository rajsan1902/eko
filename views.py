from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *

def is_admin(user):
    return user.is_superuser or user.is_staff

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'farm/login.html')

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard(request):
    # Summary statistics
    total_batches = SpawnBatch.objects.count()
    active_batches = SpawnBatch.objects.filter(status='active').count()

    # Current month's sales
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_sales = Sale.objects.filter(
        sale_date__year=current_year,
        sale_date__month=current_month
    ).aggregate(total=Sum('final_amount'))['total'] or 0

    # Monthly expenses
    monthly_expenses = Expense.objects.filter(
        date__year=current_year,
        date__month=current_month
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Recent sales
    recent_sales = Sale.objects.all().order_by('-sale_date')[:5]

    # Recent harvests
    recent_harvests = Harvest.objects.all().order_by('-harvest_date')[:5]

    context = {
        'total_batches': total_batches,
        'active_batches': active_batches,
        'monthly_sales': monthly_sales,
        'monthly_expenses': monthly_expenses,
        'profit': monthly_sales - monthly_expenses,
        'recent_sales': recent_sales,
        'recent_harvests': recent_harvests,
    }
    return render(request, 'farm/dashboard.html', context)

@login_required
def batch_list(request):
    batches = SpawnBatch.objects.all().order_by('-spawn_date')
    return render(request, 'farm/batch_list.html', {'batches': batches})

@login_required
def batch_create(request):
    if request.method == 'POST':
        form = SpawnBatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.created_by = request.user
            batch.save()
            messages.success(request, 'Batch created successfully!')
            return redirect('batch_list')
    else:
        form = SpawnBatchForm()
    return render(request, 'farm/batch_form.html', {'form': form, 'title': 'Create Batch'})

@login_required
def harvest_list(request):
    harvests = Harvest.objects.all().order_by('-harvest_date')
    return render(request, 'farm/harvest_list.html', {'harvests': harvests})

@login_required
def harvest_create(request):
    if request.method == 'POST':
        form = HarvestForm(request.POST)
        if form.is_valid():
            harvest = form.save()
            messages.success(request, 'Harvest recorded successfully!')
            return redirect('harvest_list')
    else:
        form = HarvestForm()
    return render(request, 'farm/harvest_form.html', {'form': form, 'title': 'Record Harvest'})

@login_required
def sale_list(request):
    sales = Sale.objects.all().order_by('-sale_date')
    return render(request, 'farm/sale_list.html', {'sales': sales})

@login_required
def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            messages.success(request, 'Sale recorded successfully!')
            return redirect('sale_list')
    else:
        form = SaleForm()
    return render(request, 'farm/sale_form.html', {'form': form, 'title': 'Record Sale'})

@login_required
def expense_list(request):
    expenses = Expense.objects.all().order_by('-date')
    total = expenses.aggregate(total=Sum('amount'))['total'] or 0

    # Category-wise summary
    category_summary = Expense.objects.values('category').annotate(
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'expenses': expenses,
        'total': total,
        'category_summary': category_summary,
    }
    return render(request, 'farm/expense_list.html', context)

@login_required
def expense_create(request):
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Expense recorded successfully!')
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'farm/expense_form.html', {'form': form, 'title': 'Add Expense'})

@login_required
def profit_loss(request):
    # Get date range from request
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if not start_date or not end_date:
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Calculate sales
    sales = Sale.objects.filter(sale_date__range=[start_date, end_date])
    total_sales = sales.aggregate(total=Sum('final_amount'))['total'] or 0

    # Calculate expenses
    expenses = Expense.objects.filter(date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

    profit = total_sales - total_expenses

    # Daily breakdown
    date_range = []
    for i in range((end_date - start_date).days + 1):
        date = start_date + timedelta(days=i)
        day_sales = sales.filter(sale_date=date).aggregate(total=Sum('final_amount'))['total'] or 0
        day_expenses = expenses.filter(date=date).aggregate(total=Sum('amount'))['total'] or 0
        date_range.append({
            'date': date,
            'sales': day_sales,
            'expenses': day_expenses,
            'profit': day_sales - day_expenses,
        })

    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'profit': profit,
        'date_range': date_range,
    }
    return render(request, 'farm/profit_loss.html', context)

