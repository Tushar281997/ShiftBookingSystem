import random
from django.db import models, transaction
from django_extensions.db.fields import CreationDateTimeField
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager



class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        """
        Creates and saves a User with the given email,and password.
        """
        if not email:
            raise ValueError('The given email must be set')
        try:
            with transaction.atomic():
                user = self.model(email=email, **extra_fields)
                user.set_password(password)
                user.save(using=self._db)
                return user
        except:
            raise

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(email, password=password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    """
    email = models.EmailField(max_length=40, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    mobile_number = models.IntegerField(unique=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        return self


def generate_otp():
    otp = "".join([random.choice('123456789') for i in range(6)])
    return otp

class UserOTP(models.Model):
    mobile_number=models.CharField(max_length=15, editable = False, unique = False, null=True)
    key = models.CharField(max_length=6, editable=False, default=generate_otp, unique=False)
    created_date = CreationDateTimeField(null=True)

    def __unicode__(self):
	    return '%s' % (self.key)



def generate_shift_id():
	shift_id =  "".join([random.choice('ABCDEFGHIJKLMNPQRSTUVXYZ123456789') for i in range(10)])
	return shift_id


class ShiftData(models.Model):
    status_choices = (
        ('BOOKED', 'BOOKED'),
        ('CANCELLED', 'CANCELLED'),
    )
    shift_id =  models.CharField(max_length = 10,unique = True, default = generate_shift_id)
    added_by = models.ForeignKey(User, null=True, related_name='admin_user', on_delete=models.CASCADE)
    owned_by = models.ForeignKey(User, null=True, related_name='owned_user', on_delete=models.CASCADE)
    area = models.CharField(max_length = 10,default = generate_shift_id)
    booked = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True)
    end_time = models.DateTimeField(null=True)
    created_date = CreationDateTimeField(null=True)
    modified_date = CreationDateTimeField(null=True)
    status = models.CharField(max_length=20, null=True, choices=status_choices)


