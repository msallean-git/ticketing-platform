from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from .models import Profile, Ticket, Comment, Attachment
from .forms import RegistrationForm, TicketCreateForm, TicketUpdateForm, CommentForm
from .validators import validate_file_extension, validate_file_size


class ProfileModelTest(TestCase):
    """Test cases for the Profile model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_profile_created_on_user_creation(self):
        """Test that a Profile is automatically created when a User is created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)

    def test_profile_default_role(self):
        """Test that new profiles have 'user' as default role"""
        self.assertEqual(self.user.profile.role, 'user')

    def test_profile_is_employee_property(self):
        """Test the is_employee property"""
        self.assertFalse(self.user.profile.is_employee)

        self.user.profile.role = 'employee'
        self.user.profile.save()
        self.assertTrue(self.user.profile.is_employee)

    def test_profile_str_representation(self):
        """Test the string representation of Profile"""
        expected = f"{self.user.username} - Regular User"
        self.assertEqual(str(self.user.profile), expected)


class TicketModelTest(TestCase):
    """Test cases for the Ticket model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.employee.profile.role = 'employee'
        self.employee.profile.save()

    def test_ticket_creation(self):
        """Test creating a ticket"""
        ticket = Ticket.objects.create(
            title='Test Ticket',
            description='This is a test ticket',
            created_by=self.user,
            priority='medium'
        )
        self.assertEqual(ticket.title, 'Test Ticket')
        self.assertEqual(ticket.status, 'open')
        self.assertEqual(ticket.priority, 'medium')
        self.assertIsNone(ticket.assigned_to)

    def test_ticket_str_representation(self):
        """Test the string representation of Ticket"""
        ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Description',
            created_by=self.user
        )
        self.assertEqual(str(ticket), 'Test Ticket')

    def test_ticket_assignment(self):
        """Test assigning a ticket to an employee"""
        ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Description',
            created_by=self.user
        )
        ticket.assigned_to = self.employee
        ticket.save()
        self.assertEqual(ticket.assigned_to, self.employee)

    def test_ticket_status_choices(self):
        """Test all status choices are valid"""
        valid_statuses = ['open', 'in_progress', 'waiting_on_asker', 'resolved', 'closed']
        ticket = Ticket.objects.create(
            title='Test',
            description='Test',
            created_by=self.user
        )
        for status in valid_statuses:
            ticket.status = status
            ticket.save()
            self.assertEqual(ticket.status, status)

    def test_ticket_priority_choices(self):
        """Test all priority choices are valid"""
        valid_priorities = ['low', 'medium', 'high', 'urgent']
        ticket = Ticket.objects.create(
            title='Test',
            description='Test',
            created_by=self.user
        )
        for priority in valid_priorities:
            ticket.priority = priority
            ticket.save()
            self.assertEqual(ticket.priority, priority)


class CommentModelTest(TestCase):
    """Test cases for the Comment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Description',
            created_by=self.user
        )

    def test_comment_creation(self):
        """Test creating a comment"""
        comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.user,
            body='This is a test comment'
        )
        self.assertEqual(comment.body, 'This is a test comment')
        self.assertFalse(comment.is_internal)

    def test_internal_comment(self):
        """Test creating an internal comment"""
        comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.user,
            body='Internal note',
            is_internal=True
        )
        self.assertTrue(comment.is_internal)

    def test_comment_str_representation(self):
        """Test the string representation of Comment"""
        comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.user,
            body='Test'
        )
        expected = f"Comment by {self.user.username} on {self.ticket}"
        self.assertEqual(str(comment), expected)


class RegistrationViewTest(TestCase):
    """Test cases for user registration"""

    def setUp(self):
        self.client = Client()

    def test_registration_page_loads(self):
        """Test that the registration page loads successfully"""
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')

    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex_pass123',
            'password2': 'complex_pass123',
            'role': 'user'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(User.objects.filter(username='newuser').exists())

        # Check profile was created
        user = User.objects.get(username='newuser')
        self.assertTrue(hasattr(user, 'profile'))

    def test_registration_with_invalid_password(self):
        """Test registration with mismatched passwords"""
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex_pass123',
            'password2': 'different_pass',
            'role': 'user'
        })
        self.assertEqual(response.status_code, 200)  # Stays on page
        self.assertFalse(User.objects.filter(username='newuser').exists())


