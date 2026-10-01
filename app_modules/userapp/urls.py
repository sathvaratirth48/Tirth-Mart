from django.urls import path

from app_modules.userapp import views

urlpatterns = [
    path('', views.home_page, name='index'),


    #Login Start
    path('register/', views.register_view, name='user_register'),
    path('login/', views.login_view, name='user_login'),
    path('logout/', views.logout_view, name='user_logout'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('reject/<int:user_id>/', views.reject_user, name='reject_user'),
    #Login End

    #User Profile Start
    path('profile/', views.profile_view, name='profile_view'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('profile/delete-image/', views.delete_profile_image, name='delete_profile_image'),
    #User Profile End

    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('shop_page/', views.shop_page, name='shop_page'),
    path('api/search-suggestions/', views.search_suggestions_ajax, name='search_suggestions'),
    path('api/promo/validate/', views.validate_promo, name='validate_promo'),
    path("product/<int:pk>/", views.product_detail_view, name="product_detail"),
    path("product/<int:pk>/review/", views.submit_review, name="submit_review"),
    path("cart/", views.cart_view, name="cart"),
    path("api/cart/add/", views.add_to_cart_ajax),
    path("api/cart/update/", views.update_cart_ajax),
    path("api/cart/remove/", views.remove_cart_ajax),
    path("api/cart/", views.get_cart_ajax),
    path("api/cart/count/", views.get_cart_count_ajax),
    path("api/wishlist/toggle/", views.toggle_wishlist_ajax),
    path("api/wishlist/count/", views.get_wishlist_count_ajax),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("checkout/", views.checkout_view, name="checkout"),
    path("orders/<int:pk>/confirm-upi/", views.confirm_upi_payment, name="confirm_upi_payment"),
    path("orders/", views.order_list_view, name="order_list"),
    path("orders/<int:pk>/", views.order_detail_view, name="order_detail"),
    path("orders/<int:pk>/cancel/", views.cancel_order_view, name="cancel_order"),
    path("orders/<int:pk>/cancelled/", views.order_detail_cancelled, name="order_detail_cancelled"),
    path("orders/<int:pk>/poll/", views.order_status_poll, name="order_status_poll"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notifications/clear/", views.clear_notifications, name="clear_notifications"),
    path("api/notifications/count/", views.notif_count_ajax, name="notif_count"),
    path("api/notifications/recent/", views.notif_recent_ajax, name="notif_recent"),
    path("api/notifications/<int:pk>/read/", views.notif_mark_read_ajax, name="notif_mark_read"),

]
