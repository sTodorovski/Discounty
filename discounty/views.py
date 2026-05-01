import json
import random
from datetime import timedelta, date, datetime
from django.core.mail import EmailMultiAlternatives
from django.core.paginator import Paginator
from django.db.models import Q, Count, Case, When, Value, IntegerField
from django.db.models.functions import Abs, Random
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from openpyxl import Workbook
from .models import Product, Market
from django.template.loader import render_to_string

# Create your views here.
def index(request):
    market_list = Market.objects.all()
    product_list = Product.objects.all()
    query = request.GET.get('search')
    sort = request.GET.get('sort')
    results = []

    if query:
        results = Product.objects.filter(name__icontains=query)

        if sort == 'price_asc':
            results = results.order_by('price')
        elif sort == 'price_desc':
            results = results.order_by('-price')
        elif sort == 'name_asc':
            results = results.order_by('name')
        elif sort == 'name_desc':
            results = results.order_by('-name')
        elif sort == 'discount_desc':
            results = results.order_by('-discount_percentage')

    return render(request, 'index.html', {'market_list': market_list , 'product_list': product_list, 'results': results, 'query': query})

def markets(request):
    market_list = Market.objects.all()
    return render(request, "markets.html", {'market_list': market_list})

def ajax_search_products(request):
    query = request.GET.get('search', '')
    page_number = int(request.GET.get('page', 1))
    sort = request.GET.get('sort')
    market_id = request.GET.get('market')
    discount = request.GET.get('discount')

    if query:
        results = Product.objects.filter(name__icontains=query)
    else:
        results = Product.objects.order_by('-id')

    if market_id:
        results = results.filter(market_id=market_id)

    if discount:
        try:
            results = results.filter(discount_percentage__gte=int(discount))
        except ValueError:
            pass

    if sort == 'price_asc':
        results = results.order_by('price')
    elif sort == 'price_desc':
        results = results.order_by('-price')
    elif sort == 'name_asc':
        results = results.order_by('name')
    elif sort == 'name_desc':
        results = results.order_by('-name')
    elif sort == 'discount_desc':
        results = results.annotate(
            has_discount=Case(
                When(discount_percentage__gt=0, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by('has_discount', '-discount_percentage')

    paginator = Paginator(results, 20)
    page_obj = paginator.get_page(page_number)

    html = render_to_string('partials/results.html', {
        'results': page_obj
    })

    return JsonResponse({
        'html': html,
        'has_next': page_obj.has_next()
    })

def deals(request):
    market_list = Market.objects.all()
    products = Product.objects.filter(discount_price__isnull=False).order_by(-Abs('discount_percentage'))
    market_id = request.GET.get('market')
    page_number = int(request.GET.get('page', 1))

    if market_id and market_id != "":
        products = products.filter(market_id=market_id)

    paginator = Paginator(products, 20)
    page_obj = paginator.get_page(page_number)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        html = render_to_string('partials/results.html', {'results': page_obj})
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next()
        })

    return render(request, 'deals.html', {'market_list': market_list, 'results': page_obj})

def about(request):
    return render(request, 'about.html')

def favorites(request):
    return render(request, "favorites.html")
def favorites_data(request):
    ids = request.GET.get("ids", "")
    ids_list = ids.split(",") if ids else []

    products = Product.objects.filter(id__in=ids_list)

    html = render_to_string("partials/results.html", {
        "results": products
    })

    return JsonResponse({"html": html})

def product_detail(request, id):
    product = Product.objects.get(id=id)

    if product.discount_date_to:
        today = date.today()
        days_left = (product.discount_date_to - today).days

        product.is_ending_soon = 0 <= days_left <= 2
    else:
        product.is_ending_soon = False

    html = render_to_string("partials/product_detail.html", {
        "product": product
    })

    return JsonResponse({"html": html})

def market_detail(request, id):
    market = Market.objects.get(id=id)

    products = Product.objects.filter(market=market)

    start = request.GET.get("start")
    end = request.GET.get("end")
    date_str = request.GET.get("date")

    if start and end:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        end_date = datetime.strptime(end, "%Y-%m-%d").date() - timedelta(days=1)

        products = products.filter(
            discount_price__isnull=False
        ).filter(
            Q(
                discount_date_from=start_date,
                discount_date_to=end_date
            ) |
            Q(
                discount_date_from__isnull=True,
                discount_date_to=end_date
            )
        )


    elif date_str:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        products = products.filter(
            discount_price__isnull=False
        ).filter(
            Q(
                discount_date_from__lte=selected_date,
                discount_date_to__gte=selected_date
            ) |
            Q(
                discount_date_from__isnull=True,
                discount_date_to__gte=selected_date
            )
        )


    else:
        today = date.today()
        products = products.filter(
            discount_price__isnull=False
        ).filter(
            Q(
                discount_date_from__lte=today,
                discount_date_to__gte=today
            ) |
            Q(
                discount_date_from__isnull=True,
                discount_date_to__gte=today
            )
        )

    return render(request, 'market_detail.html', {
        'market': market,
        'products': products
    })

def market_events(request, id):
    events = (
        Product.objects
        .filter(market_id=id, discount_price__isnull=False)
        .values("discount_date_from", "discount_date_to")
        .annotate(product_count=Count("id"))
    )

    today = date.today()

    result = []

    colors = ["#ffeb3b", "#0097a7", "#1a237e", "#b71c1c", "#1b5e20", "#4fc3f7", "#424242", "#a5d6a7", "#ab47bc", "#76ff03", "#7e57c2", "#26c6da", "#e1bee7", "#39a275", "#df1c44", "#2554C7", "#7e57c2", "#d500f9", "#ffab00", "#4e342e", "#212121", "#64b5f6", "#e57373"]

    random.shuffle(colors)

    for i, e in enumerate(events):
        color = colors[i % len(colors)]

        start_date = e["discount_date_from"] or today
        end_date = e["discount_date_to"]

        if not end_date:
            continue

        result.append({
            "title": f"{e['product_count']} products",
            "start": start_date.strftime("%Y-%m-%d"),
            "end": (end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
            "color": color
        })

    return JsonResponse(result, safe=False)

def shopping_list(request):
    return render(request, 'shopping-list.html')

def shopping_list_add(request, id):
    product = Product.objects.get(id=id)

    html = render_to_string("partials/shopping_list_add.html", {
        "product": product
    })

    return JsonResponse({"html": html})

def shopping_list_data(request):
    ids = request.GET.get("ids", "")
    ids_list = ids.split(",") if ids else []
    quantities_raw = request.GET.get("quantities", "{}")

    try:
        quantities = json.loads(quantities_raw)
    except:
        quantities = {}

    products = Product.objects.filter(id__in=ids_list)

    html = render_to_string("partials/shopping_list_results.html", {
        "results": products,
        "quantities": quantities
    })

    return JsonResponse({"html": html})

def export_shopping_list(request):
    ids = request.GET.get("ids", "")
    quantities_raw = request.GET.get("quantities", "{}")

    ids_list = ids.split(",") if ids else []
    quantities = json.loads(quantities_raw)

    products = Product.objects.filter(id__in=ids_list)

    wb = Workbook()
    ws = wb.active
    ws.title = "Shopping List"

    ws.append(["Product", "Quantity", "Price", "Market", "Total"])

    grand_total = 0

    for product in products:
        qty = quantities.get(str(product.id), 0)
        price = product.discount_price if product.discount_price else product.price
        total = price * qty
        market = str(product.market)
        grand_total += total

        ws.append([product.name, qty, price, market, total])

    ws.append([])
    ws.append(["", "", "TOTAL:", grand_total])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="shopping_list.xlsx"'

    wb.save(response)
    return response

def email_shopping_list(request):
    email = request.GET.get("email")
    ids = request.GET.get("ids", "")
    quantities_raw = request.GET.get("quantities", "{}")

    if not email:
        return JsonResponse({"error": "Email is required"}, status=400)

    ids_list = ids.split(",") if ids else []
    quantities = json.loads(quantities_raw)

    products = Product.objects.filter(id__in=ids_list)

    items = []
    total = 0

    for product in products:
        qty = quantities.get(str(product.id), 0)
        price = product.discount_price if product.discount_price else product.price
        subtotal = price * qty
        total += subtotal

        items.append({
            "name": product.name,
            "market": str(product.market),
            "quantity": qty,
            "price": price,
            "subtotal": subtotal
        })

    html_content = render_to_string("emails/shopping_list.html", {
        "items": items,
        "total": total
    })

    email_msg = EmailMultiAlternatives(
        subject="Your Shopping List",
        body="Your shopping list is attached.",
        to=[email],
    )

    email_msg.attach_alternative(html_content, "text/html")

    try:
        email_msg.send()
    except Exception as e:
        return JsonResponse({"error": "Email failed"}, status=500)

    return JsonResponse({"success": True})