class DashboardViewTest(TestCase):
    """Test cases for the dashboard view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.employee.profile.role = 'employee'
        self.employee.profile.save()

    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication"""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_user_dashboard_shows_own_tickets(self):
        """Test that regular users only see their own tickets"""
        self.client.login(username='testuser', password='testpass123')

        # Create tickets
        Ticket.objects.create(
            title='My Ticket',
            description='Test',
            created_by=self.user
        )
        Ticket.objects.create(
            title='Other Ticket',
            description='Test',
            created_by=self.employee
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['stats']['total'], 1)

    def test_employee_dashboard_shows_all_tickets(self):
        """Test that employees see all tickets"""
        self.client.login(username='employee', password='testpass123')

        # Create tickets
        Ticket.objects.create(
            title='Ticket 1',
            description='Test',
            created_by=self.user
        )
        Ticket.objects.create(
            title='Ticket 2',
            description='Test',
            created_by=self.employee
        )

        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['is_employee'])
        self.assertEqual(response.context['stats']['total'], 2)


class TicketViewTest(TestCase):
    """Test cases for ticket views"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.employee.profile.role = 'employee'
        self.employee.profile.save()

    def test_ticket_creation(self):
        """Test creating a new ticket"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('ticket_create'), {
            'title': 'New Ticket',
            'description': 'Test description',
            'priority': 'high'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(Ticket.objects.filter(title='New Ticket').exists())

    def test_user_cannot_view_others_tickets(self):
        """Test that regular users can't view other users' tickets"""
        other_user = User.objects.create_user(
            username='otheruser',
            password='testpass123'
        )
        ticket = Ticket.objects.create(
            title='Private Ticket',
            description='Test',
            created_by=other_user
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ticket_detail', kwargs={'pk': ticket.id}))
        self.assertEqual(response.status_code, 302)  # Redirect

    def test_employee_can_view_all_tickets(self):
        """Test that employees can view any ticket"""
        ticket = Ticket.objects.create(
            title='User Ticket',
            description='Test',
            created_by=self.user
        )

        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('ticket_detail', kwargs={'pk': ticket.id}))
        self.assertEqual(response.status_code, 200)

    def test_waiting_on_asker_auto_transition(self):
        """Test automatic status change when ticket creator comments"""
        ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test',
            created_by=self.user,
            status='waiting_on_asker'
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('ticket_detail', kwargs={'pk': ticket.id}),
            {
                'add_comment': '',
                'body': 'My response'
            }
        )

        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'in_progress')

    def test_employee_assign_self(self):
        """Test employee self-assignment to ticket"""
        ticket = Ticket.objects.create(
            title='Unassigned Ticket',
            description='Test',
            created_by=self.user,
            status='open'
        )

        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('ticket_assign_self', kwargs={'pk': ticket.id}))

        ticket.refresh_from_db()
        self.assertEqual(ticket.assigned_to, self.employee)
        self.assertEqual(ticket.status, 'in_progress')


