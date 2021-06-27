import traceback
import pytz

from django.shortcuts import render
from django.db import transaction
from django.db.models import Q
from datetime import datetime
from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserSerializer
from .models import ShiftData, UserOTP, User
from twilio.rest import Client
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import jwt_encode_handler, jwt_get_secret_key
from rest_framework_jwt.utils import jwt_payload_handler
import jwt

# Create your views here.
class CreateUserAPIView(APIView):
    # Allow any user (authenticated or not) to access this url
    permission_classes = (AllowAny,)

    def post(self, request):
        user = request.data
        serializer = UserSerializer(data=user)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LoginAPIView(APIView):
    # Allow any user (authenticated or not) to access this url
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            with transaction.atomic():
                data = request.data
                mobile_number = data.get('mobile_number')
                action = data.get('action')
                otp = data.get('otp')
                if action == 'GENERATE OTP':
                    user = User.objects.filter(mobile_number=mobile_number)
                    response = {"message":"User not found"}
                    if not user:
                        return Response(response, status=status.HTTP_404_NOT_FOUND)
                    key = UserOTP.objects.create(mobile_number=mobile_number, created_date=datetime.now())
                    # commenting because twilio credentials keeps changing as i have an trail account
                    # key = key.key
                    # account_sid = "AC241b7c980f8a729a310fc2bea054d704"
                    # auth_token = "4bcc039b87b7c96e06fade36e2c742c4"
                    # client = Client(account_sid, auth_token)
                    # mobile_number = str(mobile_number)
                    # country_code = "+91"
                    # split_number = list(mobile_number)
                    # if split_number[0] != "+":
                    #     mobile_number = country_code + mobile_number
                    #     print ("mm",mobile_number)
                    # client.messages.create(
                    #     body=("You Otp for login is {}".format(key)),
                    #     from_='+15037136236',
                    #     to=mobile_number
                    # )
                    response = {"message": "Check your registered mobile number for otp"}
                else:
                    user = User.objects.get(mobile_number=mobile_number)
                    otp_valid = UserOTP.objects.filter(mobile_number=mobile_number, key=otp).last()
                    if otp_valid and user:
                        try:
                            otp_valid.delete()
                            payload = jwt_payload_handler(user)
                            key = api_settings.JWT_PRIVATE_KEY or jwt_get_secret_key(payload)
                            token = jwt.encode(
                                payload,
                                key,
                                api_settings.JWT_ALGORITHM
                            )
                            user_details = {}
                            user_details['name'] = "%s %s" % (
                                user.first_name, user.last_name)
                            user_details['token'] = token
                            return Response(user_details, status=status.HTTP_200_OK)

                        except Exception as e:
                            raise e
                    else:
                        res = {
                            'error': 'can not authenticate with the given credentials or otp expired'}
                        return Response(res, status=status.HTTP_403_FORBIDDEN)

                return Response(response, status=status.HTTP_201_CREATED)
        except Exception as e:
            print(e)
            response = {"message": "Something went wrong!"}
            return Response(response, status=status.HTTP_502_BAD_GATEWAY)


@api_view(['POST'])
def add_shift_data(request):
    """"
    only staff can add new shifts
    email: email of the staff who is creating shift
    area: city of the shift
    start_time: shift start_time
    end_time: shift end_time
    """
    try:
        fetch_data = request.data
        email = fetch_data.get('email')
        area = fetch_data.get('area')
        start_time = fetch_data.get('start_time')
        end_time = fetch_data.get('end_time')
        staff = User.objects.filter(email=email, is_staff=True).last()
        if not staff:
            res = {
                'error': 'Only staff members can add shifts'}
            return Response(res, status=status.HTTP_403_FORBIDDEN)
        date_format_start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        date_format_end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
        if date_format_end_time <= date_format_start_time:
            response = {
                "message": "End date time should be greater than start date time",
                "response": {
                }}
            return Response(response, status=status.HTTP_403_FORBIDDEN)
        checks_if_occupied = ShiftData.objects.filter(area=area,
                                                 end_time__range=[date_format_start_time, date_format_end_time]
                                                      ).exclude(status='CANCELLED').last()
        if checks_if_occupied:
            response = {
                "message": "Shift Already Present try different date/time",
                "response": {
                    'shift_id': checks_if_occupied.shift_id
                }}
            return Response(response, status=status.HTTP_200_OK)


        created_shift = ShiftData.objects.create(area=area,
                                                 start_time=date_format_start_time,
                                                 end_time=date_format_end_time,
                                                 added_by=staff)
        response = {
                    "message":"Shift added Successfully",
                    "response":{
                        'shift_id': created_shift.shift_id
                    }}
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        print (traceback.format_tb(e))
        response = {
            "message": "Something went wrong!",
            "response": {
            }}
        return Response(response, status=status.HTTP_503_SERVICE_UNAVAILABLE)

