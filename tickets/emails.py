import logging
from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def send_comment_notification(comment, ticket):
    """Send an email notification when a public comment is added to a ticket.

    Rules:
    - Internal comments never trigger notifications.
    - If the commenter is the ticket creator, notify the assigned employee.
    - Otherwise, notify the ticket creator.
    """
    if comment.is_internal:
        return

    if comment.author == ticket.created_by:
        # Creator commented — notify assigned employee
        recipient = ticket.assigned_to
    else:
        # Employee (or anyone else) commented — notify creator
        recipient = ticket.created_by

    if not recipient or not recipient.email:
        return

    subject = f'[TicketDesk] New comment on: {ticket.title}'
    body = (
        f'A new comment has been added to ticket "{ticket.title}".\n\n'
        f'Comment by {comment.author.username}:\n'
        f'{comment.body}\n\n'
        f'View the ticket: /tickets/{ticket.pk}/'
    )

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(
            'Failed to send comment notification for ticket "%s" (pk=%s)',
            ticket.title,
            ticket.pk,
        )
