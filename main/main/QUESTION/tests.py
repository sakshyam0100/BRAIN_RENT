from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Question, Category
from advisor.models import AdvisorProfile

User = get_user_model()


class QuestionSearchTestCase(TestCase):
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
        
        self.advisor = AdvisorProfile.objects.create(
            user=self.advisor_user,
            bio='Test advisor bio',
            experience=5,
            verification_status='approved'
        )
        
        # Create test categories
        self.tech_category = Category.objects.create(
            name='Technology',
            description='Tech related questions'
        )
        
        self.business_category = Category.objects.create(
            name='Business',
            description='Business related questions'
        )
        
        # Create test questions
        self.question1 = Question.objects.create(
            questioner=self.questioner,
            category=self.tech_category,
            title='Django authentication problem',
            description='How to implement user authentication in Django?'
        )
        
        self.question2 = Question.objects.create(
            questioner=self.questioner,
            category=self.business_category,
            title='Business startup advice',
            description='Need advice on starting a small business'
        )
        
        self.question3 = Question.objects.create(
            questioner=self.questioner,
            category=self.tech_category,
            title='Python REST API',
            description='How to create REST APIs using Python?'
        )

    def test_search_by_title(self):
        """Test searching questions by title"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['questions']), 1)
        self.assertEqual(response.context['questions'][0].title, 'Django authentication problem')

    def test_search_by_description(self):
        """Test searching questions by description"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'q': 'authentication'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['questions']), 1)

    def test_search_by_category(self):
        """Test filtering questions by category"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'category': 'Technology'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['questions']), 2)

    def test_combined_search(self):
        """Test combined search with query and category filter"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(
            reverse('available_questions'), 
            {'q': 'API', 'category': 'Technology'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['questions']), 1)

    def test_no_search_results(self):
        """Test when no results match the search"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'q': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['questions']), 0)

    def test_empty_search_shows_all(self):
        """Test that empty search shows all pending questions"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['questions']), 3)
