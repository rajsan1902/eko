from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Max, Sum, Q
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import *


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
    total_batches = SpawnBatch.objects.count() or 0
    active_batches = SpawnBatch.objects.filter(status='active').count()
    active_beds = SpawnBatch.objects.filter(status='active').aggregate(total=Sum('number_of_bags'))['total'] or 0    
    total_beds = SpawnBatch.objects.filter().aggregate(total=Sum('number_of_bags'))['total'] or 0
    contaminated_beds = SpawnBatch.objects.filter(status='condaminated').aggregate(total=Sum('number_of_bags'))['total'] or 0

    # Current month's sales
    current_month = timezone.now().month
    current_year = timezone.now().year
    monthly_sales = Sale.objects.filter(
        sale_date__year=current_year,
        sale_date__month=current_month
    ).aggregate(total=Sum('sale_amount'))['total'] or 0

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
        'active_beds' : active_beds,
        'total_beds': total_beds,
        'contaminated_beds': contaminated_beds,

        'monthly_sales': monthly_sales,
        'monthly_expenses': monthly_expenses,
        'profit': monthly_sales - monthly_expenses,
        'recent_sales': recent_sales,
        'recent_harvests': recent_harvests,
    }
    return render(request, 'farm/dashboard.html', context)

@login_required
def batch_list(request):
    batches = SpawnBatch.objects.all().order_by('-batch_date')
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
        max_batch_code = SpawnBatch.objects.aggregate(Max('batch_code'))['batch_code__max']

        if max_batch_code is None:
            new_batch_code = 1
        else:
            new_batch_code = int(max_batch_code) + 1
        tdate = timezone.now().date()
        form = SpawnBatchForm(initial={'batch_code': new_batch_code, 'batch_date':tdate})
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


            # Update batch total harvested
            # batch = harvest.batch
            # total_harvested = batch.harvests.aggregate(total=Sum('quantity_g'))['total'] or 0
            # batch.total_harvested = total_harvested
            # batch.save(update_fields=['total_harvested'])

            messages.success(request, f'Harvest recorded! {harvest.quantity_g}g added to inventory.')
            return redirect('harvest_list')
    else:
        form = HarvestForm()

    return render(request, 'farm/harvest_form.html', {'form': form, 'title': 'Record Harvest'})

def sale_create(request):
    if request.method == 'POST':
        form = SaleForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    sale = form.save(commit=False)
                    sale.created_by = request.user

                    # Handle customer selection/creation
                    customer_search = form.cleaned_data.get('customer_search')
                    new_customer_name = form.cleaned_data.get('new_customer_name')
                    new_customer_mobile = form.cleaned_data.get('new_customer_mobile')
                    new_customer_email = form.cleaned_data.get('new_customer_email')
                    new_customer_address = form.cleaned_data.get('new_customer_address')

                    if customer_search and customer_search.isdigit():
                        # Customer selected from search (ID stored)
                        try:
                            customer = Customer.objects.get(id=int(customer_search))
                            sale.customer = customer
                        except Customer.DoesNotExist:
                            pass
                    elif new_customer_name and new_customer_mobile:
                        # Create new customer
                        customer, created = Customer.objects.get_or_create(
                            mobile=new_customer_mobile,
                            defaults={
                                'name': new_customer_name,
                                'email': new_customer_email,
                                'address': new_customer_address
                            }
                        )
                        if not created and customer.name != new_customer_name:
                            customer.name = new_customer_name
                            customer.save()
                        sale.customer = customer

                    sale.save()

                    messages.success(request, f'Sale created! {sale.customer_name} bought {sale.sale_quantity_g}g for ₹{sale.sale_amount}')
                    return redirect('sale_list')
            except ValueError as e:
                messages.error(request, str(e))
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = SaleForm()

    # Get summary data for cards
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    available_stock = MushroomInventory.objects.filter(
        status='available'
    ).aggregate(total=Sum('quantity_g'))['total'] or 0

    sold_today = Sale.objects.filter(
        sale_date=today
    ).aggregate(total=Sum('sale_quantity_g'))['total'] or 0

    sold_this_month = Sale.objects.filter(
        sale_date__year=current_year,
        sale_date__month=current_month
    ).aggregate(total=Sum('sale_quantity_g'))['total'] or 0

    today_revenue = Sale.objects.filter(
        sale_date=today
    ).aggregate(total=Sum('sale_amount'))['total'] or 0

    return render(request, 'farm/create_sale.html', {
        'form': form,
        'available_stock': available_stock,
        'sold_today': sold_today,
        'sold_this_month': sold_this_month,
        'today_revenue': today_revenue,
    })

