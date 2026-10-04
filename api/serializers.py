from rest_framework import serializers
from django.contrib.auth import get_user_model
from accounts.models import CustomUser
from question.models import Category, Question, QuestionAssignment, Answer
from advisor.models import AdvisorProfile, AdvisorVerification
from chat.models import Conversation, Message
from review.models import Review
from payment.models import Payment

User = get_user_model()


# User Serializers
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone_number', 'profile_picture', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'password2', 'role', 'phone_number']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'profile_picture']


# Category Serializers
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'icon']
        read_only_fields = ['id']


# Question Serializers
class QuestionSerializer(serializers.ModelSerializer):
    questioner = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Question
        fields = ['id', 'questioner', 'category', 'category_id', 'title', 'description', 'status', 'created_at']
        read_only_fields = ['id', 'questioner', 'created_at']

    def create(self, validated_data):
        validated_data['questioner'] = self.context['request'].user
        return super().create(validated_data)


class QuestionListSerializer(serializers.ModelSerializer):
    questioner = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Question
        fields = ['id', 'questioner', 'category', 'title', 'description', 'status', 'created_at']

    def get_questioner(self, obj):
        return {
            'id': obj.questioner.id,
            'username': obj.questioner.username,
            'profile_picture': obj.questioner.profile_picture.url if obj.questioner.profile_picture else None
        }


# Answer Serializers
class AnswerSerializer(serializers.ModelSerializer):
    advisor = serializers.SerializerMethodField()
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = Answer
        fields = ['id', 'question', 'advisor', 'content', 'created_at', 'updated_at']
        read_only_fields = ['id', 'advisor', 'created_at', 'updated_at']

    def get_advisor(self, obj):
        return {
            'id': obj.advisor.id,
            'username': obj.advisor.user.username,
            'bio': obj.advisor.bio
        }


# Advisor Serializers
class AdvisorProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    expertise = CategorySerializer(many=True, read_only=True)
    expertise_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    average_rating = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()

    class Meta:
        model = AdvisorProfile
        fields = ['id', 'user', 'bio', 'expertise', 'expertise_ids', 'experience', 'consultation_rate',
                  'verification_status', 'average_rating', 'total_reviews']
        read_only_fields = ['id', 'user', 'verification_status']

    def get_average_rating(self, obj):
        reviews = Review.objects.filter(advisor=obj)
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0

    def get_total_reviews(self, obj):
        return Review.objects.filter(advisor=obj).count()

    def update(self, instance, validated_data):
        expertise_ids = validated_data.pop('expertise_ids', None)
        if expertise_ids is not None:
            instance.expertise.set(expertise_ids)
        return super().update(instance, validated_data)


class AdvisorListSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    expertise = CategorySerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = AdvisorProfile
        fields = ['id', 'user', 'bio', 'expertise', 'experience', 'consultation_rate',
                  'verification_status', 'average_rating']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'username': obj.user.username,
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else None
        }

    def get_average_rating(self, obj):
        reviews = Review.objects.filter(advisor=obj)
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0


class AdvisorVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvisorVerification
        fields = ['id', 'government_id', 'certificate', 'professional_license', 'status', 'admin_note', 'verified_at']
        read_only_fields = ['id', 'status', 'admin_note', 'verified_at']


# Assignment Serializers
class QuestionAssignmentSerializer(serializers.ModelSerializer):
    question = QuestionListSerializer(read_only=True)
    advisor = AdvisorListSerializer(read_only=True)

    class Meta:
        model = QuestionAssignment
        fields = ['id', 'question', 'advisor', 'status', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']


# Chat Serializers
class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ['id', 'sender', 'content', 'created_at', 'is_read']
        read_only_fields = ['id', 'sender', 'created_at', 'is_read']


class ConversationSerializer(serializers.ModelSerializer):
    question = QuestionListSerializer(read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'question', 'messages', 'unread_count', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


class ConversationListSerializer(serializers.ModelSerializer):
    question = QuestionListSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ['id', 'question', 'last_message', 'unread_count', 'created_at']

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'id': last_message.id,
                'content': last_message.content[:100],
                'sender': last_message.sender.username,
                'created_at': last_message.created_at
            }
        return None

    def get_unread_count(self, obj):
        user = self.context['request'].user
        return obj.messages.filter(is_read=False).exclude(sender=user).count()


# Review Serializers
class ReviewSerializer(serializers.ModelSerializer):
    questioner = UserSerializer(read_only=True)
    advisor = AdvisorListSerializer(read_only=True)
    question = QuestionListSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ['id', 'questioner', 'advisor', 'question', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'questioner', 'created_at']

    def create(self, validated_data):
        validated_data['questioner'] = self.context['request'].user
        return super().create(validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']


# Payment Serializers
class PaymentSerializer(serializers.ModelSerializer):
    question = QuestionListSerializer(read_only=True)
    advisor = AdvisorListSerializer(read_only=True)
    questioner = UserSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'question', 'advisor', 'questioner', 'amount', 'currency', 'status',
                  'payment_method', 'khalti_txn_id', 'khalti_idx', 'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at', 'khalti_txn_id', 'khalti_idx']


class PaymentInitiateSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()


class PaymentVerifySerializer(serializers.Serializer):
    pidx = serializers.CharField()
