from rest_framework import serializers
from .models import CustomStore, Category, CustomProduct

class CustomStoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomStore
        fields = '__all__'
        read_only_fields = ['user', 'created_at', 'updated_at']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']



class CustomProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomProduct
        fields = '__all__'
        
        
    def create(self, validated_data):
        request = self.context.get('request')
        image = request.FILES.get('image')

        if image:
            validated_data['image'] = image

        return super().create(validated_data)