@login_required
def sale_list(request):
    """Sales list with summary cards"""

    # Get current date and month
    today = timezone.now().date()
    current_month = today.month
    current_year = today.year

    # Calculate available stock
    available_stock = MushroomInventory.objects.filter(
        status='available'
    ).aggregate(total=Sum('quantity_g'))['total'] or 0

    # Calculate sold today
    sold_today = Sale.objects.filter(
        sale_date=today
    ).aggregate(total=Sum('sale_quantity_g'))['total'] or 0

    # Calculate sold this month
    sold_this_month = Sale.objects.filter(
        sale_date__year=current_year,
        sale_date__month=current_month
    ).aggregate(total=Sum('sale_quantity_g'))['total'] or 0

    # Get all sales for the list
    sales = Sale.objects.all().order_by('-sale_date')

    # Calculate today's revenue
    today_revenue = Sale.objects.filter(
        sale_date=today
    ).aggregate(total=Sum('sale_amount'))['total'] or 0

    # Calculate monthly revenue
    monthly_revenue = Sale.objects.filter(
        sale_date__year=current_year,
        sale_date__month=current_month
    ).aggregate(total=Sum('sale_amount'))['total'] or 0

    context = {
        'available_stock': available_stock,
        'sold_today': sold_today,
        'sold_this_month': sold_this_month,
        'today_revenue': today_revenue,
        'monthly_revenue': monthly_revenue,
        'sales': sales,
    }

    return render(request, 'farm/sale_list.html', context)

def sale_detail(request, sale_id):
    """View sale details"""
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, 'farm/sale_detail.html', {'sale': sale})

def sale_invoice(request, sale_id):
    """Generate invoice for a sale"""
    sale = get_object_or_404(Sale, id=sale_id)
    return render(request, 'farm/sale_invoice.html', {'sale': sale})

def search_customers(request):
    """AJAX view to search customers"""
    query = request.GET.get('q', '')
    if query:
        customers = Customer.objects.filter(
            Q(name__icontains=query) | Q(mobile__icontains=query)
        )[:10]
        results = [
            {
                'id': c.id,
                'name': c.name,
                'mobile': c.mobile,
                'total_purchases': str(c.total_purchases),
                'total_quantity': c.total_quantity_g
            }
            for c in customers
        ]
    else:
        results = []
    return JsonResponse(results, safe=False)


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
def batch_edit(request, pk):
    batch = get_object_or_404(SpawnBatch, pk=pk)
    if request.method == 'POST':
        form = SpawnBatchForm(request.POST, instance=batch)
        if form.is_valid():
            form.save()
            return redirect('batch_list')
    else:
        form = SpawnBatchForm(instance=batch)
    return render(request, 'farm/batch_form.html', {'form': form})

@login_required
def batch_delete(request, pk):
    batch = get_object_or_404(SpawnBatch, pk=pk)
    if request.method == 'POST':
        batch.delete()
        messages.success(request, 'Batch deleted successfully!')
        return redirect('batch_list')
    return redirect('batch_list')

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
    total_sales = sales.aggregate(total=Sum('sale_amount'))['total'] or 0

    # Calculate expenses
    expenses = Expense.objects.filter(date__range=[start_date, end_date])
    total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

    profit = total_sales - total_expenses

    # Daily breakdown
    date_range = []
    for i in range((end_date - start_date).days + 1):
        date = start_date + timedelta(days=i)
        day_sales = sales.filter(sale_date=date).aggregate(total=Sum('sale_amount'))['total'] or 0
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

@login_required
def stock_list(request):
    stocks = Stock.objects.all().order_by('-created_at')

    # Calculate summary statistics
    total_items = stocks.count()
    low_stock_items = stocks.filter(quantity__lte=models.F('reorder_level')).count()

    context = {
        'stocks': stocks,
        'total_items': total_items,
        'low_stock_items': low_stock_items,
    }
    return render(request, 'stock/stock_list.html', context)

@login_required
def stock_create(request):
    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock item added successfully!')
            return redirect('stock_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StockForm()

    return render(request, 'stock/stock_form.html', {'form': form, 'title': 'Add New Stock'})

@login_required
def stock_update(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            form.save()
            messages.success(request, 'Stock item updated successfully!')
            return redirect('stock_list')
    else:
        form = StockForm(instance=stock)

    return render(request, 'stock/stock_form.html', {'form': form, 'title': 'Update Stock'})

@login_required
def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == 'POST':
        stock.delete()
        messages.success(request, 'Stock item deleted successfully!')
        return redirect('stock_list')
    return render(request, 'stock/stock_confirm_delete.html', {'stock': stock})

