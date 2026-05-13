# Agropulse

Agropulse is an AI-powered agricultural commerce platform for farmers, buyers, riders, and operations teams. The project is built with Django and Django REST Framework and currently covers user management, produce management, orders, delivery, payments, and recurring subscriptions.

## Features

- JWT-authenticated REST API
- Role-based access control for buyers, farmers, and transporters
- Produce catalog and order management
- Delivery tracking
- Squad payment gateway integration for payment initiation, verification, escrow, payout, and virtual accounts
- Subscription support for recurring produce orders
- Django admin interfaces for core business entities
- Filtering, search, and ordering on API endpoints

## Tech Stack

- Python 3.12+
- Django 6.0.5
- Django REST Framework
- PostgreSQL
- SimpleJWT
- django-filter
- django-cors-headers
- django-otp
- Squad payment gateway
- Celery and Redis are available in the dependency set for async work

## Requirements

- Python 3.12 or newer
- PostgreSQL
- Poetry
- A `.env` file or equivalent environment variables for Django, database, email, and Squad configuration


## Setup

1. Install dependencies:

```bash
poetry install
```

2. Create and configure your environment variables.

3. Run database migrations:

```bash
poetry run python -m core_agropulse.manage migrate
```

4. Create a superuser if needed:

```bash
poetry run python -m core_agropulse.manage createsuperuser
```

5. Start the development server:

```bash
poetry run python -m core_agropulse.manage runserver
```

## Running Tests

Run the full test suite:

```bash
poetry run python -m core_agropulse.manage test
```

Run a specific app test module:

```bash
poetry run python -m core_agropulse.manage test core_agropulse.payments.tests -v 2
poetry run python -m core_agropulse.manage test core_agropulse.subscriptions.tests -v 2
```

## Makefile Commands

The repository includes a small Makefile with these targets:

- `make run-server`
- `make lint`
- `make migrations`
- `make migrate`
- `make test`

## Notes

- The project uses PostgreSQL, so SQLite is not the intended runtime database.
- Payments are integrated through Squad and expect the Squad-related environment variables to be present.
- Subscriptions support recurring order lifecycles with pause, resume, and cancel actions.

## License

No license has been specified yet.