class TicketFilterTest(TestCase):
    """Test cases for ticket filtering"""

    def setUp(self):
        self.client = Client()
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.employee.profile.role = 'employee'
        self.employee.profile.save()

        # Create tickets with different statuses and priorities
        Ticket.objects.create(
            title='Open Low',
            description='Test',
            created_by=self.employee,
            status='open',
            priority='low'
        )
        Ticket.objects.create(
            title='In Progress High',
            description='Test',
            created_by=self.employee,
            status='in_progress',
            priority='high'
        )
        Ticket.objects.create(
            title='Resolved Medium',
            description='Test',
            created_by=self.employee,
            status='resolved',
            priority='medium'
        )

    def test_filter_by_status(self):
        """Test filtering tickets by status"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('ticket_list') + '?status=open')

        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].status, 'open')

    def test_filter_by_priority(self):
        """Test filtering tickets by priority"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('ticket_list') + '?priority=high')

        self.assertEqual(len(response.context['tickets']), 1)
        self.assertEqual(response.context['tickets'][0].priority, 'high')

    def test_filter_by_status_and_priority(self):
        """Test filtering by both status and priority"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('ticket_list') + '?status=in_progress&priority=high')

        self.assertEqual(len(response.context['tickets']), 1)


class CommentPermissionTest(TestCase):
    """Test cases for comment permissions"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.employee = User.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.employee.profile.role = 'employee'
        self.employee.profile.save()

        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Test',
            created_by=self.user
        )

    def test_user_cannot_create_internal_comments(self):
        """Test that regular users cannot create internal comments"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            reverse('ticket_detail', kwargs={'pk': self.ticket.id}),
            {
                'add_comment': '',
                'body': 'Test comment',
                'is_internal': True
            }
        )

        comment = Comment.objects.first()
        self.assertFalse(comment.is_internal)

    def test_employee_can_create_internal_comments(self):
        """Test that employees can create internal comments"""
        self.client.login(username='employee', password='testpass123')
        response = self.client.post(
            reverse('ticket_detail', kwargs={'pk': self.ticket.id}),
            {
                'add_comment': '',
                'body': 'Internal note',
                'is_internal': True
            }
        )

        comment = Comment.objects.first()
        self.assertTrue(comment.is_internal)

    def test_user_cannot_see_internal_comments(self):
        """Test that regular users don't see internal comments"""
        Comment.objects.create(
            ticket=self.ticket,
            author=self.employee,
            body='Internal',
            is_internal=True
        )
        Comment.objects.create(
            ticket=self.ticket,
            author=self.employee,
            body='Public',
            is_internal=False
        )

        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ticket_detail', kwargs={'pk': self.ticket.id}))

        self.assertEqual(len(response.context['comments']), 1)
        self.assertFalse(response.context['comments'][0].is_internal)


class FormTest(TestCase):
    """Test cases for forms"""

    def test_registration_form_valid(self):
        """Test valid registration form"""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'complex_pass123',
            'password2': 'complex_pass123',
            'role': 'user'
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_ticket_create_form_valid(self):
        """Test valid ticket creation form"""
        form_data = {
            'title': 'New Ticket',
            'description': 'Description',
            'priority': 'high'
        }
        form = TicketCreateForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_ticket_create_form_invalid(self):
        """Test invalid ticket creation form (missing required fields)"""
        form_data = {
            'title': 'New Ticket'
            # Missing description and priority
        }
        form = TicketCreateForm(data=form_data)
        self.assertFalse(form.is_valid())


class TemplateTagTest(TestCase):
    """Test cases for custom template tags"""

    def test_status_badge_filter(self):
        """Test status_badge template filter"""
        from .templatetags.ticket_extras import status_badge

        self.assertEqual(status_badge('open'), 'bg-primary')
        self.assertEqual(status_badge('in_progress'), 'bg-warning text-dark')
        self.assertEqual(status_badge('waiting_on_asker'), 'bg-dark')
        self.assertEqual(status_badge('resolved'), 'bg-success')
        self.assertEqual(status_badge('closed'), 'bg-secondary')
        self.assertEqual(status_badge('invalid'), 'bg-secondary')  # Default

    def test_priority_badge_filter(self):
        """Test priority_badge template filter"""
        from .templatetags.ticket_extras import priority_badge

        self.assertEqual(priority_badge('low'), 'bg-info')
        self.assertEqual(priority_badge('medium'), 'bg-primary')
        self.assertEqual(priority_badge('high'), 'bg-warning text-dark')
        self.assertEqual(priority_badge('urgent'), 'bg-danger')
        self.assertEqual(priority_badge('invalid'), 'bg-secondary')  # Default


