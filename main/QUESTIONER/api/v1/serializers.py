from rest_framework import serializers
from QUESTIONER.models import Questioner
class QuestionerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Questioner
        fields = '__all__'
