from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include, re_path
from django.conf import settings
from discounty import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('markets', views.markets, name='markets'),
    path('ajax/search-products/', views.ajax_search_products, name='ajax_search_products'),
    path('deals/', views.deals, name='deals'),
    path('about/', views.about, name='about'),
    path('shopping-list/', views.shopping_list, name='shopping-list'),
    path('favorites/', views.favorites, name='favorites'),
    path('favorites-data/', views.favorites_data, name='favorites_data'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path("market/<int:id>/", views.market_detail, name="market_detail"),
    path('market/<int:id>/events/', views.market_events, name='market_events'),
    path("shopping-list/add/<int:id>/", views.shopping_list_add, name="shopping_list_add"),
    path('shopping-list-data/', views.shopping_list_data, name='shopping_list_data'),
    path('export-shopping-list/', views.export_shopping_list, name='export_shopping_list'),
    path('email-shopping-list/', views.email_shopping_list, name='email_shopping_list'),

]

urlpatterns += static('/images/', document_root=settings.BASE_DIR / 'images')
