# BOMA Project Development Log

This file documents all development work, architectural decisions, code changes, and progress throughout the BOMA project lifecycle.

---

## Phase 0: Project Foundation & Setup

**Date**: November 14, 2025
**Status**: ✅ Completed
**Duration**: ~2 hours

### Overview
Established the complete foundational infrastructure for both backend (FastAPI) and mobile (Expo/React Native) applications. Created project structure, configuration files, development environment setup, and initialized version control.

---

### 1. Backend Infrastructure Setup

#### 1.1 Folder Structure Created
**What**: Created comprehensive backend folder organization following domain-driven design principles.

**Structure**:
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/      # Route handlers (future)
│   │   │   └── dependencies/   # Dependency injection
│   │   └── middleware/         # Custom middleware
│   ├── core/                   # Core configuration
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic validation schemas
│   ├── services/               # Business logic layer
│   ├── db/                     # Database connection/session
│   ├── tasks/                  # Celery background tasks
│   └── utils/                  # Utility functions
├── alembic/                    # Database migrations
│   └── versions/               # Migration files
└── tests/
    ├── unit/                   # Unit tests
    └── integration/            # Integration tests
```

**Why**: This structure separates concerns cleanly:
- **API layer**: HTTP interface and routing
- **Services layer**: Business logic isolated from HTTP
- **Models layer**: Database schema and ORM
- **Schemas layer**: Request/response validation
- This enables easy testing, maintenance, and future AI-assisted code generation

**Decision**: Monolith architecture over microservices for initial release to reduce complexity and operational overhead.

---

#### 1.2 Python Dependencies (requirements.txt)
**What**: Defined all Python packages needed for the backend.

**Key Dependencies**:
- **FastAPI 0.115.0**: Modern async web framework
- **SQLAlchemy 2.0.36**: ORM for database operations
- **Alembic 1.14.0**: Database migration tool
- **Pydantic 2.10.3**: Data validation using Python type hints
- **Celery 5.4.0**: Distributed task queue for background jobs
- **Redis 5.2.1**: Cache and message broker for Celery
- **Cloudinary 1.41.0**: Media storage service integration
- **PyJWT/python-jose**: JWT token verification for Clerk auth

**Why**:
- FastAPI chosen for async support, automatic OpenAPI docs, and type safety
- SQLAlchemy 2.0 for modern async ORM capabilities
- Celery+Redis for reliable background job processing (notifications, webhooks, reconciliation)

**Decision**: Use asyncpg for PostgreSQL async driver to maximize performance with FastAPI's async capabilities.

---

#### 1.3 Environment Configuration (.env.example)
**What**: Created comprehensive environment variable template covering all service integrations.

**Configuration Sections**:
1. **Application**: Basic app settings (name, version, debug mode)
2. **Database**: Neon Postgres connection with pool settings
3. **Authentication**: Clerk public keys and issuer URLs
4. **Redis**: Connection for caching and Celery
5. **Cloudinary**: Media storage credentials
6. **Payment Gateways**:
   - AzamPay (mobile money, cards)
   - Selcom (mobile money, cards)
7. **Notifications**: Twilio (SMS), SendGrid (email), Firebase (push)
8. **Business Rules**: Platform fee, booking expiry, deposit hold periods
9. **Security**: Secret keys, token expiration
10. **Regional**: Country, currency, timezone (TZ/TZS/Africa/Dar_es_Salaam)

**Why**: Centralized configuration management prevents hardcoded values and enables easy environment-specific deployments (dev, staging, production).

**Decision**: All secrets and API keys MUST be in environment variables, never committed to repository.

---

#### 1.4 Core Configuration Module (app/core/config.py)
**What**: Created Pydantic settings class that loads and validates environment variables.

**Features**:
- Type-safe configuration using Pydantic
- Automatic environment variable loading
- Validation of required fields at startup
- Helper properties (is_development, is_production, max_file_size_bytes)
- JSON parsing for list fields (CORS origins, supported countries)

**Code Snippet**:
```python
class Settings(BaseSettings):
    APP_NAME: str = "BOMA"
    DATABASE_URL: str  # Required
    CLERK_PEM_PUBLIC_KEY: str  # Required
    PLATFORM_FEE_PERCENTAGE: float = 15.0
    # ... 50+ configuration fields

