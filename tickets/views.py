import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Q, Count
from .models import Ticket, Comment
from .forms import RegistrationForm, TicketCreateForm, TicketUpdateForm, CommentForm
from .decorators import employee_required

logger = logging.getLogger(__name__)


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            logger.info(f'New user registered: {user.username} (Role: {user.profile.get_role_display()})')
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def dashboard(request):
    user = request.user
    is_employee = user.profile.is_employee

    if is_employee:
        # Employee dashboard: all tickets + unassigned
        tickets = Ticket.objects.all()[:10]
        unassigned_tickets = Ticket.objects.filter(assigned_to__isnull=True)[:5]
        my_assigned = Ticket.objects.filter(assigned_to=user)[:5]

        stats = {
            'total': Ticket.objects.count(),
            'open': Ticket.objects.filter(status='open').count(),
            'in_progress': Ticket.objects.filter(status='in_progress').count(),
            'waiting_on_asker': Ticket.objects.filter(status='waiting_on_asker').count(),
            'resolved': Ticket.objects.filter(status='resolved').count(),
        }

        context = {
            'is_employee': True,
            'tickets': tickets,
            'unassigned_tickets': unassigned_tickets,
            'my_assigned': my_assigned,
            'stats': stats,
        }
    else:
        # Regular user dashboard: own tickets
        tickets = Ticket.objects.filter(created_by=user)

        stats = {
            'total': tickets.count(),
            'open': tickets.filter(status='open').count(),
            'in_progress': tickets.filter(status='in_progress').count(),
            'waiting_on_asker': tickets.filter(status='waiting_on_asker').count(),
            'resolved': tickets.filter(status='resolved').count(),
        }

        context = {
            'is_employee': False,
            'tickets': tickets,
            'stats': stats,
        }

    return render(request, 'tickets/dashboard.html', context)


@login_required
def ticket_list(request):
    user = request.user
    is_employee = user.profile.is_employee

    # Base queryset
    if is_employee:
        tickets = Ticket.objects.all()
    else:
        tickets = Ticket.objects.filter(created_by=user)

    # Filtering
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')

    if status_filter:
        tickets = tickets.filter(status=status_filter)
    if priority_filter:
        tickets = tickets.filter(priority=priority_filter)

    context = {
        'tickets': tickets,
        'is_employee': is_employee,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'status_choices': Ticket.STATUS_CHOICES,
        'priority_choices': Ticket.PRIORITY_CHOICES,
    }

    return render(request, 'tickets/ticket_list.html', context)


@login_required
def ticket_create(request):
    if request.method == 'POST':
        form = TicketCreateForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            logger.info(f'Ticket created: "{ticket.title}" by {request.user.username} (Priority: {ticket.get_priority_display()})')
            messages.success(request, f'Ticket "{ticket.title}" created successfully!')
            return redirect('ticket_detail', pk=ticket.id)
    else:
        form = TicketCreateForm()

    return render(request, 'tickets/ticket_create.html', {'form': form})


@login_required
def ticket_detail(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    user = request.user
    is_employee = user.profile.is_employee

    # Access control: users can only view their own tickets
    if not is_employee and ticket.created_by != user:
        messages.error(request, 'You can only view your own tickets.')
        return redirect('dashboard')

    # Handle forms
    if request.method == 'POST':
        if 'update_ticket' in request.POST and is_employee:
            update_form = TicketUpdateForm(request.POST, instance=ticket)
            if update_form.is_valid():
                old_status = ticket.status
                old_priority = ticket.priority
                old_assigned = ticket.assigned_to
                updated_ticket = update_form.save()
                ticket.refresh_from_db()
                logger.info(f'Ticket updated: "{ticket.title}" by {user.username} (Status: {old_status}->{ticket.status}, Priority: {old_priority}->{ticket.priority}, Assigned: {old_assigned}->{ticket.assigned_to})')
                messages.success(request, 'Ticket updated successfully!')
                return redirect('ticket_detail', pk=pk)
        elif 'add_comment' in request.POST:
            comment_form = CommentForm(request.POST, is_employee=is_employee)
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.ticket = ticket
                comment.author = user
                # Ensure only employees can create internal comments
                if not is_employee:
                    comment.is_internal = False
                comment.save()

                # Automatically change status from "Waiting on Asker" to "In Progress"
                # when the ticket creator adds a comment
                if user == ticket.created_by and ticket.status == 'waiting_on_asker':
                    old_status = ticket.status
                    ticket.status = 'in_progress'
                    ticket.save()
                    logger.info(f'Ticket "{ticket.title}" status automatically changed from {old_status} to {ticket.status} after comment by asker')

                comment_type = "internal" if comment.is_internal else "public"
                logger.info(f'{comment_type.capitalize()} comment added to ticket "{ticket.title}" by {user.username}')
                messages.success(request, 'Comment added successfully!')
                return redirect('ticket_detail', pk=pk)

    # Initialize forms for GET request
    update_form = TicketUpdateForm(instance=ticket) if is_employee else None
    comment_form = CommentForm(is_employee=is_employee)

    # Filter comments based on user role
    if is_employee:
        comments = ticket.comments.all()
    else:
        comments = ticket.comments.filter(is_internal=False)

    context = {
        'ticket': ticket,
        'is_employee': is_employee,
        'update_form': update_form,
        'comment_form': comment_form,
        'comments': comments,
    }

    return render(request, 'tickets/ticket_detail.html', context)


@employee_required
def ticket_assign_self(request, pk):
    ticket = get_object_or_404(Ticket, pk=pk)
    ticket.assigned_to = request.user
    if ticket.status == 'open':
        ticket.status = 'in_progress'
    ticket.save()
    logger.info(f'Ticket "{ticket.title}" assigned to {request.user.username}')
    messages.success(request, f'Ticket "{ticket.title}" assigned to you!')
    return redirect('ticket_detail', pk=pk)
