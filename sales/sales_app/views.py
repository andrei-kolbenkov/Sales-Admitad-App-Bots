from django.shortcuts import render, redirect, get_object_or_404
from . models import Shop, Product, Coupon, CategoryShop, UserTG
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.db.models import Count, Q, F, ExpressionWrapper, IntegerField, Case, When, Value, BooleanField
from django.core.paginator import Paginator
from django.db.models.functions import Ceil
from django.contrib.postgres.search import SearchQuery, SearchVector, SearchRank
from django.db import connection
from transliterate import translit
from itertools import product, chain, permutations
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserTGSerializer
from django.http import JsonResponse
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def generate_translit_variants(query):
    """
    Генерирует список вариантов поискового запроса:
    - Исходный запрос
    - Транслитерированный с русского на английский
    - Транслитерированный с английского на русский
    """
    try:
        # Транслитерация в обе стороны
        translit_to_eng = translit(query, 'ru', reversed=True)
        # translit_to_rus = translit(query, 'ru')
    except Exception:
        # Если транслитерация не применима
        translit_to_eng = query
        # translit_to_rus = query

    # Убираем дубликаты
    return list(set([query, translit_to_eng]))


def all(request):
    search_query = request.GET.get('search', '')
    
    sort_order = request.GET.get('sort', '')
    # Получение текущей страницы из GET-параметра
    page_number = int(request.GET.get('page', 1))
    if search_query and not sort_order:
        limit = 1000  # Ограничение на 500 записей
    else:
        limit = 50
    exclude_shop_id=25179
    
    if page_number > 1:
        offset = limit*(page_number-1)
    else:
        offset = 0

    if search_query:
        search_variants = generate_translit_variants(search_query)
        split_variants = [variant.split() for variant in search_variants]
        num_words = len(search_query.split())
        all_words = list(set(chain.from_iterable(split_variants)))
        unique_combinations = set(
            tuple(sorted(combo)) for combo in permutations(all_words, num_words)
        )
        combinations = [' '.join(combo) for combo in unique_combinations]

        # Формируем условие для фильтрации (по всем вариантам)
        query_conditions = Q()
        for variant in combinations:
            query = SearchQuery(variant, config='russian')
            query_conditions |= Q(search=query)


        # vector = SearchVector('name', config='russian')

        if sort_order:
            # products = Product.objects.filter(query_conditions).annotate(starts_with=Case(When(name__istartswith=search_query, then=Value(1)), default=Value(0), output_field=IntegerField())).only('name', 'price', 'old_price', 'image', 'sale', 'url', 'shop_id').exclude(shop_id=exclude_shop_id).order_by(sort_order)[offset:offset + limit]
            products = Product.objects.filter(query_conditions).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).exclude(shop_id=exclude_shop_id).order_by(sort_order)[offset:offset + limit]
        else:
            products = Product.objects.filter(query_conditions).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).exclude(shop_id=exclude_shop_id).order_by()[offset:offset + limit]
    
    else:
        if sort_order == '-sale':
            products = Product.objects.filter(price__isnull=False).only('name', 'price','old_price', 'image', 'sale', 'url', 'shop_id').exclude(shop_id=exclude_shop_id).order_by(sort_order)[offset:offset + limit]
        elif sort_order in ['price', '-price']:
            products = Product.objects.only('name', 'price', 'old_price', 'image', 'sale', 'url', 'shop_id').exclude(shop_id=exclude_shop_id).order_by(sort_order)[offset:offset + limit]
        else:
            products = Product.objects.only('name', 'price', 'old_price', 'image', 'sale', 'url', 'shop_id').exclude(shop_id=exclude_shop_id).order_by()[offset:offset + limit]
            
    count = len(products)
    if search_query and not sort_order:
        page_obj = sorted(products, key=lambda obj: (not obj.name.upper().startswith(search_query.upper()), obj.name))
    else:
        page_obj = products
    if count >= limit:
        has_next = page_number + 1
    else:
        has_next = None

    if page_number > 1:
        has_previous = page_number - 1
    else:
        has_previous = None

    return render(request, 'sales_app/all.html', {'page_obj': page_obj, 'has_previous': has_previous,
        'has_next': has_next, 'number': page_number, 'order': sort_order})


