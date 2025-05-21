from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import pyotp

import base64
from .models import User, Role, UserRole, UserOTP
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    OTPSerializer, RoleSerializer, UserRoleSerializer, UserSerializer, 
    BusinessProfileSerializer
)
from .permissions import IsAdmin, HasRolePermission
from datetime import timedelta
from django.utils import timezone
import traceback

from customauth.tasks import downgrade_user_task

# password auth
from rest_framework import status
from django.core.mail import send_mail
import pyotp
from .models import User, UserOTP

# Google auth
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from .serializers import GoogleLoginSerializer

# business
from rest_framework import generics, permissions
from .models import BusinessProfile
from .serializers import BusinessProfileSerializer
from django.utils import timezone
from datetime import timedelta
    

class RegisterAPIView(APIView):
    def post(self, request):
        try:
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():

                user = serializer.save()

                user.start_trial()

                # Schedule downgrade in 14 days
                downgrade_user_task.apply_async(args=[user.id], eta=user.trial_end)

                # Generate OTP secret
                otp_secret = pyotp.random_base32()
                UserOTP.objects.create(user=user, otp_secret=otp_secret)

                # Generate OTP code (in production, send via SMS/email)
                totp = pyotp.TOTP(otp_secret, interval=300)
                otp_code = totp.now()

                return Response({
                    'message': 'User registered successfully. Please verify OTP',
                    'email': user.email,
                    'otp_code': otp_code  # Remove this in production - only for testing
                }, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
                print("🔥 EXCEPTION:", traceback.format_exc())  # Logs to Render's log panel
                return Response({"detail": "Something went wrong. Please try again later."}, status=500)

class ResendOTPAPIView(APIView):

    def post(self, request):
        email = request.data.get('email')

        if not email:
            return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)

            # Get or create UserOTP record
            user_otp, created = UserOTP.objects.get_or_create(user=user)

            if not user_otp.otp_secret:
                user_otp.otp_secret = pyotp.random_base32()


            # Update the OTP timestamp
            user_otp.created = timezone.now()
            user_otp.save()

            # Generate new OTP
            new_otp = user_otp.generate_otp()

            # Here, you’d send the OTP via email/SMS
            return Response({
                'message': 'OTP resent successfully.',
                'otp_code': new_otp  # Remove in production
            }, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class VerifyOTPAPIView(APIView):
    def post(self, request):
        serializer = OTPSerializer(data=request.data)

        if serializer.is_valid():
            otp_code = serializer.validated_data['otp']
            email = serializer.validated_data.get('email')

            if not email:
                return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(email=email)
                user_otp = UserOTP.objects.get(user=user)

                # Check if OTP expired
                if timezone.now() > user_otp.created + timedelta(minutes=5):
                    return Response({'error': 'OTP expired. Please request a new one.'}, status=status.HTTP_400_BAD_REQUEST)

                totp = pyotp.TOTP(user_otp.otp_secret, interval=300)  # 5-minute validity
                if totp.verify(otp_code):
                    user.is_verified = True
                    user.save()
                    user_otp.otp_verified = True
                    user_otp.save()
                    user_otp.delete()

                    refresh = RefreshToken.for_user(user)
                    return Response({
                        'message': 'OTP verified successfully',
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    })

                return Response({'error': 'Invalid OTP'}, status=status.HTTP_400_BAD_REQUEST)

            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
            except UserOTP.DoesNotExist:
                return Response({'error': 'OTP not configured for this user'}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                print("Something went wrong:", str(e))

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            print(serializer.validated_data)

            email = serializer.validated_data['email']
            password = serializer.validated_data['password']


            user = authenticate(email=email, password=password)
            if user is None:
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            if not user.is_verified:
                return Response({'error': 'Account not verified'}, status=status.HTTP_403_FORBIDDEN)

            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Login successful',
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RoleListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        roles = Role.objects.all()
        serializer = RoleSerializer(roles, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AssignRoleAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        user_id = request.data.get('user_id')
        role_id = request.data.get('role_id')

        try:
            user = User.objects.get(pk=user_id)
            role = Role.objects.get(pk=role_id)

            UserRole.objects.get_or_create(user=user, role=role)
            return Response(
                {'message': 'Role assigned successfully'},
                status=status.HTTP_201_CREATED
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Role.DoesNotExist:
            return Response(
                {'error': 'Role not found'},
                status=status.HTTP_404_NOT_FOUND
            )

class AdminDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated, HasRolePermission('admin')]

    def get(self, request):
        return Response({
            'message': 'Welcome to Admin Dashboard',
            'user': UserSerializer(request.user).data
        })

class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

class SubscriptionPaymentAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        tier = request.data.get('tier')
        months = int(request.data.get('months', 1))

        # Validate tier
        valid_tiers = ['pro', 'enterprise']
        if tier not in valid_tiers:
            return Response({'error': 'Invalid tier.'}, status=status.HTTP_400_BAD_REQUEST)

        # TODO: Verify payment here (e.g. call Paystack/Flutterwave API)

        # Activate subscription
        user.activate_paid_subscription(months=months, tier=tier)

        # Schedule downgrade
        
        downgrade_user_task.apply_async(args=[user.id], eta=user.subscription_end)

        return Response({
            'message': f'{tier.capitalize()} plan activated for {months} month(s).',
            'subscription_end': user.subscription_end,
        }, status=status.HTTP_200_OK)

class ForgotPasswordAPIView(APIView):
    def post(self, request):
        try:
            email = request.data.get('email')
            if not email:
                return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

            user = User.objects.filter(email=email).first()
            if not user:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            # Always generate and save a new OTP secret
            otp_secret = pyotp.random_base32()

             # Generate OTP
            totp = pyotp.TOTP(otp_secret, interval=5000)
            otp_code = totp.now()
            user_otp, _ = UserOTP.objects.get_or_create(user=user)
            user_otp.otp_secret = otp_code
            user_otp.save()



            # Send email
            send_mail(
                subject="Inspire Edge Password Reset OTP",
                message=f"""
                        Hello {user.first_name or 'there'},

                        You requested a password reset on Inspire Edge.

                        Your OTP code is: {otp_code}

                        This OTP is valid for 5 minutes.

                        If you did not request this, please ignore this email.

                        Thanks,
                        The Inspire Edge Team
                        """,

                from_email="noreply@inspireedge.com",
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({'message': 'OTP has been sent to your email.'}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({'error': 'Something went wrong. Please try again later.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResetPasswordAPIView(APIView):
    def post(self, request):
        try:
            # Get parameters from request body
            email = request.data.get('email')
            otp = request.data.get('otp')
            password = request.data.get('password')

            # Validate inputs
            if not all([email, otp, password]):
                return Response({'error': 'Email, OTP, and new password are required.'}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve user by email
            user = User.objects.filter(email=email).first()
            if not user:
                return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)

            # Retrieve OTP record for the user
            user_otp = UserOTP.objects.filter(user=user).first()
            if not user_otp:
                return Response({'error': 'OTP record not found for this user.'}, status=status.HTTP_404_NOT_FOUND)

            # Verify the OTP using pyotp
            if  user_otp.otp_secret != otp:
                return Response({'error': 'Invalid or expired OTP.'}, status=status.HTTP_400_BAD_REQUEST)

            # Update user password
            user.set_password(password)
            user.save()

            # Optionally, delete the OTP record after successful password reset
            user_otp.delete()

            return Response({'message': 'Password has been reset successfully.'}, status=status.HTTP_200_OK)

        except Exception as e:
            print(e)
            return Response({'error': f'{e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    serializer_class = GoogleLoginSerializer

    def post(self, request, *args, **kwargs):
        try:
            print("Received Google login POST request")
            print("Request data:", request.data)

            response = super().post(request, *args, **kwargs)
            user = self.request.user
            return Response({
                "access": response.data["access"],
                "refresh": response.data["refresh"],
                "user": {
                    "email": user.email,
                    "id": user.id,
                }
            })
        except Exception as e:
            print("Error in GoogleLoginView:", str(e))
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