settings = Settings()  # Global singleton
```

**Why**: Pydantic's BaseSettings provides automatic validation and type conversion, catching configuration errors at startup before any requests are processed.

**Decision**: Use a singleton pattern for settings to avoid re-parsing environment variables on every import.

---

#### 1.5 Logging Configuration (app/core/logging_config.py)
**What**: Set up structured JSON logging for production observability.

**Features**:
- JSON formatter for structured logs (easy parsing by log aggregators)
- Contextual fields: app_name, environment, level, logger name
- Configurable log levels via environment
- Reduced noise from SQLAlchemy and HTTP libraries
- ISO timestamp format

**Why**:
- JSON logs are machine-readable and easy to search/analyze
- Structured logging essential for production debugging
- Enables integration with log aggregation services (Datadog, ELK, CloudWatch)

**Decision**: Default to JSON format even in development to maintain consistency and test what we'll use in production.

---

#### 1.6 Main FastAPI Application (app/main.py)
**What**: Created the FastAPI application instance with all middleware and routing.

**Components**:
1. **Lifespan Manager**: Async context manager for startup/shutdown tasks
2. **CORS Middleware**: Allow mobile app origins (localhost for dev)
3. **Trusted Host Middleware**: Production security (only *.boma.co.tz)
4. **Custom Middleware**:
   - RequestLoggerMiddleware: Logs every request with timing
   - ErrorHandlerMiddleware: Global exception handling
5. **Health Check Endpoint**: `/health` for monitoring
6. **API Router**: Includes v1 routes with prefix `/api/v1`

**Why**:
- Middleware order matters: error handler first, then request logger
- Health check endpoint needed for load balancer health checks
- Lifespan manager provides clean startup/shutdown hooks for DB connections

**Decision**: Keep API versioning in URL path (`/api/v1/`) for clear versioning and future v2 support.

---

#### 1.7 Custom Middleware

##### RequestLoggerMiddleware (app/api/middleware/request_logger.py)
**What**: Logs every HTTP request with request ID, duration, and status.

**Features**:
- Generates unique request ID for tracing
- Logs request start and completion
- Calculates and logs request duration
- Adds X-Request-ID header to response
- Structured logging with extra context

**Why**: Essential for debugging, performance monitoring, and request tracing across distributed systems.

##### ErrorHandlerMiddleware (app/api/middleware/error_handler.py)
**What**: Catches all unhandled exceptions and returns consistent error responses.

**Features**:
- Handles ValueError → 422 Unprocessable Entity
- Handles PermissionError → 403 Forbidden
- Catches all other exceptions → 500 Internal Server Error
- Includes request_id in error responses for tracing
- Logs errors with full stack traces

**Why**: Consistent error responses improve API usability and prevent leaking sensitive error details to clients.

**Decision**: Never expose internal error details (database errors, stack traces) to API clients in production.

---

#### 1.8 API Router Structure (app/api/v1/__init__.py)
**What**: Created main API router with placeholder for future endpoints.

**Structure**:
```python
api_router = APIRouter()
# Future: include auth, users, properties, bookings routers
```

**Why**: Modular router design allows organizing endpoints by domain (auth, properties, bookings) rather than one massive route file.

---

### 2. Mobile App Infrastructure Setup

#### 2.1 Expo App Initialization
**What**: Created React Native mobile app using Expo CLI with TypeScript template.

**Command**: `npx create-expo-app mobile --template blank-typescript`

**Why**:
- Expo provides unified iOS/Android development with single codebase
- TypeScript for type safety and better IDE support
- Blank template gives clean starting point without unnecessary boilerplate

**Decision**: Use Expo SDK 54 (latest stable) with React Native 0.81.5 and React 19.1.0.

---

#### 2.2 Folder Structure (Atomic Design Pattern)
**What**: Created organized folder structure following Atomic Design principles.

**Structure**:
```
mobile/src/
├── components/
│   ├── atoms/          # Basic building blocks (Button, Input, Text)
│   ├── molecules/      # Simple combinations (InputWithLabel, PropertyCard)
│   └── organisms/      # Complex components (SearchBar, BookingSummary)
├── screens/
│   ├── auth/           # Login, Signup, OTP screens
│   ├── guest/          # Guest-specific screens
│   ├── host/           # Host-specific screens
│   └── common/         # Shared screens (Settings, Help)
├── services/           # API client, external services
├── navigation/         # React Navigation setup
├── store/              # Zustand state management
├── types/              # TypeScript definitions
├── hooks/              # Custom React hooks
├── utils/              # Helper functions
├── constants/          # Config, colors, sizes
└── assets/
    ├── images/
    ├── fonts/
    └── icons/
