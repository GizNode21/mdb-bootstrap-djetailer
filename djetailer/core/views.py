import stripe
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect, reverse
#from django.views.decorators.csrf import csrf_exempt
#from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic import ListView, DetailView, View
from django.utils import timezone
from django.http import JsonResponse #HttpResponse
from .forms import CheckoutForm
from .models import Item, OrderItem, Order, Address, Payment
# Create your views here.
class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                "object": order
            }
            return render(self.request, "order_summary.html", context)

        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order.")
            return redirect("/")
        return render(self.request, "order_summary.html")

class ProductDetail(DetailView):
    model = Item
    template_name = "item_detail.html"

def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid

class CheckoutEditView(View):
    
    def get(self, request, pk, *args, **kwargs):
        order = get_object_or_404(Order, id=pk)
        form = CheckoutForm(instance=order.shipping_address, prefix="first")
        form2 = CheckoutForm(instance=order.billing_address, prefix="second")
        context = {"form": form, "form2": form2, "object": order}
        shipping_address_qs = Address.objects.filter(
            user=self.request.user,
            address_type="S",
            default=True)
        if shipping_address_qs.exists():
            context.update({"default_shipping_address": shipping_address_qs[0]})
        billing_address_qs = Address.objects.filter(
            user=self.request.user,
            address_type="B",
            default=True)
        if billing_address_qs.exists():
            context.update({"default_billing_address": billing_address_qs[0]})
        return render(self.request, "checkout-page.html", context)
    
    def post(self, request, pk, *args, **kwargs):
        
        order = get_object_or_404(Order, id=pk)
        form = CheckoutForm(self.request.POST or None, instance=order.shipping_address, prefix="first")
        form2 = CheckoutForm(self.request.POST or None, instance=order.billing_address, prefix="second")
        if form.is_valid() and form2.is_valid():
            use_default_shipping = form.cleaned_data.get("use_default_shipping")
            #if form2.cleaned_data.get("set_default_shipping") == None:
                #form2.cleaned_data["set_default_shipping"] = form.cleaned_data.get("use_default_shipping")
            if use_default_shipping:
                address_qs = Address.objects.filter(user=self.request.user,
                address_type="S",
                default=True)
                if address_qs.exists():
                    shipping_address = address_qs[0]
                    order.shipping_address = shipping_address
                    order.save()
                else:
                    messages.info(self.request, "No default shipping address available")
                    return redirect(reverse("core:check-out-edit", kwargs={"pk": order.pk}))
            else:
                print("User is updating shipping address")
                shipping_address = form.cleaned_data.get("shipping_address")
                shipping_address2 = form.cleaned_data.get("shipping_address2")
                shipping_country = form.cleaned_data.get("shipping_country")
                shipping_zip = form.cleaned_data.get("shipping_zip")
                if not form.cleaned_data.get("billing_address"):
                    form.cleaned_data["billing_address"] = form2.cleaned_data.get("billing_address")
                if not form.cleaned_data.get("billing_address2"):
                    form.cleaned_data["billing_address2"] = form2.cleaned_data.get("billing_address2")
                if not form.cleaned_data.get("billing_country"):
                    form.cleaned_data["billing_country"] = form2.cleaned_data.get("billing_country")
                if not form.cleaned_data.get("billing_zip"):
                    form.cleaned_data["billing_zip"] = form2.cleaned_data.get("billing_zip")
                # TODO: add funtionality to fields
                #same_shipping_address = form.cleaned_data.get("same_shipping_address")
                #save_info = form.cleaned_data.get("save_info")
                payment_option = form.cleaned_data.get("payment_option")
                if not form2.cleaned_data.get("payment_option"):
                    form2.cleaned_data["payment_option"] = form.cleaned_data.get("payment_option")
                if is_valid_form([shipping_address, shipping_country, shipping_zip, payment_option]):
                    ship_address = Address.objects.get(id=order.shipping_address.id)
                    ship_address.street_address = shipping_address
                    ship_address.apartment_address = shipping_address2
                    ship_address.country = shipping_country
                    ship_address.zip = shipping_zip
                    ship_address.address_type = "S"
                        # Address(
                        #user=self.request.user,
                        #street_address=shipping_address,
                        #apartment_address=shipping_address2,
                        #country=shipping_country,
                        #zip=shipping_zip,
                        #address_type="S",
                    #)
                    ship_address.save()
                    order.shipping_address = ship_address
                    order.save()

                    set_default_shipping = form.cleaned_data.get("set_default_shipping")
                    #if form2.cleaned_data.get("set_default_shipping") == None:
                    #    form2.cleaned_data["set_default_shipping"] = form.cleaned_data.get("set_default_billing")
                    if set_default_shipping:
                        ship_address.default = True
                        ship_address.save()
                elif not payment_option:
                    messages.info(self.request, "Payment option not selected.")
                else:
                    messages.info(self.request, "Please fill in the required shipping address fields.")
            use_default_billing = form2.cleaned_data.get("use_default_billing")
            #if form.cleaned_data.get("use_default_billing") == None:
            #    form.cleaned_data["use_default_billing"] = form2.cleaned_data.get("use_default_billing")
            same_billing_address = form.cleaned_data.get("same_billing_address")
            #if form2.cleaned_data.get("same_billing_address") == None:
            #    form2.cleaned_data["same_billing_address"] = form.cleaned_data.get("same_billing_address")
            if same_billing_address:
                billing_address = ship_address
                billing_address.pk = None
                billing_address.save()
                billing_address.address_type = "B"
                billing_address.save()
                order.billing_address = billing_address
                order.save()

            elif use_default_billing:
                print("Using default billing address")
                address_qs = Address.objects.filter(user=self.request.user,
                address_type="B",
                default=True)
                if address_qs.exists():
                    billing_address = address_qs[0]
                    order.billing_address = billing_address
                    order.save()
                else:
                    messages.info(self.request, "No default billing address available")
                    return redirect("core:check-out-edit", kwargs={"pk": order.pk})
            else:
                print("User is updating billing address")
                billing_address = form2.cleaned_data.get("billing_address")
                billing_address2 = form2.cleaned_data.get("billing_address2")
                billing_country = form2.cleaned_data.get("billing_country")
                billing_zip = form2.cleaned_data.get("billing_zip")
                if not form2.cleaned_data.get("shipping_address"): 
                    form2.cleaned_data["shipping_address"] = form.cleaned_data.get("shipping_address")
                if not form2.cleaned_data.get("shipping_address2"):
                    form2.cleaned_data["shipping_address2"] = form.cleaned_data.get("shipping_address")
                if not form2.cleaned_data.get("shipping_country"):
                    form2.cleaned_data["shipping_country"] = form.cleaned_data.get("shipping_country")
                if not form2.cleaned_data.get("shipping_zip"):
                    form2.cleaned_data["shipping_zip"] = form.cleaned_data.get("shipping_zip")
                #same_shipping_address = form.cleaned_data.get("same_shipping_address")
                #save_info = form.cleaned_data.get("save_info")
                payment_option = form2.cleaned_data.get("payment_option")
                if is_valid_form([billing_address, billing_country, billing_zip, payment_option]):
                    bill_address = Address.objects.get(id=order.billing_address.id)
                    bill_address.street_address = billing_address
                    bill_address.apartment_address = billing_address2
                    bill_address.country = billing_country
                    bill_address.zip = billing_zip
                    bill_address.address_type = "B"
                        #Address(
                        #user=self.request.user,
                        #street_address=billing_address,
                        #apartment_address=billing_address2,
                        #country=billing_country,
                        #zip=billing_zip,
                        #address_type="B",
                    #)
                    bill_address.save()
                    order.billing_address = bill_address
                    order.save()

                    set_default_billing = form2.cleaned_data.get("set_default_billing")
                    #if form.cleaned_data.get("set_default_billing") == None:
                    #    form.cleaned_data["set_default_billing"] = form2.cleaned_data.get("set_default_billing")
                    if set_default_billing:
                        bill_address.default = True
                        bill_address.save()
                elif not payment_option:
                    messages.info(self.request, "Please select a valid payment option.")
                else:
                    messages.info(self.request, "Please fill in the required billing address fields.")
        #print(form.cleaned_data)
        #print(form2.cleaned_data)
        payment_option = form.cleaned_data.get("payment_option")
        if payment_option == "S":
            return redirect("core:payment", payment_option="stripe")
        elif payment_option == "P":
            return redirect("core:payment", payment_option="paypal")
        else:
            messages.info(self.request, "From the payment options below.")
            return redirect(reverse("core:check-out-edit", kwargs={"pk": order.pk}))
