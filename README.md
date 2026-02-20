# TicketDesk - Django Ticketing Platform

A simple and efficient ticketing platform built with Django 6.x and Bootstrap 5.

## Features

- **User Authentication**: Login, registration with role-based access control
- **Role-Based Access**:
  - Regular users can create and track their own tickets
  - Employees can view all tickets, assign themselves, and update ticket status/priority
- **Ticket Management**: Create, view, filter tickets by status and priority
- **Comments**: Add comments to tickets for communication
- **Responsive Design**: Bootstrap 5 with mobile-friendly interface
- **Admin Panel**: Django admin for managing users, tickets, and comments

## Tech Stack

- **Backend**: Django 6.0.2
- **Frontend**: Bootstrap 5 (CDN)
- **Database**: SQLite
- **Authentication**: Django's built-in auth system

## Installation

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run migrations**:
   ```bash
   py manage.py migrate
   ```

3. **Load seed data** (optional but recommended):
   ```bash
   py seed_data.py
   ```

4. **Start the development server**:
   ```bash
   py manage.py runserver
   ```

5. **Access the application**:
   Open your browser and navigate to `http://127.0.0.1:8000/`

## Test Accounts

After running the seed data script, you can use these accounts:

### Admin (Employee + Superuser)
- Username: `admin`
- Password: `admin123`

### Employee
- Username: `employee1`
- Password: `employee123`

### Regular User
- Username: `user1`
- Password: `user1234`

## Project Structure

```
ticketing_platform/
├── manage.py
├── requirements.txt
├── seed_data.py
├── README.md
├── db.sqlite3
├── ticketing_platform/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── tickets/                     # Main app
    ├── models.py                # Profile, Ticket, Comment
    ├── views.py                 # Function-based views
    ├── forms.py                 # Registration, Ticket, Comment forms
    ├── urls.py                  # URL routing
    ├── admin.py                 # Admin configuration
    ├── decorators.py            # @employee_required, @regular_user_required
    ├── templatetags/
    │   └── ticket_extras.py     # Custom template filters
    ├── templates/
    │   ├── base.html
    │   ├── home.html
    │   ├── registration/
    │   │   ├── login.html
    │   │   └── register.html
    │   └── tickets/
    │       ├── dashboard.html
    │       ├── ticket_list.html
    │       ├── ticket_create.html
    │       └── ticket_detail.html
    └── static/tickets/css/
        └── style.css
```

## Key Features by Role

### Regular Users
- Create tickets with title, description, and priority
- View their own tickets
- Filter tickets by status and priority
- Add comments to tickets
- View dashboard with ticket statistics

### Employees
- View all tickets in the system
- Assign tickets to themselves
- Update ticket status (Open, In Progress, Resolved, Closed)
- Update ticket priority (Low, Medium, High, Urgent)
- Reassign tickets to other employees
- Add comments to any ticket
- View unassigned tickets on dashboard
- Access Django admin panel (if superuser)

## URLs

- `/` - Home page
- `/login/` - Login page
- `/register/` - Registration page
- `/dashboard/` - User dashboard (role-aware)
- `/tickets/` - Ticket list (filterable)
- `/tickets/create/` - Create new ticket
- `/tickets/<id>/` - Ticket detail page
- `/admin/` - Django admin panel

## Models

### Profile
- OneToOneField to User
- Role field (user/employee)
- Auto-created on user registration via signals

### Ticket
- Title, description
- Status: Open, In Progress, Resolved, Closed
- Priority: Low, Medium, High, Urgent
- Created by (User)
- Assigned to (User, optional)
- Timestamps

### Comment
- ForeignKey to Ticket
- Author (User)
- Body text
- Timestamp

## Development

To create a new admin user manually:
```bash
py manage.py createsuperuser
```

To reset the database:
```bash
# Delete db.sqlite3
del db.sqlite3
py manage.py migrate
py seed_data.py
```

## License

This project is for educational purposes.
