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


class RegisterAPIView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

            # Generate OTP secret
            otp_secret = pyotp.random_base32()
            UserOTP.objects.create(user=user, otp_secret=otp_secret)

            # Generate OTP code (in production, send via SMS/email)
            totp = pyotp.TOTP(otp_secret)
            otp_code = totp.now()

            return Response({
                'message': 'User registered successfully. Please verify OTP',
                'email': user.email,
                'otp_code': otp_code  # Remove this in production - only for testing
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPAPIView(APIView):
    def post(self, request):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            otp_code = serializer.validated_data['otp']
            try:
                user_otp = UserOTP.objects.get(user=request.user)
                totp = pyotp.TOTP(user_otp.otp_secret)

                if totp.verify(otp_code):
                    request.user.is_verified = True
                    request.user.save()
                    user_otp.otp_verified = True
                    user_otp.save()

                    # Generate JWT tokens
                    refresh = RefreshToken.for_user(request.user)
                    return Response({
                        'message': 'OTP verified successfully',
                        'access': str(refresh.access_token),
                        'refresh': str(refresh)
                    }, status=status.HTTP_200_OK)
                return Response(
                    {'error': 'Invalid OTP'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except UserOTP.DoesNotExist:
                return Response(
                    {'error': 'OTP not configured for this user'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data

            # Generate OTP
            user_otp = UserOTP.objects.get(user=user)
            totp = pyotp.TOTP(user_otp.otp_secret)
            otp_code = totp.now()

            # In production: Send OTP via SMS/email here
            return Response({
                'message': 'OTP sent for verification',
                'otp_code': otp_code  # Remove this in production - only for testing
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