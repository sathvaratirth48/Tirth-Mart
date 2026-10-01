from django.urls import path

from app_modules.adminapp import views

urlpatterns = [
    path("", views.index, name="admin_index"),
    path("analytics/", views.analytics, name="analytics"),

    # Delivery Boys
    path("update_DeliveryBoy/<int:id>/", views.update_DeliveryBoy, name="update_DeliveryBoy"),
    path("list_DeliveryBoys/", views.list_DeliveryBoys, name="list_DeliveryBoys"),
    path("delete_DeliveryBoy/<int:id>/", views.delete_DeliveryBoy, name="delete_DeliveryBoy"),

    # Cart
    path("list_Cart/", views.list_Cart, name="list_Cart"),

    # Admin auth
    path("register/", views.register_view, name="admin_register"),
    path("login/", views.login_view, name="admin_login"),
    path("logout/", views.logout_view, name="logout"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("parent-dashboard/", views.parent_dashboard, name="parent_dashboard"),
    path("user-dashboard/", views.user_dashboard, name="user_dashboard"),

    path("approve/<int:user_id>/", views.approve_user, name="approve_user"),
    path("reject/<int:user_id>/", views.reject_user, name="reject_user"),

    # Categories
    path("create_Category/", views.create_Category, name="create_Category"),
    path("list_Category/", views.list_Category, name="list_Category"),
    path("update_Category/<int:pk>/", views.update_Category, name="update_Category"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),

    # Products
    path("create_Product", views.create_Product, name="create_Product"),
    path("list_Product/", views.list_Product, name="list_Product"),
    path("update_Product/<int:id>/", views.update_Product, name="update_Product"),
    path("delete_Product/<int:id>/", views.delete_Product, name="delete_Product"),

    # Orders (legacy CRUD screens)
    path("list_Orders/", views.list_Orders, name="list_Orders"),
    path("update_Orders/<int:id>/", views.update_Orders, name="update_Orders"),
    path("delete_Orders/<int:id>/", views.delete_Orders, name="delete_Orders"),

    # Orders (operational dashboard)
    path("orders/", views.order_list, name="admin_order_list"),
    path("orders/<int:pk>/", views.order_detail, name="admin_order_detail"),
    path("orders/<int:pk>/status/", views.update_order_status, name="admin_update_order_status"),
    path("orders/<int:order_pk>/assign/", views.assign_order, name="admin_assign_order"),

    # Payments
    path("payments/", views.payment_list, name="admin_payment_list"),
    path("payments/<int:pk>/status/", views.update_payment_status, name="admin_update_payment_status"),

    # Notifications
    path("notifications/", views.notification_list, name="admin_notification_list"),
    path("notifications/clear/", views.admin_clear_notifications, name="admin_clear_notifications"),

    # Contact messages
    path("contacts/", views.contact_list, name="admin_contact_list"),
    path("contacts/<int:pk>/status/", views.contact_update_status, name="admin_contact_status"),
    path("contacts/<int:pk>/delete/", views.contact_delete, name="admin_contact_delete"),

    # Admin profile
    path("profile/", views.admin_profile_view, name="admin_profile_view"),
    path("profile/edit/", views.admin_profile_edit, name="admin_profile_edit"),
]
