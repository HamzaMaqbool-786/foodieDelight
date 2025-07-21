from django.shortcuts import render, get_object_or_404, reverse
from myapp.models import Contact, Dish, Team, Category, Profile, Order
from django.http import HttpResponse,JsonResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.conf import settings
from django.urls import reverse
from .models import Dish, Order, Profile
import hashlib
from django.contrib.auth.decorators import login_required
from .models import Cart, CartItem, Dish
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from datetime import datetime, timedelta
import hashlib,hmac
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.utils import timezone



def index(request):
    context ={}
    cats = Category.objects.all().order_by('name')
    context['categories'] = cats
    # print()
    dishes = []
    for cat in cats:
        dishes.append({
            'cat_id':cat.id,
            'cat_name':cat.name,
            'cat_img':cat.image,
            'items':list(cat.dish_set.all().values())
        })
    context['menu'] = dishes
    return render(request,'index.html', context)

def contact_us(request):
    context={}
    if request.method=="POST":
        name = request.POST.get("name")
        em = request.POST.get("email")
        sub = request.POST.get("subject")
        msz = request.POST.get("message")
        
        obj = Contact(name=name, email=em, subject=sub, message=msz)
        obj.save()
        context['message']=f"Dear {name}, Thanks for your time!"

    return render(request,'contact.html', context)

def about(request):
    context ={}
    cats = Category.objects.all().order_by('name')
    context['categories'] = cats
    # print()
    dishes = []
    for cat in cats:
        dishes.append({
            'cat_id':cat.id,
            'cat_name':cat.name,
            'cat_img':cat.image,
            'items':list(cat.dish_set.all().values())
        })
    context['menu'] = dishes
    return render(request,'about.html', context)

def team_members(request):
    context={}
    members = Team.objects.all().order_by('name')
    context['team_members'] = members
    return render(request,'team.html', context)

def all_dishes(request):
    context={}
    dishes = Dish.objects.all()
    if "q" in request.GET:
        id = request.GET.get("q")
        dishes = Dish.objects.filter(category__id=id)
        context['dish_category'] = Category.objects.get(id=id).name 

    context['dishes'] = dishes
    return render(request,'all_dishes.html', context)

def dish_detail(request, dish_id):
    """
    Display the details of a single dish.
    """
    dish = get_object_or_404(Dish, id=dish_id)
    context = {
        'dish': dish,
    }
    return render(request, 'dish_detail.html', context)


def register(request):
    context = {}
    if request.method == "POST":
        # Fetch data from the HTML form
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('pass')
        contact = request.POST.get('number')
        address = request.POST.get('Address')  # Fetch address field

        # Check if the user already exists
        check = User.objects.filter(username=email)
        if len(check) == 0:
            # Save data to both tables
            usr = User.objects.create_user(email, email, password)
            usr.first_name = name
            usr.save()

            # Save profile details
            profile = Profile(user=usr, contact_number=contact, address=address)
            profile.save()

            context['status'] = f"User {name} Registered Successfully!"
        else:
            context['error'] = f"A User with this email already exists"

    return render(request, 'register.html', context)

def check_user_exists(request):
    email = request.GET.get('usern')
    check = User.objects.filter(username=email)
    if len(check)==0:
        return JsonResponse({'status':0,'message':'Not Exist'})
    else:
        return JsonResponse({'status':1,'message':'A user with this email already exists!'})

def signin(request):
    context={}
    if request.method=="POST":
        email = request.POST.get('email')
        passw = request.POST.get('password')

        check_user = authenticate(username=email, password=passw)
        if check_user:
            login(request, check_user)
            if check_user.is_superuser or check_user.is_staff:
                return HttpResponseRedirect('/admin')
            return HttpResponseRedirect('/dashboard')
        else:
            context.update({'message':'Invalid Login Details!','class':'alert-danger'})

    return render(request,'login.html', context)

