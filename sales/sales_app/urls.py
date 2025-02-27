from django.urls import path, re_path
from . import views

app_name = 'sales_app'



urlpatterns = [
    path('', views.main, name='main'),
    path('promokodi1/', views.redirect_to, name='redirect_to'),
    path('promokodi', views.show_shops, name='shops'),
    path('promokodi/<int:shop_id>', views.show_shop_item, name='shop_item'),
    path('categories', views.show_categories, name='categories'),
    path('category/<int:category_id>', views.category_shops, name='category_shops'),
    path('shops_products', views.shops_products, name='shops_products'),
    path('catalog', views.all, name='all'),
    path('promokodi/<int:shop_id>/categories', views.category_view, name='category_view'),
    path('api/add_user/', views.add_user, name='add_user'),
    path('offline/', views.offline_view, name='offline'),
]