#class CheckoutEditView(View):

    #def get(self, request, pk, *args, **kwargs):
    #    order = get_object_or_404(Order, id=pk)
    #    form = CheckoutForm(instance=order.billing_address)
    #    context = {
    #        "form": form,
    #        "object": order,
    #    }
    #    return render(self.request, "checkout-page.html", context)
        
    #def post(self, request, pk, *args, **kwargs):
    #    order = get_object_or_404(Order, id=pk)
    #    form = CheckoutForm(self.request.POST or None, instance=order.billing_address)
     
    #    if form.is_valid():
    #        street_address = form.cleaned_data.get("street_address")
    #        apartment_address = form.cleaned_data.get("apartment_address")
    #        country = form.cleaned_data.get("country")
    #        zip = form.cleaned_data.get("zip")
    #        payment_option = form.cleaned_data.get("payment_option")
    #        if is_valid_form([street_address, country, zip, payment_option]):
    #            billing_address = Address.objects.get(id=order.billing_address.id)
    #            billing_address.street_address = street_address
    #            billing_address.apartment_address = apartment_address
    #            billing_address.country = country
    #            billing_address.zip = zip
                #billing_address.update(
                #    user=self.request.user,
                #    street_address=street_address,
                #    apartment_address=apartment_address,
                #    country=country,
                #    zip=zip
                #)
    #            billing_address.save()
    #            order.billing_address = billing_address
    #            order.save()
                # TODO: add or redirect to selected payment option
    #    if form.cleaned_data.get("payment_option") == "S":
    #        return redirect("core:payment", payment_option="stripe")
    #    elif form.cleaned_data.get("payment_option") == "P":
    #        return redirect("core:payment", payment_option="paypal")
    #    else:
    #        messages.error(self.request, "Please select a valid payment option.")
    #        return redirect(reverse("core:check-out-edit", kwargs={"pk": order.pk}))