@login_required
def dashboard(request):
    context = {}

    try:
        profile = Profile.objects.get(user=request.user)
    except Profile.DoesNotExist:
        messages.error(request, "No profile found. Please register your profile.")
        return redirect('register')  # or a profile creation page

    context['profile'] = profile

    # Fetch the user's cart and related items
    user_cart = Cart.objects.filter(user=request.user).first()  # Get the user's cart
    cart_items = CartItem.objects.filter(cart=user_cart) if user_cart else []
    context['cart_items'] = cart_items  # Pass the cart items to the context

    # Update Profile
    if "update_profile" in request.POST:
        name = request.POST.get('name')
        contact = request.POST.get('contact_number')
        address = request.POST.get('address')

        # Update user's first name and profile details
        profile.user.first_name = name
        profile.user.save()
        profile.contact_number = contact
        profile.address = address

        # Update profile picture if provided
        if "profile_pic" in request.FILES:
            profile_pic = request.FILES['profile_pic']
            profile.profile_pic = profile_pic
        profile.save()

        # Add a success message
        messages.success(request, 'Profile updated successfully!')
    
    # Change Password
    if "change_pass" in request.POST:
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')

        # Check if the current password is correct
        if request.user.check_password(current_password):
            request.user.set_password(new_password)
            request.user.save()
            login(request, request.user)  # Re-authenticate the user after password change
            messages.success(request, 'Password updated successfully!')
        else:
            messages.error(request, 'Current password is incorrect!')

    # Fetch orders for the logged-in user
    orders = Order.objects.filter(customer__user=request.user, status=True).order_by('-id')  # or any other field like date
    context['orders'] = orders


    # Render the dashboard template with the context
    return render(request, 'dashboard.html', context)

def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/')

from django.conf import settings

def single_dish(request, id):
    context = {}
    dish = get_object_or_404(Dish, id=id)

    if request.user.is_authenticated:
        try:
            cust = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            messages.error(request, "No profile found for this user. Please complete your profile.")
            return redirect('dashboard')  # or redirect to a safer page

        # Proceed to create an order
        order = Order(customer=cust, item=dish)
        order.save()
           # ✅ Fix: define `inv` here
        inv = f'INV0000-{order.id}'
        order.invoice_id = inv
        order.save()


      

        # JazzCash configuration
        merchant_id = settings.PAYMENT_GATEWAYS['JAZZCASH']['MERCHANT_ID']
        password = settings.PAYMENT_GATEWAYS['JAZZCASH']['PASSWORD']
        integrity_salt = settings.PAYMENT_GATEWAYS['JAZZCASH']['INTEGRITY_SALT']
        endpoint = settings.PAYMENT_GATEWAYS['JAZZCASH']['ENDPOINT']

        # JazzCash Payment Details
        txn_ref_no = f'TXN{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
        amount = str(int(dish.discounted_price * 100))  # Convert to paisa
        date_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        post_data = {
            'pp_Version': '2.0',
            'pp_TxnType': 'MWALLET',
            'pp_Language': 'EN',
            'pp_MerchantID': merchant_id,
            'pp_SubMerchantID': '',
            'pp_Password': password,
            'pp_BankID': '',
            'pp_ProductID': '',
            'pp_TxnRefNo': txn_ref_no,
            'pp_Amount': amount,
            'pp_TxnCurrency': 'PKR',
            'pp_TxnDateTime': date_time,
            'pp_BillReference': inv,
            'pp_Description': f'Payment for {dish.name}',
            'pp_TxnExpiryDateTime': (datetime.datetime.now() + datetime.timedelta(hours=1)).strftime('%Y%m%d%H%M%S'),
            'pp_ReturnURL': 'F:\Sem 3\Python\Areeeeeeeej\foodZone\template\payment_successfull.html',  # Update with actual success URL
            'pp_SecureHash': '',
        }

        # Generate Secure Hash
        hash_string = '&'.join([integrity_salt] + [str(post_data[key]) for key in sorted(post_data) if key != 'pp_SecureHash'])
        secure_hash = hashlib.sha256(hash_string.encode('utf-8')).hexdigest().upper()
        post_data['pp_SecureHash'] = secure_hash

        # Add POST data to context for frontend rendering
        context.update({
            'dish': dish,
            'post_data': post_data,
            'jazzcash_endpoint': endpoint,
        })

    return render(request, 'dish.html', context)

