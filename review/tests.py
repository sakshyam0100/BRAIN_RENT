from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from question.models import Question, Category
from advisor.models import AdvisorProfile, AdvisorVerification
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()


class ReviewModelTestCase(TestCase):
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
        
        # Create question
        self.question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='Test question',
            description='Test description',
            status='completed'
        )

    def test_review_creation(self):
        """Test creating a review"""
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=5,
            comment='Excellent service!'
        )
        
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent service!')
        self.assertEqual(str(review), f'{self.advisor_user.username} - 5★ (Test question)')

    def test_review_updated_at_field(self):
        """Test that updated_at field works correctly"""
        import time
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=4,
            comment='Good service'
        )
        
        initial_updated_at = review.updated_at
        
        # Wait a moment to ensure timestamp difference
        time.sleep(0.1)
        
        # Simulate an update
        review.rating = 5
        review.save()
        
        # updated_at should be different after save
        review.refresh_from_db()
        self.assertNotEqual(review.updated_at, initial_updated_at)


class ReviewFormTestCase(TestCase):
    def test_valid_review_form(self):
        """Test valid review form submission"""
        form_data = {
            'rating': 5,
            'comment': 'Excellent advisor!'
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_without_comment(self):
        """Test review form without optional comment"""
        form_data = {
            'rating': 4,
            'comment': ''
        }
        form = ReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_review_form_invalid_rating(self):
        """Test review form with invalid rating"""
        form_data = {
            'rating': 6,  # Invalid: must be 1-5
            'comment': 'Test comment'
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_review_form_comment_too_long(self):
        """Test review form with comment exceeding max length"""
        long_comment = 'x' * 1001  # Exceeds 1000 character limit
        form_data = {
            'rating': 5,
            'comment': long_comment
        }
        form = ReviewForm(data=form_data)
        self.assertFalse(form.is_valid())


class ReviewViewTestCase(TestCase):
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
        
        self.other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123',
            role='questioner'
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
        
        # Create completed question
        self.question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='Test question',
            description='Test description',
            status='completed'
        )
        
        # Create assignment
        from question.models import QuestionAssignment
        QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )

    def test_submit_review_success(self):
        """Test successful review submission"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(
            reverse('submit_review', args=[self.question.id]),
            {
                'rating': 5,
                'comment': 'Excellent advisor!'
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Review.objects.count(), 1)
        
        review = Review.objects.first()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent advisor!')

    def test_submit_review_duplicate(self):
        """Test that duplicate reviews are prevented"""
        # Create initial review
        Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=4,
            comment='Good advisor'
        )
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(
            reverse('submit_review', args=[self.question.id]),
            {
                'rating': 5,
                'comment': 'Updated review'
            }
        )
        
        self.assertEqual(response.status_code, 403)  # Forbidden for duplicate
        self.assertEqual(Review.objects.count(), 1)  # Still only one review

    def test_submit_review_wrong_user(self):
        """Test that other users cannot submit reviews"""
        self.client.login(username='other', password='testpass123')
        
        response = self.client.post(
            reverse('submit_review', args=[self.question.id]),
            {
                'rating': 5,
                'comment': 'Test review'
            }
        )
        
        # Should return 404 since get_object_or_404 fails for wrong user
        self.assertEqual(response.status_code, 404)

    def test_edit_review_success(self):
        """Test successful review editing"""
        # Create initial review
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=4,
            comment='Good advisor'
        )
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(
            reverse('edit_review', args=[review.id]),
            {
                'rating': 5,
                'comment': 'Excellent advisor!'
            }
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        review.refresh_from_db()
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent advisor!')

    def test_edit_review_wrong_user(self):
        """Test that other users cannot edit reviews"""
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=4,
            comment='Good advisor'
        )
        
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(reverse('edit_review', args=[review.id]))
        self.assertEqual(response.status_code, 404)  # Not found for wrong user

    def test_delete_review_success(self):
        """Test successful review deletion"""
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=4,
            comment='Good advisor'
        )
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(reverse('delete_review', args=[review.id]))
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertEqual(Review.objects.count(), 0)  # Review deleted

    def test_delete_review_wrong_user(self):
        """Test that other users cannot delete reviews"""
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=4,
            comment='Good advisor'
        )
        
        self.client.login(username='other', password='testpass123')
        
        response = self.client.get(reverse('delete_review', args=[review.id]))
        self.assertEqual(response.status_code, 404)  # Not found for wrong user

    def test_my_reviews_view(self):
        """Test my reviews view"""
        # Create some reviews
        for i in range(3):
            question = Question.objects.create(
                questioner=self.questioner,
                category=self.category,
                title=f'Question {i}',
                description=f'Description {i}',
                status='completed'
            )
            
            from question.models import QuestionAssignment
            QuestionAssignment.objects.create(
                question=question,
                advisor=self.advisor,
                status='accepted'
            )
            
            Review.objects.create(
                question=question,
                advisor=self.advisor,
                questioner=self.questioner,
                rating=5 - i,
                comment=f'Comment {i}'
            )
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('my_reviews'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['reviews']), 3)

    def test_my_reviews_access_control(self):
        """Test that advisors cannot access my reviews"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('my_reviews'))
        self.assertEqual(response.status_code, 403)  # Forbidden for advisors
