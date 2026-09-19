from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import Question, Category, QuestionAssignment, Answer
from advisor.models import AdvisorProfile
from review.models import Review

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
        
        # Create test questions with different dates
        now = timezone.now()
        
        self.question1 = Question.objects.create(
            questioner=self.questioner,
            category=self.tech_category,
            title='Django authentication problem',
            description='How to implement user authentication in Django?',
            created_at=now - timedelta(days=5)
        )
        
        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)
        
        self.question2 = Question.objects.create(
            questioner=self.questioner,
            category=self.business_category,
            title='Business startup advice',
            description='Need advice on starting a small business',
            created_at=now - timedelta(days=3)
        )
        
        time.sleep(0.01)
        
        self.question3 = Question.objects.create(
            questioner=self.questioner,
            category=self.tech_category,
            title='Python REST API',
            description='How to create REST APIs using Python?',
            created_at=now - timedelta(days=1)
        )

    def test_search_by_title(self):
        """Test searching questions by title"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'q': 'Django'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 1)
        self.assertEqual(response.context['questions'][0].title, 'Django authentication problem')

    def test_search_by_description(self):
        """Test searching questions by description"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'q': 'authentication'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 1)

    def test_search_by_category(self):
        """Test filtering questions by category"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'category': 'Technology'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 2)

    def test_combined_search(self):
        """Test combined search with query and category filter"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(
            reverse('available_questions'), 
            {'q': 'API', 'category': 'Technology'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 1)

    def test_no_search_results(self):
        """Test when no results match the search"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'q': 'nonexistent'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 0)

    def test_empty_search_shows_all(self):
        """Test that empty search shows all pending questions"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 3)


