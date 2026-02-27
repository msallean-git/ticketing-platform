import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ticketing_platform.settings')
django.setup()

from django.contrib.auth.models import User
from tickets.models import Profile, Ticket, Comment

# Clear existing data
print("Clearing existing data...")
Comment.objects.all().delete()
Ticket.objects.all().delete()
User.objects.all().delete()

# ── Users ──────────────────────────────────────────────────────────────────

print("Creating users...")

admin = User.objects.create_superuser(
    username='admin',
    email='admin@ticketdesk.com',
    password='admin123'
)
admin.profile.role = 'employee'
admin.profile.save()

employee1 = User.objects.create_user(
    username='employee1',
    email='employee1@ticketdesk.com',
    password='employee123'
)
employee1.profile.role = 'employee'
employee1.profile.save()

employee2 = User.objects.create_user(
    username='employee2',
    email='employee2@ticketdesk.com',
    password='employee123'
)
employee2.profile.role = 'employee'
employee2.profile.save()

user1 = User.objects.create_user(
    username='user1',
    email='user1@example.com',
    password='user1234'
)

user2 = User.objects.create_user(
    username='user2',
    email='user2@example.com',
    password='user1234'
)

user3 = User.objects.create_user(
    username='user3',
    email='user3@example.com',
    password='user1234'
)

# ── Tickets ────────────────────────────────────────────────────────────────

print("Creating tickets...")

tickets_data = [
    # user1 tickets
    ('Login page not loading',                  'Getting a 404 error when accessing the login page. Happens on Chrome and Firefox.',                          'open',             'high',   user1, None),
    ('Dashboard shows incorrect stats',         'Total ticket count shows 0 even though I have multiple tickets open.',                                        'in_progress',      'medium', user1, employee1),
    ('Feature request: email notifications',    'Would love to get email alerts when my ticket status changes.',                                               'open',             'low',    user1, None),
    ('Cannot upload attachments',               'The file upload button does nothing when clicked.',                                                           'resolved',         'urgent', user1, admin),
    ('Password reset email not arriving',       'Requested a password reset 30 minutes ago and still no email.',                                              'open',             'high',   user1, None),
    ('Profile page throws 500 error',           'Navigating to /profile/ causes an internal server error.',                                                   'in_progress',      'urgent', user1, employee2),
    ('Search returns no results',               'Searching for any keyword returns an empty result set.',                                                     'waiting_on_asker', 'medium', user1, employee1),
    ('Ticket creation form resets on error',    'When I submit an invalid form, all my typed data is cleared.',                                               'open',             'low',    user1, None),
    ('Dark mode request',                       'Please add a dark mode option to reduce eye strain.',                                                        'closed',           'low',    user1, None),
    ('Export to CSV not working',               'Clicking export produces an empty file.',                                                                    'in_progress',      'medium', user1, employee1),
    ('Session expires too quickly',             'I get logged out after just a few minutes of inactivity.',                                                   'open',             'medium', user1, None),
    ('Broken link in footer',                   'The "Terms of Service" link in the footer leads to a 404.',                                                  'resolved',         'low',    user1, employee2),

    # user2 tickets
    ('Cannot assign ticket to colleague',       'The assigned_to dropdown only shows my own name.',                                                           'open',             'high',   user2, None),
    ('Notification badge not clearing',         'The notification count stays at 3 even after reading all notifications.',                                    'in_progress',      'medium', user2, employee1),
    ('Ticket priority not saving',              'Changing priority from Medium to Urgent and saving reverts back to Medium.',                                 'open',             'urgent', user2, None),
    ('Comment timestamp shows wrong timezone',  'All comment times are off by 5 hours.',                                                                     'waiting_on_asker', 'low',    user2, employee2),
    ('Bulk close not working',                  'Selecting multiple tickets and choosing bulk close does nothing.',                                            'open',             'medium', user2, None),
    ('Attachment preview broken',               'Image attachments show a broken icon instead of a preview.',                                                 'in_progress',      'medium', user2, admin),
    ('Duplicate ticket created on refresh',     'Refreshing the page after submitting a ticket creates a duplicate.',                                         'resolved',         'high',   user2, employee1),
    ('Filter state lost on back navigation',    'Going back from ticket detail clears my active filters.',                                                    'open',             'low',    user2, None),
    ('Rich text editor request',                'Plain text descriptions are hard to format. Please add markdown or a rich text editor.',                     'open',             'low',    user2, None),
    ('Internal comments visible to users',      'I can see comments marked as internal even though I am a regular user.',                                     'open',             'urgent', user2, None),
    ('API rate limit errors',                   'Getting 429 errors intermittently when loading the ticket list.',                                            'in_progress',      'high',   user2, employee2),
    ('Mobile layout broken on iOS',             'The ticket list table overflows horizontally on iPhone.',                                                    'open',             'medium', user2, None),

    # user3 tickets
    ('Account deletion request',               'Please provide a way to delete my account and all associated data.',                                         'open',             'medium', user3, None),
    ('Two-factor authentication request',       'Would like to enable 2FA for my account.',                                                                   'open',             'low',    user3, None),
    ('Ticket detail page very slow',            'Loading a ticket with many comments takes over 10 seconds.',                                                 'in_progress',      'high',   user3, employee1),
    ('Wrong email in welcome message',          'The welcome email after registration shows a different users email.',                                        'resolved',         'urgent', user3, admin),
    ('Cannot reopen closed ticket',             'Once a ticket is closed there is no way to reopen it.',                                                     'open',             'medium', user3, None),
    ('Sort order resets on filter',             'Applying a filter resets the sort order back to default.',                                                   'open',             'low',    user3, None),
    ('Pagination skips page 3',                 'When navigating pages, clicking page 3 jumps to page 5.',                                                   'open',             'high',   user3, None),
    ('Comment edit not available',              'I cannot edit a comment after posting it.',                                                                  'open',             'low',    user3, None),
    ('File size limit unclear',                 'The upload form does not show the maximum allowed file size.',                                               'resolved',         'low',    user3, employee2),
    ('Ticket status history missing',           'There is no way to see when a ticket status was changed or by whom.',                                       'open',             'medium', user3, None),
    ('Search does not include comments',        'Searching for a keyword only checks the title, not the comment body.',                                       'in_progress',      'medium', user3, employee1),
    ('Employee cannot unassign ticket',         'Once a ticket is assigned there is no option to unassign it.',                                              'open',             'medium', user3, None),
    ('Date filter request',                     'Please add a date range filter to the ticket list.',                                                        'open',             'low',    user3, None),
    ('Keyboard navigation broken',              'Tabbing through the ticket creation form skips the priority field.',                                         'open',             'low',    user3, None),
    ('Long titles overflow table',              'Ticket titles longer than ~60 characters break the table layout.',                                          'resolved',         'low',    user3, employee2),
    ('Urgent tickets not highlighted',          'Urgent priority tickets look the same as high priority in the list.',                                        'open',             'medium', user3, None),
    ('Cannot filter by assignee',              'There is no way to filter tickets by who they are assigned to.',                                             'open',             'low',    user3, None),
    ('Dashboard stat cards not clickable',      'Clicking the Open stat card should filter the ticket list but does nothing.',                               'closed',           'medium', user3, None),
    ('Registration confirmation email missing', 'No confirmation email is sent after successful registration.',                                              'open',             'low',    user3, None),
    ('Logout redirect goes to 404',             'After logging out, the browser is redirected to a page that does not exist.',                              'resolved',         'high',   user3, admin),
    ('Employee list not loading in form',       'The assigned_to dropdown in the employee update form is empty.',                                            'in_progress',      'urgent', user3, employee1),
    ('Stale ticket count on dashboard',         'The dashboard stats do not update after creating a new ticket without a page refresh.',                     'open',             'medium', user3, None),
    ('Ticket ID not shown on detail page',      'The ticket detail page does not display the ticket ID anywhere.',                                           'open',             'low',    user3, None),
    ('Comment form missing on mobile',          'The add comment form does not appear on mobile screen sizes.',                                              'open',             'high',   user3, None),
]

