from django.urls import path, include
from .views import CreateUserAPIView, LoginAPIView, add_shift_data, book_shift, get_shift_details

urlpatterns = [
    path(r'create/', CreateUserAPIView.as_view()),
    path(r'login/', LoginAPIView.as_view()),
    path(r'add/shift/', add_shift_data),
    path(r'book/shift/', book_shift),
    path(r'get/shift/data', get_shift_details),
]