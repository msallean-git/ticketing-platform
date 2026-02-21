from django import template

register = template.Library()


@register.filter
def status_badge(status):
    badge_classes = {
        'open': 'bg-primary',
        'in_progress': 'bg-warning text-dark',
        'waiting_on_asker': 'bg-dark',
        'resolved': 'bg-success',
        'closed': 'bg-secondary',
    }
    return badge_classes.get(status, 'bg-secondary')


@register.filter
def priority_badge(priority):
    badge_classes = {
        'low': 'bg-info',
        'medium': 'bg-primary',
        'high': 'bg-warning text-dark',
        'urgent': 'bg-danger',
    }
    return badge_classes.get(priority, 'bg-secondary')
