from django import forms
from .models import Address
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
PAYMENT_CHOICES = (
    ("S", "Stripe"),
    ("P", "PayPal"),
)

class CheckoutForm(forms.ModelForm):

    class Meta:
        model = Address
        fields = ["shipping_address", "shipping_address2", "billing_address", "billing_address2", "shipping_country", "billing_country", "shipping_zip", "billing_zip", "payment_option"]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["shipping_address"].initial = self.instance.street_address
            self.fields["billing_address"].initial = self.instance.street_address
            self.fields["shipping_address2"].initial = self.instance.apartment_address
            self.fields["billing_address2"].initial = self.instance.apartment_address
            self.fields["shipping_country"].initial = self.instance.country
            self.fields["billing_country"].initial = self.instance.country
            self.fields["shipping_zip"].initial = self.instance.zip
            self.fields["billing_zip"].initial = self.instance.zip
            self.fields["shipping_address"].required = False
            self.fields["shipping_address2"].required = False
            self.fields["shipping_country"].required = False
            self.fields["shipping_zip"].required = False
            self.fields["billing_address"].required = False
            self.fields["billing_address2"].required = False
            self.fields["billing_country"].required = False
            self.fields["billing_zip"].required = False
            self.fields["payment_option"].required = False
        
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.street_address = self.cleaned_data.get("shipping_address")
        instance.street_address = self.cleaned_data.get("billing_address")
        instance.apartment_address = self.cleaned_data.get("shipping_address2")
        instance.apartment_address = self.cleaned_data.get("billing_address2")
        instance.country = self.cleaned_data.get("shipping_country")
        instance.country = self.cleaned_data.get("billing_country")
        instance.zip = self.cleaned_data.get("shipping_zip")
        instance.zip = self.cleaned_data.get("billing_zip")
    
        if commit:
            instance.save()
        
        return instance
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label="(select country)").formfield(required=False,
        widget=CountrySelectWidget(attrs={
        "class": "custom-select d-block w-100"
    }))
    shipping_zip = forms.CharField(required=False)
    billing_address = forms.CharField(required=False)
    billing_address2 = forms.CharField(required=False)
    billing_country = CountryField(blank_label="(select country)").formfield(required=False,
        widget=CountrySelectWidget(attrs={
        "class": "custom-select d-block w-100"
    }))
    billing_zip = forms.CharField(required=False)
    same_billing_address = forms.BooleanField(required=False)
    set_default_shipping = forms.BooleanField(required=False)
    use_default_shipping = forms.BooleanField(required=False)
    set_default_billing = forms.BooleanField(required=False)
    use_default_billing = forms.BooleanField(required=False)
    payment_option = forms.ChoiceField(widget=forms.RadioSelect(), choices=PAYMENT_CHOICES)
