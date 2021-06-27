# SHIFT BOOKING
APi Documentation is published at : https://documenter.getpostman.com/view/14536159/Tzef935A


Api1: Create User
Method: Post
you can create user and also specify the created user is a staff member or not using boolean statement
body:
{
'email':'tushar.n@gmail.com'
'first_name':'TusharN'
'last_name':'Nachan'
'password':'7768847156'
'mobile_number':7768847156,
'is_staff': True

}


APi2: Login 
Method: Post
User can generate Otp using this also validate otp
generate_otp body:
{
  "mobile_number": 7768847156,
  "action": "GENERATE OTP",
}
Validate_otp body:
{
  "mobile_number": 7768847156,
  "action": "",
  "otp": "143978"
}


APi3:
Method Post
Create New shifts, this api can be accessed by the staff members only
{
"email":"tushar3.n@gmail.com",
"area":"Chennai",
"start_time":"2021-05-07 13:00:00",
"end_time":"2021-05-07 13:59:00"

}

Api4:
method: POST
Book a shift
body:
{"action":"BOOK",
"shift_id":"PDUCPC9EMY",
"email":"tushar.n@gmail.com"
}

Api5:
Method: GET
Fetch shift details
1.if shift details are to be fetched for particular user you can pass email or shift_id or city in params
2. For all shift details no parameter is required, or if you pass city all the shifts of the particular city will be fetched

