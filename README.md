# Shortify Link MVP

URL shortening service with comprehensive click tracking for marketing teams and SMM managers.

## Features

- Create short links from long URLs
- Track click analytics (UTM parameters, user agents, referrers, IP addresses)
- Interactive dashboard with filtering
- Mobile-responsive design
- 500-5,000 clicks/day capacity with <200ms redirect latency

## Tech Stack

- **Backend**: Django 5.x, Python 3.11+
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Tailwind CSS, Alpine.js
- **Admin**: Unfold Admin
- **Testing**: pytest, coverage ≥80%

## Setup

```bash
# Install dependencies
uv sync

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

## Testing

```bash
# Run all tests with coverage
pytest tests/ --cov

# Run specific test suite
pytest tests/contract/
pytest tests/integration/
```

## Architecture

- **links/**: Main application (models, views, services)
- **core/**: Shared infrastructure (base classes, mixins)
- **tests/**: Contract, integration, and unit tests

## Documentation

See `/specs/001-shortify-link-mvp/` for complete specification and implementation plan.
