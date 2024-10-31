from rest_framework import serializers
from users.models import CustomUser
from django.core.validators import EmailValidator
from.utils import generate_confirmation_code
from django.core.mail import send_mail


class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator])

    class Meta:
        model = CustomUser
        fields = ('email', 'username')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        confirmation_code = generate_confirmation_code()
        user.confirmation_code = confirmation_code
        user.save()
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {confirmation_code}',
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=16)

    def validate(self, attrs):
        username = attrs['username']
        confirmation_code = attrs['confirmation_code']
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError('Неправильный код подтверждения')
        return attrs