@api_view(['POST'])
def book_shift(request):
    """"
    Book or cancel you shifts
    email: user email who is booking
    shift_id: shift_id which you wish to book/cancel
    action: specify the action you need to perform book/cancel
    """
    try:
        fetch_data = request.data
        email = fetch_data.get('email')
        shift_id = fetch_data.get('shift_id')
        action = fetch_data.get('action')
        if not action or (action not in ["BOOK", "CANCEL"]):
            response = {
                "message": "Action Invalid",
                "response": {
                }}
            return Response(response, status=status.HTTP_403_FORBIDDEN)
        shift_obj = ShiftData.objects.filter(shift_id=shift_id).last()
        if not shift_obj:
            response = {
                "message": "Shift doesnt exists",
                "response": {
                }}
            return Response(response, status=status.HTTP_403_FORBIDDEN)
        # Trying Booking shifts
        if action == "BOOK":
            utc = pytz.UTC
            # checking if your time slot if already occupied
            checks_if_occupied = ShiftData.objects.filter(owned_by__email=email,
                                                          end_time__range=[shift_obj.start_time, shift_obj.end_time],
                                                          booked=True
                                                          ).exclude(status='CANCELLED', shift_id=shift_id).last()

            if shift_obj.booked and shift_obj.owned_by.email != email:
                response = {
                    "message": "Shift is already occupied by someone",
                    "response": {
                    }}
            elif shift_obj.booked and shift_obj.owned_by.email == email:
                response = {
                    "message": "Shift is already booked by you",
                    "response": {
                    }}
            elif checks_if_occupied:
                response = {
                    "message": "you have another shift in this time slot",
                    "response": {
                        "shift_id":checks_if_occupied.shift_id,
                        "area":checks_if_occupied.area
                    }}
            elif shift_obj.start_time <= datetime.now().replace(tzinfo=utc) <= shift_obj.end_time:
                response = {
                    "message": "Ongoing shifts cannot be booked",
                    "response": {}
                }
            else:
                # assigning shift
                owned_by = User.objects.filter(email=email).last()
                if not owned_by:
                    response = {
                        "message": "User Doesn't Exists",
                        }
                else:
                    shift_obj.owned_by = owned_by
                    shift_obj.status = "BOOKED"
                    shift_obj.booked = True
                    shift_obj.save()
                    response = {
                        "message": "Shift booked successfully",
                        "response": {
                            "shift_id": shift_obj.shift_id,
                            "area": shift_obj.area
                        }}
        else:
            if shift_obj.owned_by.email != email:
                response = {
                    "message": "Shift dosen't belongs to you",
                    "response": {
                    }}
            else:
                if shift_obj.status == "CANCELLED":
                    response = {
                        "message": "Already cancelled",
                        "response": {
                        }}
                else:
                    shift_obj.status = "CANCELLED"
                    shift_obj.booked = False
                    shift_obj.owned_by = None
                    shift_obj.save()
                    response = {
                        "message": "Cancelled Successfully",
                        "response": {
                        }}
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        print(traceback.format_tb(e))
        response = {
            "message": "Something went wrong!",
            "response": {
            }}
        return Response(response, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(["GET"])
def get_shift_details(request):
    """"
    can fetch user's shift details or all shift details/available shit details
    email: email of user whose shift history needed, optional parameter
    shift_id: shift_id for details of particular shift, , optional parameter
    city: if need shift details for particular city
    Blank parameter can give you all shift details and available shifts
    """
    try:
        fetch_data = request.GET
        email = fetch_data.get('email')#optional parameter
        shift_id = fetch_data.get('shift_id') #optional parameter
        city = fetch_data.get('city') #optional parameter
        if email:
            query = Q(owned_by__email=email)
            if shift_id:
                query &= Q(shift_id=shift_id)
            if city:
                query &= Q(area=city)
            shift_list = ShiftData.objects.filter(query).values("shift_id",
                                                           "area",
                                                           "start_time",
                                                           "end_time",
                                                           "booked").order_by('start_time')

            response = {
                "message": "Find below thw shift/shifts detalis",
                "response": {
                    "shift_list" : shift_list
                }}
        else:
            all_shits_data = ShiftData.objects.all().values("shift_id",
                                                           "area",
                                                           "start_time",
                                                           "end_time",
                                                           "booked").order_by('start_time')
            if city:
                all_shits_data = all_shits_data.filter(area=city)
            available_shits = all_shits_data.filter(start_time__gt=datetime.now(),booked=False)
            response_data = {"all_shifts":all_shits_data, "available_shifts":available_shits}
            response = {
                "message": "Find below thw shift/shifts detalis",
                "response": {
                    "shift_list": response_data
                }}
        return Response(response, status=status.HTTP_200_OK)
    except Exception as e:
        print(traceback.format_tb(e))
        response = {
            "message": "Something went wrong!",
            "response": {
            }}
        return Response(response, status=status.HTTP_503_SERVICE_UNAVAILABLE)






