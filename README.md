# BOMA - Tanzania Rental Marketplace

A Tanzania-focused short-stay and mid-stay rental marketplace connecting guests with verified properties and hosts.

## Project Overview

BOMA is a mobile-first platform that enables guests to search and book verified apartments or rooms, while hosts can list and manage their properties. The platform handles identity verification, bookings, payments (via local gateways like AzamPay and Selcom), deposits, disputes, reviews, and more.

## Architecture (Simplified for Solo Development)

- **Mobile App**: Expo/React Native with TypeScript (iOS & Android)
- **Backend API**: FastAPI (Python) monolith architecture
- **Database**: PostgreSQL (local via Docker Compose)
- **Authentication**: JWT-based email/password (self-hosted, no external services)
- **Media Storage**: Local file system with Nginx serving
- **Payment Gateways**: AzamPay (Tanzania mobile money & cards)
- **Hosting**: Single VPS with Nginx for static files and reverse proxy

**No external dependencies**: Clerk, Cloudinary, Neon, Redis, Celery, Twilio, SendGrid removed for simplicity and cost savings!

## Project Structure

```
boma/
├── backend/              # FastAPI backend application
│   ├── app/
│   │   ├── api/         # API routes and endpoints
│   │   ├── core/        # Core configuration and utilities
│   │   ├── models/      # SQLAlchemy database models
│   │   ├── schemas/     # Pydantic schemas for validation
│   │   ├── services/    # Business logic services
│   │   ├── db/          # Database connection and session management
│   │   ├── tasks/       # Background tasks (Celery)
│   │   └── utils/       # Utility functions
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   └── requirements.txt # Python dependencies
│
├── mobile/              # Expo/React Native mobile app
│   ├── src/
│   │   ├── components/  # React components (atomic design)
│   │   │   ├── atoms/
│   │   │   ├── molecules/
│   │   │   └── organisms/
│   │   ├── screens/     # Screen components
│   │   │   ├── auth/
│   │   │   ├── guest/
│   │   │   ├── host/
│   │   │   └── common/
│   │   ├── services/    # API client and external services
│   │   ├── navigation/  # React Navigation setup
│   │   ├── store/       # State management (Zustand)
│   │   ├── types/       # TypeScript type definitions
│   │   ├── hooks/       # Custom React hooks
│   │   ├── utils/       # Utility functions
│   │   ├── constants/   # Constants and configuration
│   │   └── assets/      # Images, fonts, icons
│   └── package.json     # Node dependencies
│
├── CLAUDE.md            # Complete project specification
├── project_log.md       # Development log and decisions
├── docker-compose.yml   # Local development environment
└── README.md            # This file
```

## Getting Started

### Prerequisites

- **Backend**:
  - Python 3.11+
  - Docker & Docker Compose (for PostgreSQL)

- **Mobile**:
  - Node.js 18+
  - Expo CLI
  - iOS Simulator (macOS) or Android Emulator

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start local database** (using Docker Compose):
   ```bash
   cd ..  # Back to project root
   docker-compose up -d postgres
   ```

6. **Run database migrations**:
   ```bash
   cd backend
   alembic upgrade head
   ```

7. **Start the development server**:
   ```bash
   python -m app.main
   # Or use uvicorn directly:
   uvicorn app.main:app --reload
   ```

   The API will be available at `http://localhost:8000`
   API docs at `http://localhost:8000/docs`

### Mobile App Setup

1. **Navigate to mobile directory**:
   ```bash
   cd mobile
   ```

2. **Install dependencies**:
   ```bash
   npm install --legacy-peer-deps
   ```

3. **Set up environment variables**:
   ```bash
   # Create a .env file
   echo "EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1" > .env
   ```

4. **Start the development server**:
   ```bash
   npm start
   ```

5. **Run on a platform**:
   - iOS: Press `i` in the terminal or run `npm run ios`
   - Android: Press `a` in the terminal or run `npm run android`
   - Web: Press `w` in the terminal or run `npm run web`

## Development Workflow

### Phase 0: Foundation (Current)
- [x] Initialize project structure
- [x] Set up backend with FastAPI
- [x] Set up mobile app with Expo
- [x] Configure development environment
- [x] Create Docker Compose for local services

### Phase 1: Database Schema
- [ ] Design complete database schema
- [ ] Create Alembic migrations
- [ ] Implement SQLAlchemy models

### Phase 2: Authentication & Users
- [ ] Integrate Clerk authentication
- [ ] Build user management system
- [ ] Implement guest/host profiles

### Phase 3-13: See CLAUDE.md for complete roadmap

## Available Scripts

### Backend
```bash
# Run development server
uvicorn app.main:app --reload

# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
pytest

# Code formatting
black app/
isort app/

# Type checking
mypy app/
```

### Mobile
```bash
# Start Expo development server
npm start

# Run on specific platform
npm run ios
npm run android
npm run web

# Type checking
npx tsc --noEmit

# Linting
npx expo lint
```

## Environment Configuration

### Backend (.env)
See `backend/.env.example` for all required environment variables including:
- Local PostgreSQL database connection
- Local file storage configuration
- Payment gateway credentials (AzamPay)
- JWT secret key
- Optional: SMTP for emails

### Mobile (.env)
```
EXPO_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Database Migrations

```bash
# Create a new migration after model changes
alembic revision --autogenerate -m "Add bookings table"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Testing

### Backend Tests
```bash
cd backend
pytest tests/
pytest tests/unit/
pytest tests/integration/
pytest --cov=app tests/  # With coverage
```

### Mobile Tests
```bash
cd mobile
# To be set up with Jest/React Native Testing Library
```

## Documentation

- **CLAUDE.md**: Complete project specification, architecture, and implementation guide
- **project_log.md**: Development log documenting decisions, changes, and progress
- **API Documentation**: Available at `/docs` when running the backend in development mode

## Target Market

- **Primary**: Tanzania
- **Currency**: TZS (Tanzanian Shilling)
- **Payment Methods**: Mobile money (M-Pesa, Tigo Pesa, Airtel Money, Halopesa) via AzamPay and Selcom
- **Network Considerations**: App optimized for mid-range smartphones and unstable network conditions

## Key Features

### For Guests
- Search and filter properties by location, dates, price, amenities
- View verified property photos and details
- Book properties with secure payments
- Mobile money and card payment support
- Track bookings and payment status
- Leave reviews and ratings
- 24/7 support access

### For Hosts
- List and manage properties
- Upload property photos
- Set pricing and availability rules
- Receive bookings and manage calendar
- Automated payouts to mobile money
- KYC verification process
- Access to earnings dashboard

### Platform
- Identity and KYC verification
- Payment processing and split payouts
- Deposit and damage dispute handling
- Cancellation and refund management
- Review and reputation system
- Automated notifications (SMS, email, push)
- Admin panel for operations

## Contributing

This is a private project. See `CLAUDE.md` for development guidelines and architecture patterns.

## License

Proprietary - All rights reserved

## Support

For development questions, refer to:
- CLAUDE.md for architecture and implementation details
- project_log.md for development history and decisions
- API documentation at `/docs` endpoint

---

Built with ❤️ for visitors