class CheckoutView(View):

    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                "form": form,
                "object": order,
            }
            shipping_address_qs = Address.objects.filter(
                user = self.request.user,
                address_type="S",
                default=True
            )
            if shipping_address_qs.exists():
                context.update({
                    "default_shipping_address": shipping_address_qs[0]
                })
            
            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type="B",
                default=True
            )
            if billing_address_qs.exists():
                context.update({
                    "default_billing_address": billing_address_qs[0]
                })
            return render(self.request, "checkout-page.html", context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order.")
            return redirect("core:item-list")
       
    
    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get("use_default_shipping")
                if use_default_shipping:
                    address_qs = Address.objects.filter(user=self.request.user,
                    address_type="S",
                    default=True)
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, "No default shipping address available")
                        return redirect("core:check-out")
                else:
                    print("User is entering a new shipping address")
                    shipping_address = form.cleaned_data.get("shipping_address")
                    shipping_address2 = form.cleaned_data.get("shipping_address2")
                    shipping_country = form.cleaned_data.get("shipping_country")
                    shipping_zip = form.cleaned_data.get("shipping_zip")
                    # TODO: add funtionality to fields
                    #same_shipping_address = form.cleaned_data.get("same_shipping_address")
                    #save_info = form.cleaned_data.get("save_info")
                    payment_option = form.cleaned_data.get("payment_option")
                    if is_valid_form([shipping_address, shipping_country, shipping_zip, payment_option]):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type="S",
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get("set_default_shipping")
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required shipping address fields.")
                use_default_billing = form.cleaned_data.get("use_default_billing")
                same_billing_address = form.cleaned_data.get("same_billing_address")
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = "B"
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()

                elif use_default_billing:
                    print("Using default billing address")
                    address_qs = Address.objects.filter(user=self.request.user,
                    address_type="B",
                    default=True)
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()
                    else:
                        messages.info(self.request, "No default billing address available")
                        return redirect("core:check-out")
                else:
                    print("User is entering a new billing address")
                    billing_address = form.cleaned_data.get("billing_address")
                    billing_address2 = form.cleaned_data.get("billing_address2")
                    billing_country = form.cleaned_data.get("billing_country")
                    billing_zip = form.cleaned_data.get("billing_zip")
                    #same_shipping_address = form.cleaned_data.get("same_shipping_address")
                    #save_info = form.cleaned_data.get("save_info")
                    payment_option = form.cleaned_data.get("payment_option")
                    if is_valid_form([billing_address, billing_country, billing_zip, payment_option]):
                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type="B",
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get("set_default_billing")
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(self.request, "Please fill in the required billing address fields.")
            payment_option = form.cleaned_data.get("payment_option")
            if payment_option == "S":
                return redirect("core:payment", payment_option="stripe")
            elif payment_option == "P":
                return redirect("core:payment", payment_option="paypal")
            else:
                messages.info(self.request, "Please select a valid payment option.")
                return redirect("core:check-out")
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order.")
            return redirect("core:order-summary")