class ValidatorTest(TestCase):
    """Test cases for file validators"""

    def test_validate_file_extension_allowed(self):
        """Test that allowed file extensions pass validation"""
        allowed_files = [
            SimpleUploadedFile("test.png", b"file_content"),
            SimpleUploadedFile("test.jpeg", b"file_content"),
            SimpleUploadedFile("test.jpg", b"file_content"),
            SimpleUploadedFile("test.pdf", b"file_content"),
            SimpleUploadedFile("test.docx", b"file_content"),
            SimpleUploadedFile("test.xlsx", b"file_content"),
            SimpleUploadedFile("test.csv", b"file_content"),
            SimpleUploadedFile("test.har", b"file_content"),
        ]
        for file in allowed_files:
            try:
                validate_file_extension(file)
            except ValidationError:
                self.fail(f"validate_file_extension raised ValidationError for {file.name}")

    def test_validate_file_extension_disallowed(self):
        """Test that disallowed file extensions raise ValidationError"""
        disallowed_files = [
            SimpleUploadedFile("test.exe", b"file_content"),
            SimpleUploadedFile("test.bat", b"file_content"),
            SimpleUploadedFile("test.sh", b"file_content"),
            SimpleUploadedFile("test.zip", b"file_content"),
        ]
        for file in disallowed_files:
            with self.assertRaises(ValidationError):
                validate_file_extension(file)

    def test_validate_file_size_within_limit(self):
        """Test that files within size limit pass validation"""
        small_file = SimpleUploadedFile("test.pdf", b"x" * (1024 * 1024))  # 1 MB
        try:
            validate_file_size(small_file)
        except ValidationError:
            self.fail("validate_file_size raised ValidationError for file within limit")

    def test_validate_file_size_exceeds_limit(self):
        """Test that files exceeding size limit raise ValidationError"""
        large_file = SimpleUploadedFile("test.pdf", b"x" * (6 * 1024 * 1024))  # 6 MB
        with self.assertRaises(ValidationError):
            validate_file_size(large_file)


