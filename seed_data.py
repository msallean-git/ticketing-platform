import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticketing_platform.settings')
django.setup()

from django.contrib.auth.models import User
from tickets.models import Profile, Ticket, Comment

# Clear existing data (optional)
print("Clearing existing data...")
Comment.objects.all().delete()
Ticket.objects.all().delete()
User.objects.all().delete()

# Create admin user (superuser + employee)
print("Creating admin user...")
admin = User.objects.create_superuser(
    username='admin',
    email='admin@ticketdesk.com',
    password='admin123'
)
admin.profile.role = 'employee'
admin.profile.save()

# Create employee user
print("Creating employee user...")
employee1 = User.objects.create_user(
    username='employee1',
    email='employee1@ticketdesk.com',
    password='employee123'
)
employee1.profile.role = 'employee'
employee1.profile.save()

# Create regular user
print("Creating regular user...")
user1 = User.objects.create_user(
    username='user1',
    email='user1@example.com',
    password='user1234'
)
user1.profile.role = 'user'
user1.profile.save()

# Create sample tickets
print("Creating sample tickets...")

ticket1 = Ticket.objects.create(
    title='Login page not loading',
    description='When I try to access the login page, I get a 404 error. This has been happening since yesterday.',
    status='open',
    priority='high',
    created_by=user1
)

ticket2 = Ticket.objects.create(
    title='Dashboard shows incorrect data',
    description='The dashboard displays wrong statistics. The total count is showing 0 even though I have multiple tickets.',
    status='in_progress',
    priority='medium',
    created_by=user1,
    assigned_to=employee1
)

ticket3 = Ticket.objects.create(
    title='Feature request: Email notifications',
    description='It would be great to receive email notifications when there are updates on my tickets.',
    status='open',
    priority='low',
    created_by=user1
)

ticket4 = Ticket.objects.create(
    title='Cannot upload attachments',
    description='The file upload button is not working. I tried uploading a screenshot but nothing happens.',
    status='resolved',
    priority='urgent',
    created_by=user1,
    assigned_to=admin
)

# Create comments
print("Creating comments...")

Comment.objects.create(
    ticket=ticket1,
    author=user1,
    body='I also noticed this happens on different browsers (Chrome and Firefox).'
)

Comment.objects.create(
    ticket=ticket2,
    author=employee1,
    body='I am looking into this issue. It seems to be a caching problem.'
)

Comment.objects.create(
    ticket=ticket2,
    author=user1,
    body='Thanks for the quick response! Please let me know if you need any additional information.'
)

Comment.objects.create(
    ticket=ticket4,
    author=admin,
    body='This has been fixed in the latest update. Please try again and let me know if the issue persists.'
)

Comment.objects.create(
    ticket=ticket4,
    author=user1,
    body='Confirmed working now. Thank you!'
)

print("\n" + "="*50)
print("Seed data created successfully!")
print("="*50)
print("\nTest accounts:")
print("-" * 50)
print("Admin (Employee + Superuser):")
print("  Username: admin")
print("  Password: admin123")
print("\nEmployee:")
print("  Username: employee1")
print("  Password: employee123")
print("\nRegular User:")
print("  Username: user1")
print("  Password: user1234")
print("="*50)
print(f"\nCreated {Ticket.objects.count()} tickets")
print(f"Created {Comment.objects.count()} comments")
print("="*50)
