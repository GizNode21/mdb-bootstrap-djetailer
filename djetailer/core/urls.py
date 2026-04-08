from django.urls import path
from django.contrib.auth.views import LoginView
from .views import HomeView, ProductDetail, CheckoutView, CheckoutEditView, add_to_cart, remove_from_cart, OrderSummaryView, remove_single_item_from_cart, PaymentView, create_payment, success # webhook_received

app_name="core"
urlpatterns = [
    path('', HomeView.as_view(), name="item-list"),
    path('products/<slug>/product/', ProductDetail.as_view(), name="product-detail"),
    path('checkout/edit/<int:pk>/', CheckoutEditView.as_view(), name="check-out-edit"),
    path('checkout/', CheckoutView.as_view(), name="check-out"),
    path('order-summary/', OrderSummaryView.as_view(), name="order-summary"),
    path("add-to-cart/<slug>/", add_to_cart, name="add-to-cart"),
    path("remove-from-cart/<slug>/", remove_from_cart, name="remove-from-cart"),
    path("accounts/login/", LoginView.as_view(template_name="account/login.html"), name="login"),
    path("remove-item-from-cart/<slug>/", remove_single_item_from_cart, name="remove-single-item-from-cart"),
    path("payment/<payment_option>/", PaymentView.as_view(), name="payment"),
    path("create-payment-intent/", create_payment, name="create-payment"),
    path("return/", success, name="return"),
    #path("webhook/", webhook_received, name="webhook")
]