from rest_framework.response import Response
from rest_framework.decorators import api_view
from QUESTIONER.models import Questioner
from QUESTIONER.api.v1.serializers import QuestionerSerializer
@api_view(['GET'])
def questioner_list(request):
    data = Questioner.objects
    serializer = QuestionerSerializer(data,many=True)
    return Response(serializer.data)