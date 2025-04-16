from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Confession, Like, Comment
from .serializers import ConfessionSerializer, LikeSerializer, CommentSerializer

class ConfessionListCreateView(generics.ListCreateAPIView):
    queryset = Confession.objects.all().order_by('-created_at')
    serializer_class = ConfessionSerializer

class LikeCreateView(generics.CreateAPIView):
    serializer_class = LikeSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        confession_id = request.data.get("confession")
        if Like.objects.filter(user=user, confession_id=confession_id).exists():
            return Response({'detail': 'Already liked'}, status=status.HTTP_400_BAD_REQUEST)
        like = Like.objects.create(user=user, confession_id=confession_id)
        return Response(LikeSerializer(like).data, status=status.HTTP_201_CREATED)

class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
