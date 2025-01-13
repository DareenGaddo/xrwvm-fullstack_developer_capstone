from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse,JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, render, redirect
# from .models import related models
from .restapis import get_request, analyze_review_sentiments
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from datetime import datetime
import logging
import json

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.


# Create an `about` view to render a static about page
def about(request):
    context = {}
    if request.method == "GET":
        return render(request, 'djangoapp/about.html', context)


# Create a `contact` view to return a static contact page
def contact(request):
    context = {}
    if request.method == "GET":
        return render(request, "djangoapp/contact.html", context)

# Create a `login_request` view to handle sign in request
def login_request(request):
    # Check if the request is a POST request
    if request.method == "POST":
        # If the content type is JSON, load the data from request.body
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            username = data.get('userName')  # Use .get() to avoid KeyError
            password = data.get('password')
            
            if username and password:
                # Authenticate user
                user = authenticate(username=username, password=password)
                if user is not None:
                    login(request, user)
                    return JsonResponse({"userName": username, "status": "Authenticated"})
                else:
                    return JsonResponse({"error": "Invalid credentials"}, status=400)
            else:
                return JsonResponse({"error": "Username and password are required"}, status=400)
        else:
            return JsonResponse({"error": "Expected JSON format"}, status=400)
    
    return JsonResponse({"error": "Invalid method"}, status=405)

# Create a `logout_request` view to handle sign out request
def logout_request(request):
    # Get the user object based on session id in request
    print("Log out the user `{}`".format(request.user.username))
    # Logout user in the request
    logout(request)
    # Redirect user back to course list view
    return redirect('djangoapp:index')


# Create a `registration_request` view to handle sign up request
def registration_request(request):
    context = {}
    # If it is a GET request, just render the registration page
    if request.method == 'GET':
        return render(request, 'djangoapp/registration.html', context)
    # If it is a POST request
    elif request.method == 'POST':
        # Get user information from request.POST
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST['firstname']
        last_name = request.POST['lastname']
        user_exist = False
        try:
            # Check if user already exists
            User.objects.get(username=username)
            user_exist = True
        except:
            # If not, simply log this is a new user
            logger.debug("{} is new user".format(username))
        # If it is a new user
        if not user_exist:
            # Create user in auth_user table
            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name,
                                            password=password)
            # Login the user and redirect to course list page
            login(request, user)
            return redirect("djangoapp:index")
        else:
            return render(request, 'djangoapp/registration.html', context)

# Update the `get_dealerships` view to render the index page with a list of dealerships
#Update the `get_dealerships` render list of dealerships all by default, particular state if state is passed
def get_dealerships(request, state="All"):
    if(state == "All"):
        endpoint = "/fetchDealers"
    else:
        endpoint = "/fetchDealers/"+state
    dealerships = get_request(endpoint)
    return JsonResponse({"status":200,"dealers":dealerships})

# Create a `get_dealer_details` view to render the reviews of a dealer
def get_dealer_details(request, dealer_id):
    if(dealer_id):
        endpoint = "/fetchDealer/"+str(dealer_id)
        dealership = get_request(endpoint)
        return JsonResponse({"status":200,"dealer":dealership})
    else:
        return JsonResponse({"status":400,"message":"Bad Request"})

def get_dealer_reviews(request, dealer_id):
    # if dealer id has been provided
    if(dealer_id):
        endpoint = "/fetchReviews/dealer/"+str(dealer_id)
        reviews = get_request(endpoint)
        for review_detail in reviews:
            response = analyze_review_sentiments(review_detail['review'])
            print(response)
            review_detail['sentiment'] = response['sentiment']
        return JsonResponse({"status":200,"reviews":reviews})
    else:
        return JsonResponse({"status":400,"message":"Bad Request"})

# Create a `add_review` view to submit a review
@csrf_exempt
def add_review(request):
    if(request.user.is_anonymous == False):
        data = json.loads(request.body)
        try:
            response = post_review(data)
            return JsonResponse({"status":200})
        except:
            return JsonResponse({"status":401,"message":"Error in posting review"})
    else:
        return JsonResponse({"status":403,"message":"Unauthorized"})