def show_shops(request):
    query = request.GET.get('search')

    # Optimize the query using select_related for ForeignKey or OneToOne relationships
    if query:
        words = query.split()  # Разбиваем запрос на отдельные слова
        shops = Shop.objects.annotate(coupon_count=Count('promocodes')).filter(coupon_count__gt=0).filter(*[Q(name__icontains=word) for word in words]).only('shop_id', 'category', 'name', 'image').order_by("name").prefetch_related('category')
    else:
        shops = Shop.objects.annotate(coupon_count=Count('promocodes')).filter(coupon_count__gt=0).all().only('shop_id', 'category', 'name', 'image').order_by("name").prefetch_related('category')

    return render(
        request,
        'sales_app/show_shops.html',
        {'shops': shops},
    )


def show_shop_item(request, shop_id):
    shop = Shop.objects.get(pk=shop_id)
    coupons = Coupon.objects.filter(shop=shop)
    for coupon in coupons:
        if coupon.discount is not None:
            if coupon.currency == '%':
                if int(coupon.discount) >= 30:
                    coupon.name = f"1{coupon.name}"
                elif coupon.code in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН', None]:
                    coupon.name = f"2{coupon.name}"
                else:
                    coupon.name = f"3{coupon.name}"
            elif coupon.code in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН', None]:
                coupon.name = f"2{coupon.name}"
            else:
                coupon.name = f"3{coupon.name}"
                
            if (str(coupon.currency) not in coupon.name) and (str(coupon.discount) != '1'):
                coupon.name = f"{coupon.name} - Скидка {coupon.discount}{coupon.currency}"
        elif coupon.code in ['NOT REQUIRED', 'NOT REQUIRE', 'НЕ НУЖЕН', None]:
            coupon.name = f"2{coupon.name}"
        else:
            coupon.name = f"3{coupon.name}"

    return render(
        request,
        'sales_app/show_shop_item.html',
        {'shop': shop, 'coupons': coupons},
    )

def show_categories(request):
    shops = Shop.objects.annotate(coupon_count=Count('promocodes')).filter(coupon_count__gt=0).order_by("name")
    categories = CategoryShop.objects.all().annotate(store_count=Count('shops')).order_by("name")
    return render(
        request,
        'sales_app/show_categories.html',
        {'shops': shops, 'categories': categories}
        ,)


def category_shops(request, category_id):
    search_query = request.GET.get('search')
    category = CategoryShop.objects.get(pk=category_id)
    if search_query:
        words = search_query.split()
        shops = Shop.objects.annotate(coupon_count=Count('promocodes')).filter(coupon_count__gt=0).filter(category=category_id).filter(*[Q(name__icontains=word) for word in words])
    else:
        shops = Shop.objects.annotate(coupon_count=Count('promocodes')).filter(coupon_count__gt=0).filter(category=category_id)

    return render(request, 'sales_app/category_shops.html', {'shops': shops, 'search_query': search_query, 'category': category})


def shops_products(request):
    query = request.GET.get('search')
    excluded_shop_names = ['lamoda ru', 'xcom-shop.ru', 'Glasseslit WW', 'Мегамаркет', 'ChicMe WW', 'Boutiquefeel WW', 'Яндекс.Маркет', 'ЭПЛ Даймонд', 'Онлайн-кинотеатр START', 'Lichi', 'ПУЛЬТ.РУ', 'premier.one', 'AliExpress WW', 'AliExpress RU&CIS NEW']
    if query:
        words = query.split()  # Разбиваем запрос на отдельные слова
        shops = Shop.objects.filter(*[Q(name__icontains=word) for word in words]).only('shop_id', 'category', 'name', 'image').exclude(name__in=excluded_shop_names).order_by("name").prefetch_related('category')
    else:
        shops = Shop.objects.all().only('shop_id', 'category', 'name', 'image').exclude(name__in=excluded_shop_names).order_by("name").prefetch_related('category')

    return render(
        request,
        'sales_app/shop_products.html',
        {'shops': shops},
    )





