from rest_framework import generics, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Q, Avg
from django_filters.rest_framework import DjangoFilterBackend

from accounts.models import CustomUser
from question.models import Category, Question, QuestionAssignment, Answer
from advisor.models import AdvisorProfile, AdvisorVerification
from chat.models import Conversation, Message
from review.models import Review
from payment.models import Payment

from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserUpdateSerializer,
    CategorySerializer, QuestionSerializer, QuestionListSerializer,
    AnswerSerializer, AdvisorProfileSerializer, AdvisorListSerializer,
    AdvisorVerificationSerializer, QuestionAssignmentSerializer,
    MessageSerializer, ConversationSerializer, ConversationListSerializer,
    ReviewSerializer, ReviewUpdateSerializer, PaymentSerializer,
    PaymentInitiateSerializer, PaymentVerifySerializer
)


# ==================== Authentication Views ====================

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            'user': UserSerializer(user).data,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom login view that includes user data in response"""
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = CustomUser.objects.get(username=request.data.get('username'))
            response.data['user'] = UserSerializer(user).data
        return response


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer


# ==================== Category Views ====================

class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    ordering = ['name']


class CategoryDetailView(generics.RetrieveAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


# ==================== Question Views ====================

class QuestionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'category']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'questioner':
            return Question.objects.filter(questioner=user).select_related('category', 'questioner')
        elif user.role == 'advisor':
            # Advisors can see pending questions and their assigned questions
            advisor_profile = AdvisorProfile.objects.filter(user=user).first()
            if advisor_profile:
                return Question.objects.filter(
                    Q(status='pending') | Q(assignments__advisor=advisor_profile)
                ).distinct().select_related('category', 'questioner')
            return Question.objects.none()
        return Question.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return QuestionListSerializer
        return QuestionSerializer

    def perform_create(self, serializer):
        if self.request.user.role != 'questioner':
            return Response({'error': 'Only questioners can create questions'},
                          status=status.HTTP_403_FORBIDDEN)
        serializer.save(questioner=self.request.user)

    @action(detail=True, methods=['get'])
    def answer(self, request, pk=None):
        """Get the official answer for a question"""
        question = self.get_object()
        try:
            answer = Answer.objects.get(question=question)
            serializer = AnswerSerializer(answer)
            return Response(serializer.data)
        except Answer.DoesNotExist:
            return Response({'error': 'No answer submitted yet'},
                          status=status.HTTP_404_NOT_FOUND)


# ==================== Advisor Views ====================

class AdvisorViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['verification_status', 'expertise']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'bio']
    ordering_fields = ['experience', 'consultation_rate', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return AdvisorProfile.objects.filter(verification_status='approved').select_related('user').prefetch_related('expertise')

    def get_serializer_class(self):
        if self.action == 'list':
            return AdvisorListSerializer
        return AdvisorProfileSerializer

    def get_object(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            # Advisors can only update their own profile
            if self.request.user.role == 'advisor':
                return AdvisorProfile.objects.get(user=self.request.user)
        return super().get_object()

    def perform_update(self, serializer):
        if self.request.user.role != 'advisor':
            return Response({'error': 'Only advisors can update their profile'},
                          status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get all reviews for an advisor"""
        advisor = self.get_object()
        reviews = Review.objects.filter(advisor=advisor).select_related('questioner', 'question')
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get', 'post'])
    def verification(self, request):
        """Get or submit advisor verification"""
        if request.user.role != 'advisor':
            return Response({'error': 'Only advisors can submit verification'},
                          status=status.HTTP_403_FORBIDDEN)

        advisor_profile = AdvisorProfile.objects.get(user=request.user)

        if request.method == 'GET':
            try:
                verification = AdvisorVerification.objects.get(advisor=advisor_profile)
                serializer = AdvisorVerificationSerializer(verification)
                return Response(serializer.data)
            except AdvisorVerification.DoesNotExist:
                return Response({'error': 'No verification submitted yet'},
                              status=status.HTTP_404_NOT_FOUND)

        elif request.method == 'POST':
            try:
                verification = AdvisorVerification.objects.get(advisor=advisor_profile)
                return Response({'error': 'Verification already submitted'},
                              status=status.HTTP_400_BAD_REQUEST)
            except AdvisorVerification.DoesNotExist:
                serializer = AdvisorVerificationSerializer(data=request.data)
                if serializer.is_valid():
                    serializer.save(advisor=advisor_profile)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== Assignment Views ====================

class AssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionAssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'advisor':
            advisor_profile = AdvisorProfile.objects.filter(user=user).first()
            if advisor_profile:
                return QuestionAssignment.objects.filter(advisor=advisor_profile).select_related(
                    'question', 'question__category', 'question__questioner'
                )
        return QuestionAssignment.objects.none()

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get available (pending) questions for advisors"""
        if request.user.role != 'advisor':
            return Response({'error': 'Only advisors can view available questions'},
                          status=status.HTTP_403_FORBIDDEN)

        advisor_profile = AdvisorProfile.objects.filter(user=request.user).first()
        if not advisor_profile or advisor_profile.verification_status != 'approved':
            return Response({'error': 'Advisor account not approved'},
                          status=status.HTTP_403_FORBIDDEN)

        questions = Question.objects.filter(status='pending').select_related('category', 'questioner')
        serializer = QuestionListSerializer(questions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Accept a question assignment"""
        if request.user.role != 'advisor':
            return Response({'error': 'Only advisors can accept questions'},
                          status=status.HTTP_403_FORBIDDEN)

        advisor_profile = AdvisorProfile.objects.filter(user=request.user).first()
        if not advisor_profile or advisor_profile.verification_status != 'approved':
            return Response({'error': 'Advisor account not approved'},
                          status=status.HTTP_403_FORBIDDEN)

        question = Question.objects.get(pk=pk)
        if question.status != 'pending':
            return Response({'error': 'Question is not available'},
                          status=status.HTTP_400_BAD_REQUEST)

        # Create assignment
        assignment, created = QuestionAssignment.objects.get_or_create(
            question=question,
            advisor=advisor_profile,
            defaults={'status': 'accepted'}
        )

        if not created:
            return Response({'error': 'Question already assigned'},
                          status=status.HTTP_400_BAD_REQUEST)

        # Update question status
        question.status = 'accepted'
        question.save()

        # Create conversation
        Conversation.objects.get_or_create(question=question)

        serializer = QuestionAssignmentSerializer(assignment)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ==================== Chat Views ====================

class ConversationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'questioner':
            return Conversation.objects.filter(question__questioner=user).select_related('question')
        elif user.role == 'advisor':
            advisor_profile = AdvisorProfile.objects.filter(user=user).first()
            if advisor_profile:
                return Conversation.objects.filter(
                    question__assignments__advisor=advisor_profile,
                    question__assignments__status='accepted'
                ).select_related('question').distinct()
        return Conversation.objects.none()

    def get_serializer_class(self):
        if self.action == 'list':
            return ConversationListSerializer
        return ConversationSerializer

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a conversation"""
        conversation = self.get_object()

        # Check access
        if request.user.role == 'questioner':
            if conversation.question.questioner != request.user:
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'advisor':
            advisor_profile = AdvisorProfile.objects.filter(user=request.user).first()
            if not QuestionAssignment.objects.filter(
                question=conversation.question,
                advisor=advisor_profile,
                status='accepted'
            ).exists():
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        # Mark unread messages as read
        conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

        messages = conversation.messages.all().order_by('created_at')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message in a conversation"""
        conversation = self.get_object()

        # Check access
        if request.user.role == 'questioner':
            if conversation.question.questioner != request.user:
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'advisor':
            advisor_profile = AdvisorProfile.objects.filter(user=request.user).first()
            if not QuestionAssignment.objects.filter(
                question=conversation.question,
                advisor=advisor_profile,
                status='accepted'
            ).exists():
                return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        # Check if chat is closed
        if conversation.question.status == 'completed':
            return Response({'error': 'Chat is closed'}, status=status.HTTP_400_BAD_REQUEST)

        content = request.data.get('content')
        if not content:
            return Response({'error': 'Content is required'}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content
        )

        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ==================== Review Views ====================

class ReviewViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'questioner':
            return Review.objects.filter(questioner=user).select_related('advisor', 'question')
        elif user.role == 'advisor':
            advisor_profile = AdvisorProfile.objects.filter(user=user).first()
            if advisor_profile:
                return Review.objects.filter(advisor=advisor_profile).select_related('questioner', 'question')
        return Review.objects.none()

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        return ReviewSerializer

    def perform_create(self, serializer):
        if self.request.user.role != 'questioner':
            return Response({'error': 'Only questioners can submit reviews'},
                          status=status.HTTP_403_FORBIDDEN)

        question_id = self.request.data.get('question_id')
        question = Question.objects.get(id=question_id)

        if question.status != 'completed':
            return Response({'error': 'Can only review completed questions'},
                          status=status.HTTP_400_BAD_REQUEST)

        if Review.objects.filter(question=question, questioner=self.request.user).exists():
            return Response({'error': 'Review already submitted'},
                          status=status.HTTP_400_BAD_REQUEST)

        advisor_profile = AdvisorProfile.objects.filter(
            assignments__question=question,
            assignments__status='accepted'
        ).first()

        serializer.save(questioner=self.request.user, advisor=advisor_profile, question=question)

    def perform_update(self, serializer):
        review = self.get_object()
        if review.questioner != self.request.user:
            return Response({'error': 'Can only edit your own reviews'},
                          status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def perform_destroy(self, instance):
        if instance.questioner != self.request.user:
            return Response({'error': 'Can only delete your own reviews'},
                          status=status.HTTP_403_FORBIDDEN)
        instance.delete()


# ==================== Payment Views ====================

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'questioner':
            return Payment.objects.filter(questioner=user).select_related('question', 'advisor', 'advisor__user')
        elif user.role == 'advisor':
            advisor_profile = AdvisorProfile.objects.filter(user=user).first()
            if advisor_profile:
                return Payment.objects.filter(advisor=advisor_profile).select_related('question', 'questioner')
        return Payment.objects.none()

    @action(detail=False, methods=['post'])
    def initiate(self, request):
        """Initiate payment for a question"""
        if request.user.role != 'questioner':
            return Response({'error': 'Only questioners can make payments'},
                          status=status.HTTP_403_FORBIDDEN)

        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question_id = serializer.validated_data['question_id']
        question = Question.objects.get(id=question_id, questioner=request.user)

        # Check if advisor is assigned
        assignment = QuestionAssignment.objects.filter(
            question=question,
            status='accepted'
        ).first()

        if not assignment:
            return Response({'error': 'No advisor assigned to this question'},
                          status=status.HTTP_400_BAD_REQUEST)

        # Check if payment already exists
        existing_payment = Payment.objects.filter(
            question=question,
            status='completed'
        ).first()

        if existing_payment:
            return Response({'error': 'Payment already completed'},
                          status=status.HTTP_400_BAD_REQUEST)

        # Get advisor's consultation rate
        advisor = assignment.advisor
        amount = advisor.consultation_rate

        if amount <= 0:
            return Response({'error': 'Advisor has not set a consultation rate'},
                          status=status.HTTP_400_BAD_REQUEST)

        # Create pending payment
        payment = Payment.objects.create(
            question=question,
            advisor=advisor,
            questioner=request.user,
            amount=amount,
            status='pending'
        )

        # In test mode, auto-complete payment
        from django.conf import settings
        payment_mode = getattr(settings, 'PAYMENT_MODE', 'test')

        if payment_mode == 'test':
            payment.mark_completed()
            serializer = PaymentSerializer(payment)
            return Response({
                'payment': serializer.data,
                'message': 'Payment completed successfully (Test Mode)'
            }, status=status.HTTP_201_CREATED)

        # In sandbox/production, return payment details for Khalti integration
        serializer = PaymentSerializer(payment)
        return Response({
            'payment': serializer.data,
            'message': 'Payment initiated. Complete with Khalti.'
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify payment (for Khalti callback)"""
        payment = self.get_object()

        serializer = PaymentVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pidx = serializer.validated_data['pidx']

        # Verify with Khalti (simplified for now)
        from payment.khalti_service import KhaltiPaymentService
        service = KhaltiPaymentService()
        verification = service.verify_payment(pidx, payment.amount)

        if verification.get('success', False):
            payment.mark_completed(
                txn_id=verification.get('transaction_id'),
                idx=pidx
            )
            serializer = PaymentSerializer(payment)
            return Response({
                'payment': serializer.data,
                'message': 'Payment verified successfully'
            })
        else:
            payment.mark_failed()
            return Response({'error': 'Payment verification failed'},
                          status=status.HTTP_400_BAD_REQUEST)
