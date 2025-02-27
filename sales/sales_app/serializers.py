from rest_framework import serializers
from .models import UserTG


class UserTGSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserTG
        fields = '__all__'