from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Payment
from question.models import Question, Category
from advisor.models import AdvisorProfile
from question.models import QuestionAssignment

User = get_user_model()


class PaymentModelTestCase(TestCase):
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
            verification_status='approved',
            consultation_rate=500.00
        )
        self.advisor.expertise.add(self.category)
        
        # Create question
        self.question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='Test question',
            description='Test description',
            status='accepted'
        )
        
        # Create assignment
        self.assignment = QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )

    def test_payment_creation(self):
        """Test basic payment creation"""
        payment = Payment.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            amount=500.00,
            status='pending'
        )
        
        self.assertEqual(payment.question, self.question)
        self.assertEqual(payment.advisor, self.advisor)
        self.assertEqual(payment.questioner, self.questioner)
        self.assertEqual(payment.amount, 500.00)
        self.assertEqual(payment.status, 'pending')
        self.assertEqual(payment.currency, 'NPR')

    def test_payment_mark_completed(self):
        """Test marking payment as completed"""
        payment = Payment.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            amount=500.00,
            status='pending'
        )
        
        self.assertFalse(payment.completed_at)
        
        payment.mark_completed(txn_id='test_txn_123', idx='test_idx_456')
        
        self.assertEqual(payment.status, 'completed')
        self.assertEqual(payment.khalti_txn_id, 'test_txn_123')
        self.assertEqual(payment.khalti_idx, 'test_idx_456')
        self.assertIsNotNone(payment.completed_at)

    def test_payment_mark_failed(self):
        """Test marking payment as failed"""
        payment = Payment.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            amount=500.00,
            status='pending'
        )
        
        payment.mark_failed()
        
        self.assertEqual(payment.status, 'failed')

    def test_payment_mark_refunded(self):
        """Test marking payment as refunded"""
        payment = Payment.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            amount=500.00,
            status='completed'
        )
        
        payment.mark_refunded()
        
        self.assertEqual(payment.status, 'refunded')
        self.assertIsNotNone(payment.completed_at)

    def test_payment_str_representation(self):
        """Test payment string representation"""
        payment = Payment.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            amount=500.00,
            status='pending'
        )
        
        # Check that the string contains the expected components
        payment_str = str(payment)
        self.assertIn(f"Payment {payment.id}", payment_str)
        self.assertIn(self.questioner.username, payment_str)
        self.assertIn(self.advisor.user.username, payment_str)
        self.assertIn("500.0", payment_str)  # Decimal might be formatted differently
        self.assertIn("NPR", payment_str)


class KhaltiServiceTestCase(TestCase):
    def test_khalti_service_initialization(self):
        """Test Khalti service initialization"""
        from .khalti_service import KhaltiPaymentService
        
        service = KhaltiPaymentService()
        
        self.assertIsNotNone(service.secret_key)
        self.assertIsNotNone(service.public_key)
        self.assertEqual(service.BASE_URL, "https://a.khalti.com/api/v2")

    def test_khalti_config_retrieval(self):
        """Test Khalti configuration retrieval"""
        from .config import get_khalti_config
        
        config = get_khalti_config()
        
        self.assertIn('public_key', config)
        self.assertIn('secret_key', config)