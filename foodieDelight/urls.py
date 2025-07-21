from django.contrib import admin
from django.urls import path, include
from myapp import views 
from django.conf import settings 
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',views.index,name="index"),
    path('contact/',views.contact_us,name="contact"),
    path('about/',views.about,name="about"),
    path('team/',views.team_members,name="team"),
    path('dishes/',views.all_dishes,name="all_dishes"),
    path('register/',views.register,name="register"),
    path('check_user_exists/',views.check_user_exists,name="check_user_exist"),
    path('login/', views.signin, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.user_logout, name='logout'),
    path('dish/<int:id>/', views.single_dish, name='dish'),
    path('cart/', views.view_cart, name='view_cart'),
    path('add-to-cart/<int:dish_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/<int:item_id>/', views.update_cart, name='update_cart'), 
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update_quantity/<int:item_id>/', views.update_quantity, name='update_quantity'),
    path('dish/<int:dish_id>/', views.dish_detail, name='dish_detail'),
    path('remove_item/<int:item_id>/', views.remove_item, name='remove_item'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('checkout/', views.checkout, name='checkout'),  # Your existing checkout page
    path('process_payment/', views.process_payment, name='process_payment'),  # New payment processing view
    path('success/', views.success, name='payment_success'), 
    path('payment_cancel/', views.payment_cancel, name='payment_cancel'),
]+static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
