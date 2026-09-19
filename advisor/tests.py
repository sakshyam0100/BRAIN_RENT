from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import AdvisorProfile
from question.models import Question, Category
from review.models import Review
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


class AdvisorProfileViewTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.advisor_user = User.objects.create_user(
            username='advisor',
            email='advisor@test.com',
            password='testpass123',
            role='advisor',
            first_name='John',
            last_name='Doe'
        )
        
        self.questioner_user = User.objects.create_user(
            username='questioner',
            email='questioner@test.com',
            password='testpass123',
            role='questioner'
        )
        
        # Create categories
        self.tech_category = Category.objects.create(
            name='Technology',
            description='Tech questions'
        )
        
        self.business_category = Category.objects.create(
            name='Business',
            description='Business questions'
        )
        
        # Create approved advisor profile
        self.advisor = AdvisorProfile.objects.create(
            user=self.advisor_user,
            bio='Experienced technology advisor with 10+ years in software development',
            experience=10,
            verification_status='approved'
        )
        self.advisor.expertise.add(self.tech_category, self.business_category)
        
        # Create test questions
        self.question1 = Question.objects.create(
            questioner=self.questioner_user,
            category=self.tech_category,
            title='Django question',
            description='How to use Django?'
        )
        
        self.question2 = Question.objects.create(
            questioner=self.questioner_user,
            category=self.business_category,
            title='Business question',
            description='Business advice needed'
        )
        
        # Create test reviews
        self.review1 = Review.objects.create(
            question=self.question1,
            advisor=self.advisor,
            questioner=self.questioner_user,
            rating=5,
            comment='Excellent advice!'
        )
        
        self.review2 = Review.objects.create(
            question=self.question2,
            advisor=self.advisor,
            questioner=self.questioner_user,
            rating=4,
            comment='Very helpful, thank you!'
        )

    def test_advisor_profile_view_success(self):
        """Test that advisor profile view loads successfully"""
        self.client.login(username='questioner', password='testpass123')
        response = self.client.get(reverse('advisor_profile_view', args=[self.advisor.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertContains(response, 'Experienced technology advisor')
        self.assertContains(response, '10 years')

    def test_advisor_profile_view_unapproved_advisor(self):
        """Test that unapproved advisors cannot be viewed"""
        self.client.login(username='questioner', password='testpass123')
        
        unapproved_advisor = AdvisorProfile.objects.create(
            user=User.objects.create_user(
                username='unapproved',
                email='unapproved@test.com',
                password='testpass123',
                role='advisor'
            ),
            bio='Test bio',
            experience=5,
            verification_status='pending'
        )
        
        response = self.client.get(reverse('advisor_profile_view', args=[unapproved_advisor.id]))
        self.assertEqual(response.status_code, 404)

    def test_advisor_profile_view_rating_calculation(self):
        """Test that ratings are calculated correctly"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('advisor_profile_view', args=[self.advisor.id]))
        self.assertEqual(response.status_code, 200)
        
        # Average should be (5 + 4) / 2 = 4.5
        self.assertContains(response, '4.5')
        self.assertEqual(response.context['average_rating'], 4.5)
        self.assertEqual(response.context['total_reviews'], 2)

    def test_advisor_profile_view_rating_distribution(self):
        """Test that rating distribution is calculated correctly"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('advisor_profile_view', args=[self.advisor.id]))
        self.assertEqual(response.status_code, 200)
        
        distribution = response.context['rating_distribution']
        self.assertEqual(distribution['5']['count'], 1)  # One 5-star review
        self.assertEqual(distribution['4']['count'], 1)  # One 4-star review
        self.assertEqual(distribution['3']['count'], 0)  # No 3-star reviews
        self.assertEqual(distribution['2']['count'], 0)  # No 2-star reviews
        self.assertEqual(distribution['1']['count'], 0)  # No 1-star reviews

    def test_advisor_profile_view_expertise_display(self):
        """Test that expertise areas are displayed correctly"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('advisor_profile_view', args=[self.advisor.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Technology')
        self.assertContains(response, 'Business')

    def test_advisor_profile_view_no_reviews(self):
        """Test profile view with no reviews"""
        self.client.login(username='questioner', password='testpass123')
        
        # Create advisor with no reviews
        new_advisor = AdvisorProfile.objects.create(
            user=User.objects.create_user(
                username='newadvisor',
                email='newadvisor@test.com',
                password='testpass123',
                role='advisor'
            ),
            bio='New advisor',
            experience=2,
            verification_status='approved'
        )
        
        response = self.client.get(reverse('advisor_profile_view', args=[new_advisor.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['average_rating'], 0)
        self.assertEqual(response.context['total_reviews'], 0)
        self.assertContains(response, "hasn't received any reviews yet")

    def test_advisor_profile_view_completion_rate(self):
        """Test that completion rate is calculated correctly"""
        self.client.login(username='questioner', password='testpass123')
        
        from question.models import QuestionAssignment
        
        # Create some assignments
        QuestionAssignment.objects.create(
            question=self.question1,
            advisor=self.advisor,
            status='completed'
        )
        
        QuestionAssignment.objects.create(
            question=self.question2,
            advisor=self.advisor,
            status='accepted'
        )
        
        response = self.client.get(reverse('advisor_profile_view', args=[self.advisor.id]))
        self.assertEqual(response.status_code, 200)
        
        # 1 completed out of 2 total = 50%
        self.assertEqual(response.context['completion_rate'], 50.0)

    def test_advisor_profile_view_invalid_id(self):
        """Test that invalid advisor ID returns 404"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('advisor_profile_view', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_advisor_profile_view_context_data(self):
        """Test that all required context data is present"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('advisor_profile_view', args=[self.advisor.id]))
        self.assertEqual(response.status_code, 200)
        
        self.assertIn('advisor', response.context)
        self.assertIn('reviews', response.context)
        self.assertIn('average_rating', response.context)
        self.assertIn('total_reviews', response.context)
        self.assertIn('rating_distribution', response.context)
        self.assertIn('completion_rate', response.context)
        self.assertIn('recent_assignments', response.context)

    def test_advisor_profile_view_review_details(self):
        """Test that review details are displayed correctly"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('advisor_profile_view', args=[self.advisor.id]))
        self.assertEqual(response.status_code, 200)
        
        reviews = response.context['reviews']
        self.assertEqual(len(reviews), 2)
        
        # Check review content exists (order may vary)
        review_comments = [review.comment for review in reviews]
        self.assertIn('Excellent advice!', review_comments)
        self.assertIn('Very helpful, thank you!', review_comments)
        
        review_ratings = [review.rating for review in reviews]
        self.assertIn(5, review_ratings)
        self.assertIn(4, review_ratings)
