from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
import json
from .models import Conversation, Message
from question.models import Question, Category
from advisor.models import AdvisorProfile
from review.models import Review

User = get_user_model()


class ChatModelTestCase(TestCase):
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
            status='accepted'
        )
        
        # Create conversation
        self.conversation = Conversation.objects.create(
            question=self.question
        )

    def test_conversation_creation(self):
        """Test basic conversation creation"""
        self.assertEqual(self.conversation.question, self.question)
        self.assertEqual(str(self.conversation), f"Conversation - {self.question.title}")

    def test_message_creation(self):
        """Test basic message creation"""
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.questioner,
            content='Test message'
        )
        
        self.assertEqual(message.conversation, self.conversation)
        self.assertEqual(message.sender, self.questioner)
        self.assertEqual(message.content, 'Test message')
        self.assertFalse(message.is_read)

    def test_message_ordering(self):
        """Test that messages are ordered by creation time"""
        message1 = Message.objects.create(
            conversation=self.conversation,
            sender=self.questioner,
            content='First message'
        )
        
        message2 = Message.objects.create(
            conversation=self.conversation,
            sender=self.advisor_user,
            content='Second message'
        )
        
        messages = list(self.conversation.messages.all())
        self.assertEqual(messages[0], message1)
        self.assertEqual(messages[1], message2)

    def test_unread_messages(self):
        """Test filtering unread messages"""
        Message.objects.create(
            conversation=self.conversation,
            sender=self.questioner,
            content='Unread message',
            is_read=False
        )
        
        Message.objects.create(
            conversation=self.conversation,
            sender=self.advisor_user,
            content='Read message',
            is_read=True
        )
        
        unread_count = self.conversation.messages.filter(is_read=False).count()
        self.assertEqual(unread_count, 1)


class ChatViewTestCase(TestCase):
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
        
        # Create question and conversation
        self.question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='Test question',
            description='Test description',
            status='accepted'
        )
        
        self.conversation = Conversation.objects.create(
            question=self.question
        )

    def test_conversation_list_questioner(self):
        """Test conversation list for questioner"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('conversation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['conversations']), 1)

    def test_conversation_list_advisor(self):
        """Test conversation list for advisor"""
        from question.models import QuestionAssignment
        
        # Create assignment
        QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )
        
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('conversation_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['conversations']), 1)

    def test_conversation_detail_questioner(self):
        """Test conversation detail for questioner"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('conversation_detail', args=[self.question.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['conversation'], self.conversation)

    def test_conversation_detail_advisor(self):
        """Test conversation detail for advisor"""
        from question.models import QuestionAssignment
        
        # Create assignment
        QuestionAssignment.objects.create(
            question=self.question,
            advisor=self.advisor,
            status='accepted'
        )
        
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('conversation_detail', args=[self.question.id]))
        self.assertEqual(response.status_code, 200)

    def test_conversation_access_control_questioner(self):
        """Test that questioner can only access their own conversations"""
        other_user = User.objects.create_user(
            username='other_questioner',
            email='other@test.com',
            password='testpass123',
            role='questioner'
        )
        
        other_question = Question.objects.create(
            questioner=other_user,
            category=self.category,
            title='Other question',
            description='Other description'
        )
        
        other_conversation = Conversation.objects.create(question=other_question)
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('conversation_detail', args=[other_question.id]))
        self.assertEqual(response.status_code, 403)

    def test_conversation_access_control_advisor(self):
        """Test that advisor can only access assigned conversations"""
        self.client.login(username='advisor', password='testpass123')
        
        response = self.client.get(reverse('conversation_detail', args=[self.question.id]))
        self.assertEqual(response.status_code, 403)  # No assignment yet

    def test_send_message(self):
        """Test sending a message"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(
            reverse('conversation_detail', args=[self.question.id]),
            {'content': 'Test message'}
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        message = Message.objects.filter(conversation=self.conversation).first()
        self.assertEqual(message.content, 'Test message')
        self.assertEqual(message.sender, self.questioner)

    def test_closed_chat(self):
        """Test that closed chat doesn't allow new messages"""
        self.question.status = 'completed'
        self.question.save()
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(reverse('conversation_detail', args=[self.question.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['chat_closed'])

    def test_mark_messages_as_read(self):
        """Test that viewing conversation marks messages as read"""
        # Create unread message from advisor
        Message.objects.create(
            conversation=self.conversation,
            sender=self.advisor_user,
            content='Unread message',
            is_read=False
        )
        
        self.client.login(username='questioner', password='testpass123')
        
        self.client.get(reverse('conversation_detail', args=[self.question.id]))
        
        message = Message.objects.get(conversation=self.conversation, sender=self.advisor_user)
        self.assertTrue(message.is_read)


class ChatAjaxTestCase(TestCase):
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
        
        # Create question and conversation
        self.question = Question.objects.create(
            questioner=self.questioner,
            category=self.category,
            title='Test question',
            description='Test description',
            status='accepted'
        )
        
        self.conversation = Conversation.objects.create(
            question=self.question
        )

    def test_send_message_ajax(self):
        """Test sending message via AJAX"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(
            reverse('send_message_ajax', args=[self.question.id]),
            data=json.dumps({'content': 'AJAX test message'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['message']['content'], 'AJAX test message')
        self.assertEqual(data['message']['sender'], 'questioner')

    def test_send_empty_message_ajax(self):
        """Test that empty messages are rejected"""
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(
            reverse('send_message_ajax', args=[self.question.id]),
            data=json.dumps({'content': ''}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_send_message_ajax_closed_chat(self):
        """Test that messages can't be sent to closed chats"""
        self.question.status = 'completed'
        self.question.save()
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.post(
            reverse('send_message_ajax', args=[self.question.id]),
            data=json.dumps({'content': 'Test message'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.content)
        self.assertFalse(data['success'])

    def test_get_new_messages_ajax(self):
        """Test getting new messages via AJAX"""
        # Create initial message
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.advisor_user,
            content='Initial message'
        )
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(
            reverse('get_new_messages_ajax', args=[self.question.id]),
            {'last_message_id': 0}
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['messages']), 1)
        self.assertEqual(data['messages'][0]['content'], 'Initial message')

    def test_get_new_messages_no_new(self):
        """Test getting new messages when there are none"""
        # Create initial message
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.advisor_user,
            content='Initial message'
        )
        
        self.client.login(username='questioner', password='testpass123')
        
        response = self.client.get(
            reverse('get_new_messages_ajax', args=[self.question.id]),
            {'last_message_id': message.id}
        )
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(len(data['messages']), 0)

    def test_ajax_access_control(self):
        """Test AJAX access control"""
        other_user = User.objects.create_user(
            username='other',
            email='other@test.com',
            password='testpass123',
            role='questioner'
        )
        
        self.client.login(username='other', password='testpass123')
        
        response = self.client.post(
            reverse('send_message_ajax', args=[self.question.id]),
            data=json.dumps({'content': 'Test'}),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