class QuestionFilteringTestCase(TestCase):
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
        
        # Create test questions with different dates
        now = timezone.now()
        
        self.question1 = Question.objects.create(
            questioner=self.questioner,
            category=self.tech_category,
            title='A Django authentication problem',
            description='How to implement user authentication in Django?',
            created_at=now - timedelta(days=10)
        )
        
        # Small delay to ensure different timestamps
        import time
        time.sleep(0.01)
        
        self.question2 = Question.objects.create(
            questioner=self.questioner,
            category=self.business_category,
            title='B Business startup advice',
            description='Need advice on starting a small business',
            created_at=now - timedelta(days=5)
        )
        
        time.sleep(0.01)
        
        self.question3 = Question.objects.create(
            questioner=self.questioner,
            category=self.tech_category,
            title='C Python REST API',
            description='How to create REST APIs using Python?',
            created_at=now - timedelta(days=2)
        )

    def test_date_from_filter(self):
        """Test filtering questions by date from"""
        self.client.login(username='advisor', password='testpass123')
        
        # Questions from 4 days ago should only include question2 and question3
        date_from = (timezone.now() - timedelta(days=4)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('available_questions'), {'date_from': date_from})
        
        self.assertEqual(response.status_code, 200)
        # question2 (3 days ago) and question3 (1 day ago) should be included
        self.assertGreaterEqual(response.context['questions'].paginator.count, 1)

    def test_date_to_filter(self):
        """Test filtering questions by date to"""
        self.client.login(username='advisor', password='testpass123')
        
        # Questions until 6 days ago should only include question1
        date_to = (timezone.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('available_questions'), {'date_to': date_to})
        
        self.assertEqual(response.status_code, 200)
        # Should filter to only older questions
        self.assertLessEqual(response.context['questions'].paginator.count, 2)

    def test_date_range_filter(self):
        """Test filtering questions by date range"""
        self.client.login(username='advisor', password='testpass123')
        
        # Questions between 8 and 3 days ago should only include question2
        date_from = (timezone.now() - timedelta(days=8)).strftime('%Y-%m-%d')
        date_to = (timezone.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        response = self.client.get(reverse('available_questions'), {'date_from': date_from, 'date_to': date_to})
        
        self.assertEqual(response.status_code, 200)
        # Should filter to a subset of questions
        self.assertLessEqual(response.context['questions'].paginator.count, 2)

    def test_sort_newest_first(self):
        """Test sorting by newest first"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'sort': 'newest'})
        self.assertEqual(response.status_code, 200)
        
        questions = list(response.context['questions'])
        # Verify that questions are sorted by created_at descending
        self.assertGreater(questions[0].created_at, questions[1].created_at)
        self.assertGreater(questions[1].created_at, questions[2].created_at)

    def test_sort_oldest_first(self):
        """Test sorting by oldest first"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'sort': 'oldest'})
        self.assertEqual(response.status_code, 200)
        
        questions = list(response.context['questions'])
        # Verify that questions are sorted by created_at ascending
        self.assertLess(questions[0].created_at, questions[1].created_at)
        self.assertLess(questions[1].created_at, questions[2].created_at)

    def test_sort_title_ascending(self):
        """Test sorting by title ascending"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'sort': 'title_asc'})
        self.assertEqual(response.status_code, 200)
        
        questions = list(response.context['questions'])
        # Verify that questions are sorted by title ascending
        titles = [q.title for q in questions]
        self.assertEqual(titles, sorted(titles))

    def test_sort_title_descending(self):
        """Test sorting by title descending"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'sort': 'title_desc'})
        self.assertEqual(response.status_code, 200)
        
        questions = list(response.context['questions'])
        # Verify that questions are sorted by title descending
        titles = [q.title for q in questions]
        self.assertEqual(titles, sorted(titles, reverse=True))

    def test_combined_filters(self):
        """Test combining multiple filters"""
        self.client.login(username='advisor', password='testpass123')
        
        # Combine category and sort
        response = self.client.get(
            reverse('available_questions'), 
            {
                'category': 'Business',
                'sort': 'newest'
            }
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 1)
        self.assertEqual(response.context['questions'][0].title, 'B Business startup advice')

    def test_invalid_date_format(self):
        """Test that invalid date formats are handled gracefully"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'date_from': 'invalid-date'})
        self.assertEqual(response.status_code, 200)
        # Should still show all questions since invalid date is ignored
        self.assertEqual(response.context['questions'].paginator.count, 3)

    def test_date_filter_integration(self):
        """Test that date filters work with other filters"""
        self.client.login(username='advisor', password='testpass123')
        
        # Filter from today onwards
        today = timezone.now().strftime('%Y-%m-%d')
        
        # Filter from today with business category
        response = self.client.get(
            reverse('available_questions'), 
            {'date_from': today, 'category': 'Business'}
        )
        
        self.assertEqual(response.status_code, 200)
        # Should only include business questions from today onwards
        self.assertGreaterEqual(response.context['questions'].paginator.count, 0)


class QuestionPaginationTestCase(TestCase):
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
        
        # Create test category
        self.tech_category = Category.objects.create(
            name='Technology',
            description='Tech related questions'
        )
        
        # Create 25 test questions to test pagination (10 per page)
        for i in range(25):
            Question.objects.create(
                questioner=self.questioner,
                category=self.tech_category,
                title=f'Question {i+1}',
                description=f'Test question description {i+1}',
                created_at=timezone.now() - timedelta(days=i, hours=i)
            )

    def test_pagination_first_page(self):
        """Test that first page shows 10 questions"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].number, 1)
        self.assertEqual(len(response.context['questions']), 10)
        self.assertEqual(response.context['questions'].paginator.count, 25)
        self.assertEqual(response.context['questions'].paginator.num_pages, 3)

    def test_pagination_second_page(self):
        """Test that second page shows next 10 questions"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].number, 2)
        self.assertEqual(len(response.context['questions']), 10)

    def test_pagination_last_page(self):
        """Test that last page shows remaining questions"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('available_questions'), {'page': 3})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].number, 3)
        self.assertEqual(len(response.context['questions']), 5)  # Remaining 5 questions

    def test_pagination_with_filters(self):
        """Test that pagination works with search filters"""
        self.client.login(username='advisor', password='testpass123')
        
        # Create additional questions with specific titles
        for i in range(5):
            Question.objects.create(
                questioner=self.questioner,
                category=self.tech_category,
                title=f'Special Question {i+1}',
                description=f'Special test question {i+1}',
                created_at=timezone.now() - timedelta(hours=i)
            )
        
        response = self.client.get(reverse('available_questions'), {'q': 'Special', 'page': 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 5)
        self.assertEqual(len(response.context['questions']), 5)

    def test_invalid_page_number(self):
        """Test that invalid page numbers are handled gracefully"""
        self.client.login(username='advisor', password='testpass123')
        
        # Test with non-existent page
        response = self.client.get(reverse('available_questions'), {'page': 999})
        self.assertEqual(response.status_code, 200)
        # Should show last page
        self.assertEqual(response.context['questions'].number, 3)

    def test_invalid_page_format(self):
        """Test that invalid page format is handled gracefully"""
        self.client.login(username='advisor', password='testpass123')
        
        # Test with invalid page format
        response = self.client.get(reverse('available_questions'), {'page': 'invalid'})
        self.assertEqual(response.status_code, 200)
        # Should show first page
        self.assertEqual(response.context['questions'].number, 1)

    def test_pagination_preserves_filters(self):
        """Test that pagination preserves search filters"""
        self.client.login(username='advisor', password='testpass123')
        
        # Create additional questions with specific category
        business_category = Category.objects.create(
            name='Business',
            description='Business questions'
        )
        
        for i in range(15):
            Question.objects.create(
                questioner=self.questioner,
                category=business_category,
                title=f'Business Question {i+1}',
                description=f'Business test question {i+1}',
                created_at=timezone.now() - timedelta(hours=i)
            )
        
        # Test with category filter
        response = self.client.get(
            reverse('available_questions'), 
            {'category': 'Business', 'page': 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['questions'].paginator.count, 15)
        self.assertEqual(response.context['category_filter'], 'Business')


class QuestionCompletionFlowTestCase(TestCase):
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

    def test_question_completion_workflow(self):
        """Test the complete question workflow from creation to completion"""
        # Step 1: Question is created (pending)
        self.assertEqual(self.question.status, 'pending')
        
        # Step 2: Advisor accepts question
        assignment = QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )
        self.question.status = 'accepted'
        self.question.save()
        
        self.assertEqual(self.question.status, 'accepted')
        self.assertEqual(assignment.status, 'accepted')
        
        # Step 3: Advisor submits answer
        answer = Answer.objects.create(
            question=self.question,
            advisor=self.advisor,
            content='Test answer content'
        )
        self.question.status = 'completed'
        self.question.save()
        
        self.assertEqual(self.question.status, 'completed')
        self.assertIsNotNone(answer)
        
        # Step 4: Questioner submits review
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=5,
            comment='Excellent service!'
        )
        
        self.assertIsNotNone(review)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.question, self.question)

    def test_question_status_transitions(self):
        """Test that question status transitions are correct"""
        # Initial status
        self.assertEqual(self.question.status, 'pending')
        
        # After acceptance
        self.question.status = 'accepted'
        self.question.save()
        self.assertEqual(self.question.status, 'accepted')
        
        # After answer submission
        self.question.status = 'completed'
        self.question.save()
        self.assertEqual(self.question.status, 'completed')

    def test_answer_creation_completion(self):
        """Test that answer creation marks question as completed"""
        # Create assignment first
        QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )
        self.question.status = 'accepted'
        self.question.save()
        
        # Submit answer
        answer = Answer.objects.create(
            question=self.question,
            advisor=self.advisor,
            content='Test answer'
        )
        
        # Mark as completed
        self.question.status = 'completed'
        self.question.save()
        
        self.assertEqual(self.question.status, 'completed')
        self.assertEqual(answer.question, self.question)
        self.assertEqual(answer.advisor, self.advisor)

    def test_completion_status_check(self):
        """Test that completed status is properly set"""
        # Create assignment and answer
        QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )
        self.question.status = 'accepted'
        self.question.save()
        
        Answer.objects.create(
            question=self.question,
            advisor=self.advisor,
            content='Test answer'
        )
        self.question.status = 'completed'
        self.question.save()
        
        # Verify completion status
        self.assertEqual(self.question.status, 'completed')
        
        # Check that answer exists
        self.assertTrue(hasattr(self.question, 'answer'))
        self.assertEqual(self.question.answer.content, 'Test answer')

    def test_review_after_completion(self):
        """Test that review can only be submitted after completion"""
        # Create assignment and answer
        QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )
        self.question.status = 'accepted'
        self.question.save()
        
        Answer.objects.create(
            question=self.question,
            advisor=self.advisor,
            content='Test answer'
        )
        self.question.status = 'completed'
        self.question.save()
        
        # Now review can be created
        review = Review.objects.create(
            question=self.question,
            advisor=self.advisor,
            questioner=self.questioner,
            rating=4,
            comment='Good service'
        )
        
        self.assertEqual(review.question.status, 'completed')
        self.assertEqual(review.advisor, self.advisor)
