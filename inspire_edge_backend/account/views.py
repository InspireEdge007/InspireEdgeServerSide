from httpx import delete
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import pyotp  # Changed from django_otp to pyotp
import base64
from .models import User, Role, UserRole, UserOTP
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer,
    OTPSerializer, RoleSerializer, UserRoleSerializer, UserSerializer
)
from .permissions import IsAdmin, HasRolePermission
from datetime import timedelta
from django.utils import timezone


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate OTP secret
            otp_secret = pyotp.random_base32()
            UserOTP.objects.create(user=user, otp_secret=otp_secret)

            # Generate OTP code (in production, send via SMS/email)
            totp = pyotp.TOTP(otp_secret, interval=300)
            otp_code = totp.now()

            # send_mail(
            #     subject="Your new OTP code",
            #     message=f"Your new OTP is: {otp_code}",
            #     from_email="noreply@yourdomain.com",
            #     recipient_list=[user.email],
            #     fail_silently=False,
            # )

            return Response({
                'message': 'User registered successfully. Please verify OTP',
                'email': user.email,
                'otp_code': otp_code  # Remove this in production - only for testing
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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