class AttachmentModelTest(TestCase):
    """Test cases for the Attachment model"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Description',
            created_by=self.user
        )
        self.comment = Comment.objects.create(
            ticket=self.ticket,
            author=self.user,
            body='Test comment'
        )

    def test_attachment_creation_for_ticket(self):
        """Test creating an attachment for a ticket"""
        file = SimpleUploadedFile("test.pdf", b"file_content", content_type="application/pdf")
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=file,
            original_filename="test.pdf",
            file_size=file.size,
            uploaded_by=self.user
        )
        self.assertEqual(attachment.ticket, self.ticket)
        self.assertIsNone(attachment.comment)
        self.assertEqual(attachment.original_filename, "test.pdf")

    def test_attachment_creation_for_comment(self):
        """Test creating an attachment for a comment"""
        file = SimpleUploadedFile("image.png", b"file_content", content_type="image/png")
        attachment = Attachment.objects.create(
            comment=self.comment,
            file=file,
            original_filename="image.png",
            file_size=file.size,
            uploaded_by=self.user
        )
        self.assertEqual(attachment.comment, self.comment)
        self.assertIsNone(attachment.ticket)

    def test_attachment_file_extension_property(self):
        """Test the file_extension property"""
        file = SimpleUploadedFile("document.docx", b"content")
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=file,
            original_filename="document.docx",
            file_size=file.size,
            uploaded_by=self.user
        )
        self.assertEqual(attachment.file_extension, '.docx')

    def test_attachment_file_size_display_property(self):
        """Test the file_size_display property"""
        file = SimpleUploadedFile("test.pdf", b"x" * 1024)
        attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=file,
            original_filename="test.pdf",
            file_size=1024,
            uploaded_by=self.user
        )
        self.assertEqual(attachment.file_size_display, "1.0 KB")

    def test_attachment_is_image_property(self):
        """Test the is_image property"""
        image_file = SimpleUploadedFile("image.png", b"content")
        pdf_file = SimpleUploadedFile("doc.pdf", b"content")

        image_attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=image_file,
            original_filename="image.png",
            file_size=image_file.size,
            uploaded_by=self.user
        )
        pdf_attachment = Attachment.objects.create(
            ticket=self.ticket,
            file=pdf_file,
            original_filename="doc.pdf",
            file_size=pdf_file.size,
            uploaded_by=self.user
        )

        self.assertTrue(image_attachment.is_image)
        self.assertFalse(pdf_attachment.is_image)

    def test_attachment_icon_class_property(self):
        """Test the icon_class property for different file types"""
        test_cases = [
            ("image.png", "bi-file-image"),
            ("document.pdf", "bi-file-pdf"),
            ("report.docx", "bi-file-word"),
            ("data.xlsx", "bi-file-excel"),
            ("log.har", "bi-file-code"),
        ]

        for filename, expected_icon in test_cases:
            file = SimpleUploadedFile(filename, b"content")
            attachment = Attachment.objects.create(
                ticket=self.ticket,
                file=file,
                original_filename=filename,
                file_size=file.size,
                uploaded_by=self.user
            )
            self.assertEqual(attachment.icon_class, expected_icon)

    def test_attachment_cascade_delete_with_ticket(self):
        """Test that attachments are deleted when ticket is deleted"""
        file = SimpleUploadedFile("test.pdf", b"content")
        Attachment.objects.create(
            ticket=self.ticket,
            file=file,
            original_filename="test.pdf",
            file_size=file.size,
            uploaded_by=self.user
        )
        self.assertEqual(Attachment.objects.count(), 1)

        self.ticket.delete()
        self.assertEqual(Attachment.objects.count(), 0)

    def test_attachment_cascade_delete_with_comment(self):
        """Test that attachments are deleted when comment is deleted"""
        file = SimpleUploadedFile("test.pdf", b"content")
        Attachment.objects.create(
            comment=self.comment,
            file=file,
            original_filename="test.pdf",
            file_size=file.size,
            uploaded_by=self.user
        )
        self.assertEqual(Attachment.objects.count(), 1)

        self.comment.delete()
        self.assertEqual(Attachment.objects.count(), 0)


class TicketCreateAttachmentTest(TestCase):
    """Test cases for ticket creation with attachments"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_create_ticket_with_attachments(self):
        """Test creating a ticket with file attachments"""
        file1 = SimpleUploadedFile("test1.pdf", b"pdf_content", content_type="application/pdf")
        file2 = SimpleUploadedFile("test2.png", b"png_content", content_type="image/png")

        response = self.client.post(reverse('ticket_create'), {
            'title': 'Ticket with Attachments',
            'description': 'Test description',
            'priority': 'high',
            'attachments': [file1, file2]
        })

        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title='Ticket with Attachments')
        self.assertEqual(ticket.attachments.count(), 2)

    def test_create_ticket_without_attachments(self):
        """Test creating a ticket without attachments"""
        response = self.client.post(reverse('ticket_create'), {
            'title': 'Ticket without Attachments',
            'description': 'Test description',
            'priority': 'medium'
        })

        self.assertEqual(response.status_code, 302)
        ticket = Ticket.objects.get(title='Ticket without Attachments')
        self.assertEqual(ticket.attachments.count(), 0)


class CommentAttachmentTest(TestCase):
    """Test cases for comment attachments"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.ticket = Ticket.objects.create(
            title='Test Ticket',
            description='Description',
            created_by=self.user
        )
        self.client.login(username='testuser', password='testpass123')

    def test_add_comment_with_attachments(self):
        """Test adding a comment with file attachments"""
        file = SimpleUploadedFile("attachment.pdf", b"content", content_type="application/pdf")

        response = self.client.post(
            reverse('ticket_detail', kwargs={'pk': self.ticket.id}),
            {
                'add_comment': '',
                'body': 'Comment with attachment',
                'attachments': [file]
            }
        )

        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.attachments.count(), 1)
        self.assertEqual(comment.attachments.first().original_filename, "attachment.pdf")

    def test_add_comment_without_attachments(self):
        """Test adding a comment without attachments"""
        response = self.client.post(
            reverse('ticket_detail', kwargs={'pk': self.ticket.id}),
            {
                'add_comment': '',
                'body': 'Comment without attachment'
            }
        )

        self.assertEqual(response.status_code, 302)
        comment = Comment.objects.first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.attachments.count(), 0)