class PaymentView(View):

    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            stripeKey = settings.STRIPE_PUBLISHABLE_KEY
            
            context = {
                "stripeKey": stripeKey,
                "object": order,
            }
            return render(self.request, "payment.html", context)
        except ObjectDoesNotExist:
            messages.error(self.request, "You do not have an active order.")
            return redirect("core:item-list")



def create_payment(request):
    # Create a PaymentIntent with the amount, currency, and a payment method type.
    #
    # See the documentation [0] for the full list of supported parameters.
    #
    # [0] https://stripe.com/docs/api/payment_intents/create
    order = Order.objects.get(user=request.user, ordered=False)
    try:
        orderAmount = int(order.get_total_price() * 100)
        intent: PaymentIntent

        intent: PaymentIntent = stripe.PaymentIntent.create(
            amount=orderAmount,
            currency='usd',
            automatic_payment_methods={
                'enabled': True,
            }
        )
        # Send PaymentIntent details to the front end.
        return JsonResponse({'clientSecret': intent.client_secret})
    except stripe.error.StripeError as e:
        return JsonResponse({'error': {'message': str(e)}})
    except Exception as e:
        return JsonResponse({'error': {'message': str(e)}})   

#@csrf_exempt
#@require_POST
#def webhook_received(request):
#    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
#    request_data = json.loads(request.body)
#    print(request_data)
#    if webhook_secret:
#        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
#        #signature = request.headers.get("stripe-signature")
#        try:
#            event = stripe.Webhook.construct_event(
#                payload=request_data, sig_header=sig_header, secret=webhook_secret
#            )
#            data = event["data"]
#        except stripe.error.SignatureVerificationError as e:
#            # CORRECT HANDLING: e is an exception object, not a dict
#            print(f"⚠️  Webhook signature verification failed. {e}")
#            return HttpResponse(status=400)
#        except Exception as e:
#            return e
#        event_type = event["type"]
#    else:
#        data = request_data["data"]
#        event_type = request_data["type"]
#    data_object = data["object"]
#    if event_type == "payment_intent.succeeded":
#        print("💰 Payment received.")
#    elif event_type == "payment_intent.failed":
#        print("❌ Payment failed.")

def success(request):
    context = {"stripeKey": settings.STRIPE_PUBLISHABLE_KEY}
    order = Order.objects.get(user=request.user, ordered=False)
    payment_intent_id = request.GET.get("payment_intent")
    payment = Payment()
    payment.stripe_payment_id = payment_intent_id
    payment.user = request.user
    payment.amount = order.get_total_price()
    payment.save()
    ordered = order.ordered == False
    if ordered:
        order.ordered = True
        order.payment = payment
        order.save()
        for order_item in order.items.all():
            order_item.ordered = True
            order_item.save()
    messages.success(request, "Order has been placed.")
    return render(request, "return.html", context)

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item,
                                                 user=request.user,
                                                 ordered=False)
    order_qs = Order.objects.filter(user=request.user, 
                                    ordered=False)
    
    if order_qs.exists():
        order = order_qs[0]
        # Check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, "This item quantity increased by one.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "This item was added to the cart.")
            return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, 
                                     ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")

@login_required    
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, 
                                    ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item,
                                                 user=request.user,
                                                 ordered=False)[0]
            
            order.items.remove(order_item)
            order_item.delete()
            orders = order.items
            if not orders.exists():
                order_qs.delete() 
            #print(f"{order_item} deleted of {order} in {Order.objects.filter(user=request.user)}")
            #order_item.delete()

            #orders = OrderItem.objects.filter(user=request.user, ordered=False)
            #if (len(orders) == 0):
            #    Order.objects.filter(user=request.user, ordered=False).delete()
                
            
            messages.info(request, "This item was removed from the cart.")
            return redirect("core:order-summary")
        else:
            # add a message saying that the order doesn't contain the item
            messages.info(request, "This item is not in the cart.")
            return redirect("core:product-detail", slug=slug)
            
    else:
        # add a message saying the user doesn't have an order
        messages.info(request, "There are no items in the cart.")
        return redirect("core:product-detail", slug=slug)

@login_required    
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, 
                                    ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(item=item,
                                                 user=request.user,
                                                 ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
                order_item.delete()
                orders = order.items
                if not orders.exists():
                    order_qs.delete() 
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            # add a message saying that the order doesn't contain the item
            messages.info(request, "This item is not in the cart.")
            return redirect("core:product-detail", slug=slug)
            
    else:
        # add a message saying the user doesn't have an order
        messages.info(request, "There are no items in the cart.")
        return redirect("core:product-detail", slug=slug)