```

**Why**:
- **Atomic Design**: Promotes reusability and consistency in UI components
- **Screen Organization**: Separates guest and host flows for clarity
- **Service Layer**: Isolates API logic from UI components
- **Type Safety**: Central TypeScript definitions prevent type mismatches

**Decision**: Strict separation between guest and host screens, though some components will be shared via common folder.

---

#### 2.3 Mobile Dependencies
**What**: Installed essential npm packages for navigation, state, API, and auth.

**Key Dependencies**:
- **@react-navigation/native, /stack, /bottom-tabs**: App navigation
- **zustand**: Lightweight state management
- **axios**: HTTP client for API calls
- **@clerk/clerk-expo**: Authentication integration
- **expo-secure-store**: Secure token storage
- **expo-image-picker**: Property photo uploads
- **expo-location**: Location services for property search
- **date-fns**: Date manipulation for bookings
- **zod**: Runtime validation

**Why**:
- React Navigation is industry standard for RN navigation
- Zustand is simpler than Redux, perfect for mobile app state
- Clerk Expo SDK provides pre-built auth UI components
- Expo modules integrate seamlessly with Expo SDK

**Decision**: Use `--legacy-peer-deps` flag due to React 19 peer dependency conflicts (common in early React 19 adoption).

---

#### 2.4 Configuration Constants (mobile/src/constants/config.ts)
**What**: Created central configuration file for app-wide constants.

**Sections**:
```typescript
export const API_CONFIG = {
  BASE_URL: __DEV__ ? 'http://localhost:8000' : 'https://api.boma.co.tz',
  API_VERSION: 'v1',
  TIMEOUT: 30000,
};

export const APP_CONFIG = {
  DEFAULT_COUNTRY: 'TZ',
  DEFAULT_CURRENCY: 'TZS',
  SUPPORTED_LANGUAGES: ['en', 'sw'],
};

export const BOOKING_CONFIG = {
  MIN_HOURS: 4,
  MAX_ADVANCE_DAYS: 365,
};
```

**Why**:
- Central configuration prevents magic numbers scattered throughout code
- Environment-specific API URLs handled automatically
- Tanzania-specific defaults (TZ, TZS, Dar es Salaam coordinates)

**Decision**: Use `__DEV__` flag for automatic localhost/production API switching.

---

#### 2.5 TypeScript Type Definitions (mobile/src/types/index.ts)
**What**: Created comprehensive type definitions for all domain entities.

**Types Defined**:
1. **User Types**: User, GuestProfile, HostProfile, UserRole
2. **Property Types**: Property, PropertyPhoto, Amenity, PropertyStatus
3. **Booking Types**: Booking, BookingQuote, BookingStatus, CancellationPolicy
4. **Payment Types**: Payment, PaymentGateway, PaymentStatus
5. **Review Types**: Review
6. **Search Types**: SearchFilters, PaginationParams, PaginatedResponse
7. **API Types**: ApiResponse, ApiError
8. **State Types**: AuthState, AppState

**Example**:
```typescript
export interface Property {
  id: string;
  hostId: string;
  title: string;
  propertyType: 'apartment' | 'house' | 'room' | 'studio' | 'villa';
  status: PropertyStatus;
  latitude: number;
  longitude: number;
  basePrice: number;
  currency: string;
  amenities: Amenity[];
  // ... more fields
}
```

**Why**:
- Shared types between mobile and backend ensure API contract compliance
- TypeScript catches type errors at compile time
- IDE autocomplete improves developer experience
- Self-documenting code

**Decision**: Keep types in sync with backend Pydantic schemas. Consider generating types from OpenAPI spec in future.

---

#### 2.6 API Client Service (mobile/src/services/api.ts)
**What**: Created centralized API client with error handling, retries, and auth token management.

**Features**:
1. **Axios Instance**: Pre-configured with base URL and timeout
2. **Request Interceptor**: Automatically adds auth token to headers
3. **Response Interceptor**: Handles errors uniformly
4. **Error Handling**: Maps HTTP status codes to semantic error codes
5. **HTTP Methods**: get, post, put, patch, delete wrappers
6. **File Upload**: multipart/form-data support
7. **Retry Logic**: Exponential backoff for network errors

**Key Methods**:
```typescript
class ApiClient {
  setAuthToken(token: string | null): void
  async get<T>(url: string): Promise<ApiResponse<T>>
  async post<T>(url: string, data: any): Promise<ApiResponse<T>>
  async uploadFile<T>(url: string, file: File): Promise<ApiResponse<T>>
  async retryRequest<T>(requestFn: () => Promise<T>): Promise<T>
}