created_tickets = []
for title, description, status, priority, created_by, assigned_to in tickets_data:
    t = Ticket.objects.create(
        title=title,
        description=description,
        status=status,
        priority=priority,
        created_by=created_by,
        assigned_to=assigned_to,
    )
    created_tickets.append(t)

# ── Comments ───────────────────────────────────────────────────────────────

print("Creating comments...")

comments_data = [
    # (ticket index, author, body, is_internal)
    (0,  user1,     'Happens on Edge too — definitely not browser-specific.', False),
    (0,  employee1, 'Looking into this now. Can you share your browser version?', False),
    (0,  employee1, 'Looks like a misconfigured URL pattern. Working on a fix.', True),

    (1,  employee1, 'Identified a caching issue. Deploying a fix shortly.', False),
    (1,  user1,     'Thanks! Let me know if you need anything else.', False),

    (3,  admin,     'Fixed in the latest release. Please try again.', False),
    (3,  user1,     'Confirmed working now. Thank you!', False),

    (6,  employee1, 'Can you clarify which search terms you used?', False),
    (6,  user1,     'Tried "login", "error", and "dashboard" — all returned empty.', False),

    (12, employee1, 'The dropdown is filtered to employees only by design. Could you describe your use case?', False),
    (12, user2,     'I need to reassign a ticket to my colleague who is also a regular user.', False),

    (17, admin,     'Fixed the image preview rendering bug.', False),
    (17, user2,     'Works perfectly now, thank you!', False),

    (18, employee1, 'Added a POST-redirect-GET fix to prevent duplicate submissions.', True),
    (18, user2,     'Great, no more duplicates!', False),

    (26, employee1, 'Investigating the slow load time. Likely an N+1 query issue.', True),
    (26, user3,     'Still slow today — took 12 seconds to load ticket #14.', False),
    (26, employee1, 'Deployed query optimisation. Please check if it is faster now.', False),

    (27, admin,     'Corrected the email template. Sorry for the confusion.', False),
    (27, user3,     'All good now, thanks!', False),

    (44, admin,     'Fixed the logout redirect to point to the home page.', False),
    (44, user3,     'Confirmed — logout now redirects correctly.', False),

    (45, employee1, 'The employee queryset was missing. Fixed and deployed.', True),
    (45, user3,     'The dropdown is now populated. Thank you!', False),
]

for ticket_idx, author, body, is_internal in comments_data:
    Comment.objects.create(
        ticket=created_tickets[ticket_idx],
        author=author,
        body=body,
        is_internal=is_internal,
    )

# ── Summary ────────────────────────────────────────────────────────────────

print("\n" + "=" * 50)
print("Seed data created successfully!")
print("=" * 50)
print("\nTest accounts:")
print("-" * 50)
print("Admin (Employee + Superuser):")
print("  Username: admin        Password: admin123")
print("\nEmployees:")
print("  Username: employee1    Password: employee123")
print("  Username: employee2    Password: employee123")
print("\nRegular Users:")
print("  Username: user1        Password: user1234")
print("  Username: user2        Password: user1234")
print("  Username: user3        Password: user1234")
print("=" * 50)
print(f"\nCreated {Ticket.objects.count()} tickets")
print(f"Created {Comment.objects.count()} comments")
print(f"Created {User.objects.count()} users")
print("=" * 50)
