from django.contrib import admin
from .models import User, UserOTP, ShiftData

# Register your models here.
admin.site.register(User)
admin.site.register(UserOTP)
admin.site.register(ShiftData)