export const apiClient = new ApiClient();
```

**Error Mapping**:
- 401 → UNAUTHORIZED (trigger logout)
- 403 → FORBIDDEN
- 404 → NOT_FOUND
- 422 → VALIDATION_ERROR
- 429 → RATE_LIMIT_EXCEEDED
- 5xx → SERVER_ERROR

**Why**:
- Single source of truth for API communication
- Consistent error handling across entire app
- Automatic token injection prevents manual header management
- Retry logic handles unstable network conditions (common in Tanzania)

**Decision**: Export singleton instance (apiClient) for convenience, but also export class for testing purposes.

---

### 3. Infrastructure & Development Environment

#### 3.1 Docker Compose Configuration (docker-compose.yml)
**What**: Created Docker Compose file for local development services.

**Services**:
1. **postgres**: PostgreSQL 16 Alpine
   - Port 5432
   - Credentials: boma_user/boma_password/boma_db
   - Health check enabled
   - Persistent volume

2. **redis**: Redis 7 Alpine
   - Port 6379
   - Persistent volume
   - AOF (append-only file) enabled

3. **api** (commented): Backend API service (optional containerized dev)
4. **worker** (commented): Celery worker (optional containerized dev)

**Why**:
- Consistent development environment across team
- No need to install Postgres/Redis locally
- Docker Compose simple enough for non-DevOps developers
- Optional backend containerization allows flexible dev workflow

**Decision**: Keep backend containerization optional (commented) to allow developers to run backend locally for faster iteration with hot-reload.

**Usage**:
```bash
docker-compose up -d postgres redis    # Start DB and cache only
docker-compose up -d                   # Start all services
```

---

#### 3.2 Git Repository & .gitignore
**What**: Initialized Git repository and created comprehensive .gitignore file.

**.gitignore Includes**:
- Python: __pycache__, *.pyc, venv/, .pytest_cache/
- Node.js: node_modules/, package-lock.json, .expo/
- Secrets: .env, *.pem, *.key, credentials.json
- IDE: .vscode/, .idea/, .DS_Store
- Databases: *.db, *.sqlite
- Build artifacts: build/, dist/, *.egg-info/

**Why**:
- Prevent committing secrets and credentials
- Keep repository clean of generated files
- Reduce repository size
- Follow security best practices

**Decision**: Removed mobile/.git (created by Expo CLI) to maintain single repository for monorepo structure.

---

#### 3.3 Comprehensive README.md
**What**: Created detailed README with project overview, setup instructions, and development workflows.

**Sections**:
1. **Project Overview**: What BOMA is and core features
2. **Architecture**: Tech stack overview
3. **Project Structure**: Detailed folder explanations
4. **Getting Started**: Step-by-step setup for backend and mobile
5. **Development Workflow**: Phase breakdown
6. **Available Scripts**: Common commands for both backend and mobile
7. **Environment Configuration**: How to set up .env files
8. **Database Migrations**: Alembic commands
9. **Testing**: How to run tests
10. **Documentation References**: Links to CLAUDE.md and project_log.md

**Why**:
- Essential for onboarding new developers
- Quick reference for common commands
- Documents project structure and decisions
- Self-contained knowledge base

**Decision**: Keep README concise and link to CLAUDE.md for detailed architecture and project_log.md for development history.

---

### 4. Key Architectural Decisions Made

#### 4.1 Monolith vs Microservices
**Decision**: Monolith architecture (single FastAPI app, single repo)

**Rationale**:
- Simpler to develop, test, and deploy
- Easier to maintain consistency
- Lower operational overhead (one deployment)
- Can split into microservices later if needed
- Most successful startups start with monoliths

---

#### 4.2 Authentication Strategy
**Decision**: Use Clerk for authentication, maintain own user database

**Rationale**:
- Clerk handles complex auth flows (OTP, session management, password security)
- Clerk supports phone number auth (critical for Tanzania)
- Backend validates JWT and maps to internal user ID
- Own database allows:
  - Custom roles (guest, host, admin)
  - KYC status tracking
  - Business logic tied to users
  - Flexibility to switch auth providers later

---

#### 4.3 Mobile State Management
**Decision**: Zustand over Redux

**Rationale**:
- Simpler API with less boilerplate
- Hooks-based (modern React pattern)
- Smaller bundle size
- TypeScript-friendly
- Sufficient for mobile app complexity

---

#### 4.4 Database Access Pattern
**Decision**: SQLAlchemy ORM with async support

**Rationale**:
- Type-safe database queries
- Automatic SQL generation
- Migration support via Alembic
- Async/await support for FastAPI
- Python-native (no learning new query language)

---

#### 4.5 API Versioning
**Decision**: URL path versioning (`/api/v1/`)

**Rationale**:
- Clear and explicit versioning
- Easy to support multiple versions simultaneously
- Industry standard
- Mobile apps can specify version they support

---

#### 4.6 Error Handling Strategy
**Decision**: Consistent error response format with semantic error codes

**Format**:
```json
{
  "error": "Validation Error",
  "code": "VALIDATION_ERROR",
  "detail": "Email address is invalid",
  "request_id": "uuid"
}
```

**Rationale**:
- Clients can handle errors programmatically using codes
- Request ID enables tracing errors in logs
- Consistent structure reduces client-side error handling complexity
- Never expose internal details (stack traces, DB errors)

---

### 5. Next Steps (Phase 1)

**Phase 1: Database Schema & Core Models** will include:
1. Design complete PostgreSQL schema (35+ tables)
2. Create Alembic migration files for all entities:
   - users, guest_profiles, host_profiles
   - properties, property_photos, amenities
   - bookings, payments, payouts, refunds, transactions
   - reviews, support_tickets, disputes
   - kyc_documents, notifications
3. Implement SQLAlchemy models with relationships
4. Add indexes, constraints, foreign keys
5. Generate ER diagram
6. Create seed data for development

**Timeline**: Week 1-2

---

### 6. Files Created in Phase 0

**Backend**:
- backend/requirements.txt
- backend/.env.example
- backend/app/main.py
- backend/app/core/config.py
- backend/app/core/logging_config.py
- backend/app/api/v1/__init__.py
- backend/app/api/middleware/request_logger.py
- backend/app/api/middleware/error_handler.py
- backend/app/{models,schemas,services,db,tasks,utils}/__init__.py
- backend/tests/{unit,integration}/__init__.py
- backend/alembic/ (directory structure)

**Mobile**:
- mobile/src/constants/config.ts
- mobile/src/types/index.ts
- mobile/src/services/api.ts
- mobile/src/{components,screens,navigation,store,hooks,utils,assets}/ (directory structure)

**Root**:
- .gitignore
- docker-compose.yml
- README.md
- project_log.md (this file)

**Total**: 50+ files and directories created

---

### 7. Technical Metrics

- **Backend Lines of Code**: ~800 lines (configuration, middleware, core)
- **Mobile Lines of Code**: ~500 lines (types, API client, config)
- **Dependencies**: 30+ Python packages, 15+ npm packages
- **Time to Setup**: ~2 hours
- **Documentation**: 350+ lines in README, 600+ lines in project_log

---

### 8. Lessons Learned & Notes

1. **React 19 Peer Dependencies**: Encountered peer dependency conflicts with Clerk SDK. Resolved with `--legacy-peer-deps` flag. Monitor for updates.

2. **Expo as Git Submodule**: Expo CLI creates its own .git directory. Removed it to maintain single repository structure.

3. **Configuration First**: Setting up comprehensive configuration and environment management early prevents technical debt later.

4. **Type Safety**: Defining types early (TypeScript mobile + Pydantic backend) provides immediate value and prevents future bugs.

5. **Structured Logging**: JSON logging from day one makes production debugging much easier later.

6. **Docker for Development**: Docker Compose simplifies onboarding and ensures consistency, but keeping backend outside Docker allows faster iteration.

---

## Phase 1: Database Schema & Core Models
**Status**: 🔜 Pending
**Start Date**: TBD

---

*This log will be updated continuously as development progresses.*
