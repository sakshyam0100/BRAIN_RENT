from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Notification
from .utils import create_notification, notify_question_accepted, notify_answer_submitted, notify_review_received, notify_new_question
from question.models import Question, Category
from advisor.models import AdvisorProfile
from review.models import Review

User = get_user_model()


class NotificationModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )

    def test_notification_creation(self):
        """Test basic notification creation"""
        notification = create_notification(
            recipient=self.user,
            notification_type='system',
            title='Test Notification',
            message='This is a test notification'
        )
        
        self.assertEqual(notification.recipient, self.user)
        self.assertEqual(notification.notification_type, 'system')
        self.assertEqual(notification.title, 'Test Notification')
        self.assertFalse(notification.is_read)

    def test_notification_mark_as_read(self):
        """Test marking notification as read"""
        notification = create_notification(
            recipient=self.user,
            notification_type='system',
            title='Test',
            message='Test message'
        )
        
        self.assertFalse(notification.is_read)
        notification.mark_as_read()
        self.assertTrue(notification.is_read)

    def test_notification_with_related_ids(self):
        """Test notification with related question and advisor IDs"""
        notification = create_notification(
            recipient=self.user,
            notification_type='question_accepted',
            title='Question Accepted',
            message='Your question was accepted',
            related_question_id=123,
            related_advisor_id=456
        )
        
        self.assertEqual(notification.related_question_id, 123)
        self.assertEqual(notification.related_advisor_id, 456)


class NotificationUtilsTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.questioner = User.objects.create_user(
            username='questioner',
            email='questioner@test.com',
            password='testpass123',
            role='questioner'
        )
        
        self.advisor_user = User.objects.create_user(
            username='advisor',
            email='advisor@test.com',
            password='testpass123',
            role='advisor'
        )
        
        # Create category and advisor
        self.category = Category.objects.create(
            name='Technology',
            description='Tech questions'
        )
        
        self.advisor = AdvisorProfile.objects.create(
            user=self.advisor_user,
            bio='Test advisor',
            experience=5,
            verification_status='approved'
        )
        self.advisor.expertise.add(self.category)
        
        # Create question
        self.question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='Test question',
            description='Test description',
            status='completed'
        )

    def test_notify_question_accepted(self):
        """Test question accepted notification"""
        notification = notify_question_accepted(self.question, self.advisor)
        
        self.assertEqual(notification.recipient, self.questioner)
        self.assertEqual(notification.notification_type, 'question_accepted')
        self.assertEqual(notification.related_question_id, self.question.id)
        self.assertEqual(notification.related_advisor_id, self.advisor.id)
        self.assertIn('accepted', notification.title.lower())

    def test_notify_answer_submitted(self):
        """Test answer submitted notification"""
        notification = notify_answer_submitted(self.question, self.advisor)
        
        self.assertEqual(notification.recipient, self.questioner)
        self.assertEqual(notification.notification_type, 'answer_submitted')
        self.assertEqual(notification.related_question_id, self.question.id)
        self.assertIn('answer', notification.title.lower())

    def test_notify_review_received(self):
        """Test review received notification"""
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=5,
            comment='Excellent!'
        )
        
        notification = notify_review_received(review)
        
        self.assertEqual(notification.recipient, self.advisor_user)
        self.assertEqual(notification.notification_type, 'review_received')
        self.assertEqual(notification.related_question_id, self.question.id)
        self.assertIn('review', notification.title.lower())

    def test_notify_new_question(self):
        """Test new question notification to advisors"""
        notifications = notify_new_question(self.question)
        
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].recipient, self.advisor_user)
        self.assertEqual(notifications[0].notification_type, 'new_question')
        self.assertEqual(notifications[0].related_question_id, self.question.id)


class NotificationViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@test.com',
            password='testpass123'
        )
        
        # Create some test notifications
        for i in range(5):
            Notification.objects.create(
                recipient=self.user,
                notification_type='system',
                title=f'Notification {i}',
                message=f'Test message {i}',
                is_read=(i < 2)  # First 2 are read
            )

    def test_notification_list_view(self):
        """Test notification list view"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('notification_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['notifications']), 5)
        self.assertEqual(response.context['unread_count'], 3)

    def test_mark_as_read(self):
        """Test marking notification as read"""
        notification = Notification.objects.filter(recipient=self.user, is_read=False).first()
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('mark_as_read', args=[notification.id]))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_all_as_read(self):
        """Test marking all notifications as read"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('mark_all_as_read'))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        unread_count = Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_delete_notification(self):
        """Test deleting notification"""
        notification = Notification.objects.filter(recipient=self.user).first()
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('delete_notification', args=[notification.id]))
        self.assertEqual(response.status_code, 302)  # Redirect
        
        self.assertEqual(Notification.objects.filter(recipient=self.user).count(), 4)

    def test_notification_count_api(self):
        """Test notification count API"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(reverse('notification_count'))
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        self.assertEqual(data['count'], 3)  # 3 unread notifications

    def test_notification_access_control(self):
        """Test that users can only see their own notifications"""
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123'
        )
        
        other_notification = Notification.objects.create(
            recipient=other_user,
            notification_type='system',
            title='Other notification',
            message='Other message'
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Try to mark other user's notification as read
        response = self.client.post(reverse('mark_as_read', args=[other_notification.id]))
        self.assertEqual(response.status_code, 404)  # Not found


class NotificationSignalsTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.questioner = User.objects.create_user(
            username='questioner',
            email='questioner@test.com',
            password='testpass123',
            role='questioner'
        )
        
        self.advisor_user = User.objects.create_user(
            username='advisor',
            email='advisor@test.com',
            password='testpass123',
            role='advisor'
        )
        
        # Create category and advisor
        self.category = Category.objects.create(
            name='Technology',
            description='Tech questions'
        )
        
        self.advisor = AdvisorProfile.objects.create(
            user=self.advisor_user,
            bio='Test advisor',
            experience=5,
            verification_status='approved'
        )
        self.advisor.expertise.add(self.category)
        
        # Create question
        self.question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='Test question',
            description='Test description',
            status='pending'
        )

    def test_question_assignment_creates_notification(self):
        """Test that creating a question assignment triggers notification"""
        from question.models import QuestionAssignment
        
        initial_count = Notification.objects.filter(
            recipient=self.questioner,
            notification_type='question_accepted'
        ).count()
        
        # Create assignment
        assignment = QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )
        
        # Check notification was created
        new_count = Notification.objects.filter(
            recipient=self.questioner,
            notification_type='question_accepted'
        ).count()
        
        self.assertEqual(new_count, initial_count + 1)
        
        notification = Notification.objects.filter(
            recipient=self.questioner,
            notification_type='question_accepted'
        ).first()
        
        self.assertEqual(notification.related_question_id, self.question.id)
        self.assertEqual(notification.related_advisor_id, self.advisor.id)

    def test_answer_submission_creates_notification(self):
        """Test that submitting an answer triggers notification"""
        from question.models import Answer
        
        initial_count = Notification.objects.filter(
            recipient=self.questioner,
            notification_type='answer_submitted'
        ).count()
        
        # Create answer
        answer = Answer.objects.create(
            question=self.question,
            advisor=self.advisor,
            content='Test answer content'
        )
        
        # Check notification was created
        new_count = Notification.objects.filter(
            recipient=self.questioner,
            notification_type='answer_submitted'
        ).count()
        
        self.assertEqual(new_count, initial_count + 1)
        
        notification = Notification.objects.filter(
            recipient=self.questioner,
            notification_type='answer_submitted'
        ).first()
        
        self.assertEqual(notification.related_question_id, self.question.id)

    def test_review_submission_creates_notification(self):
        """Test that submitting a review triggers notification"""
        initial_count = Notification.objects.filter(
            recipient=self.advisor_user,
            notification_type='review_received'
        ).count()
        
        # Create review
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=5,
            comment='Excellent!'
        )
        
        # Check notification was created
        new_count = Notification.objects.filter(
            recipient=self.advisor_user,
            notification_type='review_received'
        ).count()
        
        self.assertEqual(new_count, initial_count + 1)
        
        notification = Notification.objects.filter(
            recipient=self.advisor_user,
            notification_type='review_received'
        ).first()
        
        self.assertEqual(notification.related_question_id, self.question.id)

    def test_new_question_creates_notification(self):
        """Test that creating a new question triggers notifications to advisors"""
        initial_count = Notification.objects.filter(
            recipient=self.advisor_user,
            notification_type='new_question'
        ).count()
        
        # Create new question
        new_question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='New test question',
            description='New test description',
            status='pending'
        )
        
        # Check notification was created
        new_count = Notification.objects.filter(
            recipient=self.advisor_user,
            notification_type='new_question'
        ).count()
        
        self.assertEqual(new_count, initial_count + 1)
        
        notification = Notification.objects.filter(
            recipient=self.advisor_user,
            notification_type='new_question'
        ).first()
        
        self.assertEqual(notification.related_question_id, new_question.id)