def category_view(request, shop_id):
    shop = Shop.objects.get(pk=shop_id)
    search_query = request.GET.get('search', '')
    sort_order = request.GET.get('sort', 'name')
    # Получение текущей страницы из GET-параметра
    page_number = int(request.GET.get('page', 1))
    limit = 50  # Ограничение на 10 записей

    if page_number > 1:
        offset = limit * (page_number - 1)
    else:
        offset = 0

    if search_query:
        search_variants = generate_translit_variants(search_query)
        split_variants = [variant.split() for variant in search_variants]
        num_words = len(search_query.split())
        all_words = list(set(chain.from_iterable(split_variants)))
        unique_combinations = set(
            tuple(sorted(combo)) for combo in permutations(all_words, num_words)
        )
        combinations = [' '.join(combo) for combo in unique_combinations]

        # Формируем условие для фильтрации (по всем вариантам)
        query_conditions = Q()
        for variant in combinations:
            query = SearchQuery(variant, config='russian')
            query_conditions |= Q(search=query)
        # vector = SearchVector('name', config='russian')

        if sort_order == '-sale':
            products = Product.objects.filter(shop_id=shop_id).filter(query_conditions).annotate(
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-starts_with', '-sale')[offset:offset + limit]
        elif sort_order in ['price', '-price']:
            products = Product.objects.filter(shop_id=shop_id).filter(query_conditions).annotate(
                starts_with=Case(
                    When(name__istartswith=search_query, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField()
                )
            ).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-starts_with', sort_order)[offset:offset + limit]
        else:
            products = Product.objects.filter(shop_id=shop_id).filter(query_conditions).annotate(
                    starts_with=Case(
                        When(name__istartswith=search_query, then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField()
                    )
                ).only(
                'name', 'price', 'old_price', 'image', 'sale', 'url'
            ).order_by('-starts_with')[offset:offset + limit]
    else:
        if sort_order == '-sale':
            products = Product.objects.filter(shop_id=shop_id).filter(price__isnull=False).only('name', 'price', 'old_price', 'image', 'sale',
                                                                        'url').order_by(sort_order)[
                       offset:offset + limit]
        elif sort_order in ['price', '-price']:
            products = Product.objects.filter(shop_id=shop_id).only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by(sort_order)[
                       offset:offset + limit]
        else:
            products = Product.objects.filter(shop_id=shop_id).only('name', 'price', 'old_price', 'image', 'sale', 'url').order_by()[
                       offset:offset + limit]

    count = len(products)
    page_obj = products
    if count >= limit:
        has_next = page_number + 1
    else:
        has_next = None

    if page_number > 1:
        has_previous = page_number - 1
    else:
        has_previous = None

    return render(request, 'sales_app/products.html', {'page_obj': page_obj, 'has_previous': has_previous,
                                                  'has_next': has_next, 'number': page_number, 'order': sort_order, 'shop': shop})


def redirect_to(request):
    yclid = request.GET.get('yclid')
    # if yclid:
    #     LinkClick.objects.create(yclid=yclid, clicked_at=timezone.now())

    return redirect(f'https://t.me/coupons186_bot/?start={yclid}')


def redirect_to2(request):
    yclid = request.GET.get('yclid')
    # if yclid:
    #     LinkClick.objects.create(yclid=yclid, clicked_at=timezone.now())

    return redirect(f'https://t.me/products186_bot/?start={yclid}')


def main(request):
    shops = Shop.objects.all().only('image')
    return render(request, 'sales_app/main.html', {'shops': shops})


def redirect_main(request):
    return redirect('sales_app:redirect_to')




@api_view(['POST'])
def add_user(request):
    ALLOWED_REFERER = 'https://www.skidki186.ru'
    referer = request.META.get('HTTP_REFERER')
    logger.info(referer)
    if not referer or not referer.startswith(ALLOWED_REFERER):
        return JsonResponse({"success": False, "error": "Invalid request origin"}, status=403)

    user_id = request.data.get('id')  # Telegram ID из запроса

    if not user_id:
        return Response({"success": False, "error": "ID is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Получаем текущие данные пользователя
    user = UserTG.objects.filter(id=user_id).first()

    # Собираем обновляемые поля, если они есть в запросе
    update_fields = {}
    if 'username' in request.data:
        update_fields['username'] = request.data.get('username')
    if 'last_date_prom' in request.data:
        update_fields['last_date_prom'] = request.data.get('last_date_prom')
    if 'last_date_prod' in request.data:
        update_fields['last_date_prod'] = request.data.get('last_date_prod')

    if user:
        # Обновляем только те поля, которые были переданы
        for field, value in update_fields.items():
            setattr(user, field, value)
        user.save()
        created = False
    else:
        # Если пользователя нет, то создаем нового
        user = UserTG.objects.create(id=user_id, **update_fields)
        created = True

    return Response(
        {"success": True, "user": UserTGSerializer(user).data, "created": created},
        status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )



def offline_view(request):
    return render(request, 'sales_app/offline.html')