@login_required
def add_to_cart(request, dish_id):
    """
    Add a dish to the cart and display a success message.
    """
    # Get the dish by ID, raise 404 if not found
    dish = get_object_or_404(Dish, id=dish_id)

    # Get or create the cart for the logged-in user
    user_cart, created = Cart.objects.get_or_create(user=request.user)

    # Check if the dish is already in the user's cart
    cart_item, created = CartItem.objects.get_or_create(cart=user_cart, dish=dish)
    if not created:
        # If the dish is already in the cart, increment the quantity
        cart_item.quantity += 1
        cart_item.save()  # Save the updated quantity

    # Add a success message for the user
    messages.success(request, f"{dish.name} has been added to your cart.")

    # Redirect to the dish detail page or another page (ensure correct URL pattern is used)
    return redirect('dish_detail', dish_id=dish.id)  # Replace 'dish_detail' with your correct view name if different

@login_required
def view_cart(request):
    """
    Display the cart for the logged-in user.
    """
    user_cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = CartItem.objects.filter(cart=user_cart)
    
    quantities = list(range(1, 11))
    
    for item in cart_items:
        item.selected_quantity = item.quantity  

    # Calculate the total price
    total_price = sum(item.dish.discounted_price * item.quantity for item in cart_items)

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'quantities': quantities, 
    }
    return render(request, 'cart.html', context)


def update_quantity(request, item_id):
    """Update the quantity of an item in the cart."""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        cart_item = CartItem.objects.get(id=item_id)
        cart_item.quantity = quantity
        cart_item.save()
    return redirect('view_cart')  # Redirect back to the cart page

def remove_item(request, item_id):
    # Ensure the CartItem belongs to the user's cart
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()

    # Check if the cart is now empty
    if not CartItem.objects.filter(cart__user=request.user).exists():
        return redirect('all_dishes')  # Redirect to menu if cart is empty

    return redirect('all_dishes')  # Otherwise, redirect to cart



@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from your cart.")
    return redirect('view_cart')

@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == "POST":
        new_quantity = int(request.POST.get('quantity', 1))
        cart_item.quantity = new_quantity
        cart_item.total_price = new_quantity * cart_item.dish.discounted_price
        cart_item.save()
        messages.success(request, f"Quantity updated for {cart_item.dish.name}.")
    return redirect('view_cart')

@login_required
def clear_cart(request):
    # Clear the user's cart
    user_cart, created = Cart.objects.get_or_create(user=request.user)
    CartItem.objects.filter(cart=user_cart).delete()
    
    # Redirect back to the cart view with a success message
    messages.success(request, "Your cart has been cleared.")
    return redirect('view_cart')

@login_required
def checkout(request):
    """
    Proceed to checkout using JazzCash payment gateway.
    """
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return redirect('view_cart')

    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.total_price() for item in cart_items)

    # Prepare data for JazzCash payment
    # Example data setup (adapt based on your requirements)
    jazzcash_payment_data = {
        'amount': total_price,
        'description': "Order Checkout",
        'return_url': 'http://127.0.0.1:8000/success',  # Replace with your success view
        # Add other required fields
    }

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'jazzcash_payment_data': jazzcash_payment_data,
    }
    return render(request, 'checkout.html', context)



@csrf_exempt  # Disable CSRF for this view if the payment gateway sends POST data
def payment_success(request):
    if request.method == 'POST':
        # Optionally process the POST data from JazzCash
        post_data = request.POST
        print("POST data from JazzCash:", post_data)
        return render(request, 'success.html', {'post_data': post_data})
    else:
        return render(request, 'success.html')

def payment_cancel(request):
    ## remove comment to delete cancelled order
    # order_id = request.session.get('order_id')
    # Order.objects.get(id=order_id).delete()

    return render(request, 'payment_failed.html') 

JAZZCASH_MERCHANT_ID = "MC147650"
JAZZCASH_PASSWORD = "d0v7138yu6"
JAZZCASH_RETURN_URL = "http://127.0.0.1:8000/success/"
JAZZCASH_INTEGRITY_SALT = "a3t9ce6dx3"

import hashlib
from django.shortcuts import render

def generate_secure_hash(params, secret_key):
    sorted_keys = sorted(params.keys())
    hash_string = '&'.join(f"{key}={params[key]}" for key in sorted_keys)
    hash_string += f"&{secret_key}"
    secure_hash = hashlib.sha256(hash_string.encode()).hexdigest()
    return secure_hash

@login_required
def checkout(request):
    """
    Proceed to checkout using JazzCash payment gateway.
    """
    # Fetch the user's cart
    cart = Cart.objects.filter(user=request.user).first()
    if not cart:
        return redirect('view_cart')

    # Fetch cart items and calculate the total price
    cart_items = CartItem.objects.filter(cart=cart)
    total_price = sum(item.dish.discounted_price * item.quantity for item in cart_items)
    
    # Convert the total price to paisa (e.g., 100.00 PKR = 10000 paisa)
    total_price_paisa = int(total_price * 100)

    # Example JazzCash payment data
    jazzcash_payment_data = {
        'pp_Version': '1.0',
        'pp_TxnType': 'MWALLET',
        'pp_Language': 'EN',
        'pp_MerchantID': 'MC147650',  # Replace with actual Merchant ID
        'pp_Password': 'd0v7138yu6',   # Replace with actual password
        'pp_TxnRefNo': 'REF' + str(cart.id) + str(request.user.id),  # Unique transaction reference
        'pp_Amount': str(total_price_paisa),  # Amount in paisa
        'pp_TxnCurrency': 'PKR',
        'pp_TxnDateTime': timezone.now().strftime('%Y%m%d%H%M%S'),  # Current timestamp
        'pp_TxnExpiryDateTime': (timezone.now() + timedelta(hours=1)).strftime('%Y%m%d%H%M%S'),  # Expiry timestamp
        'pp_BillReference': 'BILL' + str(cart.id),
        'pp_Description': 'Payment for order',
        'pp_ReturnURL': 'http://127.0.0.1:8000/success/',  # Replace with actual return URL
    }

    # JazzCash secret key
    secret_key = 'hu92z081xv'  # Replace with your secret key

    # Generate the secure hash
    jazzcash_payment_data['pp_SecureHash'] = generate_secure_hash(jazzcash_payment_data, secret_key)

    return render(request, 'checkout.html', {
        'jazzcash_payment_data': jazzcash_payment_data,
        'total_price': total_price,  # Pass the calculated total price
        'cart_items': cart_items,  # Optional: Pass items for the order summary
    })



def process_payment(request):
    # Assuming the cart for the logged-in user
    cart_items = CartItem.objects.filter(cart__user=request.user)
    
    # Calculate the total price of items in the cart
    total_price = sum(item.total_price() for item in cart_items)

    # Prepare data for payment
    current_datetime = datetime.datetime.now()
    pp_TxnDateTime = current_datetime.strftime('%Y%m%d%H%M%S')

    expiry_datetime = current_datetime + timedelta(hours=1)
    pp_TxnExpiryDateTime = expiry_datetime.strftime('%Y%m%d%H%M%S')

    pp_TxnRefNo = "T" + pp_TxnDateTime
    post_data = {
        "pp_Version": "1.0",
        "pp_TxnType": "SALE",  # Assuming sale transaction type
        "pp_Language": "EN",
        "pp_MerchantID": JAZZCASH_MERCHANT_ID,
        "pp_Password": JAZZCASH_PASSWORD,
        "pp_BankID": "TBANK",
        "pp_ProductID": "RETL",  # Retail product ID
        "pp_TxnRefNo": pp_TxnRefNo,
        "pp_Amount": total_price,  # Total price from cart
        "pp_TxnCurrency": "PKR",
        "pp_TxnDateTime": pp_TxnDateTime,
        "pp_BillReference": "billRef",
        "pp_Description": "Payment for FoodieDelight order",
        "pp_TxnExpiryDateTime": pp_TxnExpiryDateTime,
        "pp_ReturnURL": JAZZCASH_RETURN_URL,
        "pp_SecureHash": "",
    }

    # Generate secure hash for the request
    sorted_string = "&".join(f"{key}={value}" for key, value in sorted(post_data.items()) if value != "")
    pp_SecureHash = hmac.new(
        JAZZCASH_INTEGRITY_SALT.encode(),
        sorted_string.encode(),
        hashlib.sha256
    ).hexdigest()

    post_data['pp_SecureHash'] = pp_SecureHash

    # Pass the context to the template
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
        'post_data': post_data  # Pass the payment data to the template
    }

    # Render process_payment page with payment data
    return render(request, '', context)

@csrf_exempt
def success(request):
    # Assuming you have a success page for JazzCash payment gateway
    return render(request, 'success.html')