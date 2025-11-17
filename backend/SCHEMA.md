# BOMA Database Schema Design

This document defines the complete PostgreSQL database schema for the BOMA platform.

## Design Principles

1. **Multi-currency & multi-country ready**: All tables include `country_code` and `currency` fields where relevant
2. **Audit trail**: All tables have `created_at` and `updated_at` timestamps
3. **Soft deletes**: Critical tables use `deleted_at` for soft deletion
4. **UUIDs for IDs**: Using UUID primary keys for better distribution and security
5. **Double-entry accounting**: Financial transactions follow double-entry bookkeeping
6. **Denormalization where needed**: Some fields duplicated for performance (e.g., currency on bookings)

---

## Table Definitions

### 1. Users & Authentication

#### `users`
Core identity table for all platform users.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Internal user ID |
| clerk_id | VARCHAR(255) | UNIQUE, NOT NULL | External auth provider ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| phone_number | VARCHAR(50) | UNIQUE, NULL | Phone number |
| country_code | VARCHAR(2) | NOT NULL, DEFAULT 'TZ' | ISO country code |
| is_guest | BOOLEAN | DEFAULT TRUE | Can act as guest |
| is_host | BOOLEAN | DEFAULT FALSE | Can act as host |
| is_admin | BOOLEAN | DEFAULT FALSE | Platform admin |
| status | ENUM | NOT NULL, DEFAULT 'active' | active, suspended, banned |
| email_verified | BOOLEAN | DEFAULT FALSE | Email verification status |
| phone_verified | BOOLEAN | DEFAULT FALSE | Phone verification status |
| created_at | TIMESTAMP | NOT NULL | Account creation |
| updated_at | TIMESTAMP | NOT NULL | Last update |
| last_login_at | TIMESTAMP | NULL | Last login timestamp |

**Indexes**:
- `idx_users_clerk_id` on `clerk_id`
- `idx_users_email` on `email`
- `idx_users_phone_number` on `phone_number`
- `idx_users_status` on `status`

---

#### `guest_profiles`
Extended profile for users acting as guests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Profile ID |
| user_id | UUID | FK(users.id), UNIQUE | User reference |
| preferred_language | VARCHAR(10) | DEFAULT 'en' | Preferred language |
| emergency_contact_name | VARCHAR(255) | NULL | Emergency contact |
| emergency_contact_phone | VARCHAR(50) | NULL | Emergency phone |
| government_id_type | VARCHAR(50) | NULL | NIDA, Passport, etc. |
| government_id_number | VARCHAR(100) | NULL | ID number (encrypted) |
| date_of_birth | DATE | NULL | Date of birth |
| profile_photo_url | TEXT | NULL | Cloudinary URL |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_guest_profiles_user_id` on `user_id`

---

#### `host_profiles`
Extended profile for users acting as hosts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Profile ID |
| user_id | UUID | FK(users.id), UNIQUE | User reference |
| business_type | ENUM | NOT NULL | individual, business |
| business_name | VARCHAR(255) | NULL | Company name |
| business_registration_number | VARCHAR(100) | NULL | Tax/registration number |
| tax_id | VARCHAR(100) | NULL | TIN number |
| payout_method | ENUM | NOT NULL, DEFAULT 'mobile_money' | mobile_money, bank_transfer |
| payout_phone_number | VARCHAR(50) | NULL | Mobile money number |
| payout_bank_name | VARCHAR(100) | NULL | Bank name |
| payout_account_number | VARCHAR(100) | NULL | Account number |
| payout_account_name | VARCHAR(255) | NULL | Account holder name |
| verification_status | ENUM | NOT NULL, DEFAULT 'unverified' | unverified, pending, verified, rejected |
| verification_notes | TEXT | NULL | Admin notes |
| verified_at | TIMESTAMP | NULL | Verification timestamp |
| verified_by | UUID | FK(users.id), NULL | Admin who verified |
| profile_photo_url | TEXT | NULL | Cloudinary URL |
| bio | TEXT | NULL | Host bio |
| response_rate | DECIMAL(5,2) | DEFAULT 0.00 | % of messages responded |
| response_time_hours | INTEGER | NULL | Avg response time |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_host_profiles_user_id` on `user_id`
- `idx_host_profiles_verification_status` on `verification_status`

---

#### `kyc_documents`
KYC documents uploaded by users (hosts mainly).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Document ID |
| user_id | UUID | FK(users.id), NOT NULL | User who uploaded |
| document_type | ENUM | NOT NULL | nida, passport, business_reg, tax_cert, utility_bill |
| document_url | TEXT | NOT NULL | Secure storage URL |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending, approved, rejected |
| rejection_reason | TEXT | NULL | Why rejected |
| reviewed_by | UUID | FK(users.id), NULL | Admin who reviewed |
| reviewed_at | TIMESTAMP | NULL | Review timestamp |
| expiry_date | DATE | NULL | Document expiry |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_kyc_documents_user_id` on `user_id`
- `idx_kyc_documents_status` on `status`

---

### 2. Properties

#### `properties`
Rentable properties listed by hosts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Property ID |
| host_id | UUID | FK(users.id), NOT NULL | Owner/manager |
| title | VARCHAR(255) | NOT NULL | Property title |
| description | TEXT | NOT NULL | Full description |
| property_type | ENUM | NOT NULL | apartment, house, room, studio, villa |
| address_line1 | VARCHAR(255) | NOT NULL | Street address |
| address_line2 | VARCHAR(255) | NULL | Apt/Unit |
| city | VARCHAR(100) | NOT NULL | City |
| region | VARCHAR(100) | NOT NULL | State/Region |
| postal_code | VARCHAR(20) | NULL | Postal code |
| country_code | VARCHAR(2) | NOT NULL, DEFAULT 'TZ' | Country |
| latitude | DECIMAL(10,8) | NOT NULL | GPS latitude |
| longitude | DECIMAL(11,8) | NOT NULL | GPS longitude |
| bedrooms | INTEGER | NOT NULL | Number of bedrooms |
| bathrooms | DECIMAL(3,1) | NOT NULL | Number of bathrooms |
| max_guests | INTEGER | NOT NULL | Maximum guests |
| square_meters | DECIMAL(8,2) | NULL | Property size |
| base_price | DECIMAL(10,2) | NOT NULL | Base nightly price |
| currency | VARCHAR(3) | NOT NULL, DEFAULT 'TZS' | Price currency |
| cleaning_fee | DECIMAL(10,2) | DEFAULT 0.00 | One-time cleaning fee |
| deposit_amount | DECIMAL(10,2) | NOT NULL | Security deposit |
| minimum_nights | INTEGER | NOT NULL, DEFAULT 1 | Min booking nights |
| maximum_nights | INTEGER | NOT NULL, DEFAULT 365 | Max booking nights |
| check_in_time | TIME | NOT NULL, DEFAULT '14:00' | Check-in time |
| check_out_time | TIME | NOT NULL, DEFAULT '11:00' | Check-out time |
| cancellation_policy | ENUM | NOT NULL, DEFAULT 'moderate' | flexible, moderate, strict |
| pets_allowed | BOOLEAN | DEFAULT FALSE | |
| smoking_allowed | BOOLEAN | DEFAULT FALSE | |
| parties_allowed | BOOLEAN | DEFAULT FALSE | |
| children_allowed | BOOLEAN | DEFAULT TRUE | |
| house_rules | TEXT | NULL | Additional rules |
| status | ENUM | NOT NULL, DEFAULT 'draft' | draft, pending_verification, verified, suspended, delisted |
| verification_status | ENUM | NOT NULL, DEFAULT 'unverified' | unverified, pending, verified |
| verified_at | TIMESTAMP | NULL | |
| verified_by | UUID | FK(users.id), NULL | City ops member |
| instant_book | BOOLEAN | DEFAULT FALSE | Allow instant booking |
| active | BOOLEAN | DEFAULT TRUE | Currently accepting bookings |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |
| deleted_at | TIMESTAMP | NULL | Soft delete |

**Indexes**:
- `idx_properties_host_id` on `host_id`
- `idx_properties_status` on `status`
- `idx_properties_location` (GiST) on `(latitude, longitude)`
- `idx_properties_city` on `city`
- `idx_properties_property_type` on `property_type`
- `idx_properties_created_at` on `created_at DESC`

---

#### `property_photos`
Photos of properties.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Photo ID |
| property_id | UUID | FK(properties.id), NOT NULL | Property reference |
| photo_url | TEXT | NOT NULL | Cloudinary URL |
| thumbnail_url | TEXT | NOT NULL | Thumbnail URL |
| display_order | INTEGER | NOT NULL | Sort order |
| is_cover | BOOLEAN | DEFAULT FALSE | Cover photo flag |
| caption | VARCHAR(500) | NULL | Photo caption |
| is_verified | BOOLEAN | DEFAULT FALSE | Taken by staff |
| uploaded_by | UUID | FK(users.id), NOT NULL | Who uploaded |
| created_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_property_photos_property_id` on `property_id`
- `idx_property_photos_order` on `(property_id, display_order)`

---

#### `amenities`
Master list of available amenities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Amenity ID |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Amenity name |
| category | ENUM | NOT NULL | basic, kitchen, bathroom, entertainment, safety, outdoor |
| icon | VARCHAR(50) | NULL | Icon identifier |
| created_at | TIMESTAMP | NOT NULL | |

---

#### `property_amenities`
Join table for property amenities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| property_id | UUID | FK(properties.id), NOT NULL | |
| amenity_id | UUID | FK(amenities.id), NOT NULL | |
| created_at | TIMESTAMP | NOT NULL | |

**Primary Key**: `(property_id, amenity_id)`

**Indexes**:
- `idx_property_amenities_property` on `property_id`
- `idx_property_amenities_amenity` on `amenity_id`

---

### 3. Availability & Pricing

#### `availability_rules`
Default availability rules for properties.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Rule ID |
| property_id | UUID | FK(properties.id), NOT NULL | Property reference |
| day_of_week | INTEGER | NULL | 0-6 (Sunday-Saturday), NULL for all |
| min_nights | INTEGER | NULL | Override minimum nights |
| max_nights | INTEGER | NULL | Override maximum nights |
| is_available | BOOLEAN | DEFAULT TRUE | Available on this day |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_availability_rules_property_id` on `property_id`

---

#### `availability_overrides`
Specific date overrides for availability.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Override ID |
| property_id | UUID | FK(properties.id), NOT NULL | Property reference |
| date | DATE | NOT NULL | Specific date |
| is_available | BOOLEAN | DEFAULT FALSE | Available on this date |
| reason | VARCHAR(255) | NULL | Why blocked |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Unique Constraint**: `(property_id, date)`

**Indexes**:
- `idx_availability_overrides_property_date` on `(property_id, date)`

---

#### `pricing_rules`
Dynamic pricing rules for properties.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Rule ID |
| property_id | UUID | FK(properties.id), NOT NULL | Property reference |
| rule_type | ENUM | NOT NULL | weekly_discount, monthly_discount, weekend_premium, seasonal |
| discount_percentage | DECIMAL(5,2) | NULL | Discount % (negative for premium) |
| start_date | DATE | NULL | Seasonal start |
| end_date | DATE | NULL | Seasonal end |
| min_nights | INTEGER | NULL | Minimum nights for discount |
| active | BOOLEAN | DEFAULT TRUE | Rule active |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_pricing_rules_property_id` on `property_id`
- `idx_pricing_rules_dates` on `(start_date, end_date)`

---

### 4. Bookings & Reviews

#### `bookings`
Core booking records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Booking ID |
| property_id | UUID | FK(properties.id), NOT NULL | Property booked |
| guest_id | UUID | FK(users.id), NOT NULL | Guest user |
| host_id | UUID | FK(users.id), NOT NULL | Host user (denormalized) |
| check_in_date | DATE | NOT NULL | Check-in date |
| check_out_date | DATE | NOT NULL | Check-out date |
| num_nights | INTEGER | NOT NULL | Calculated nights |
| num_guests | INTEGER | NOT NULL | Number of guests |
| base_price_per_night | DECIMAL(10,2) | NOT NULL | Nightly rate at booking |
| total_nights_cost | DECIMAL(10,2) | NOT NULL | Nights × rate |
| cleaning_fee | DECIMAL(10,2) | DEFAULT 0.00 | Cleaning fee |
| platform_fee | DECIMAL(10,2) | NOT NULL | BOMA commission |
| total_price | DECIMAL(10,2) | NOT NULL | Grand total |
| deposit_amount | DECIMAL(10,2) | NOT NULL | Security deposit |
| currency | VARCHAR(3) | NOT NULL | Booking currency |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending, awaiting_payment, confirmed, checked_in, checked_out, completed, cancelled, no_show |
| payment_status | ENUM | NOT NULL, DEFAULT 'unpaid' | unpaid, partially_paid, paid, refunded |
| cancellation_policy | ENUM | NOT NULL | Policy at booking time |
| cancelled_at | TIMESTAMP | NULL | Cancellation timestamp |
| cancelled_by | UUID | FK(users.id), NULL | Who cancelled |
| cancellation_reason | TEXT | NULL | Cancellation reason |
| refund_amount | DECIMAL(10,2) | NULL | Refund amount |
| special_requests | TEXT | NULL | Guest special requests |
| check_in_instructions | TEXT | NULL | Access instructions |
| check_in_confirmed_at | TIMESTAMP | NULL | |
| check_out_confirmed_at | TIMESTAMP | NULL | |
| expires_at | TIMESTAMP | NULL | Payment expiry |
| created_at | TIMESTAMP | NOT NULL | Booking created |
| updated_at | TIMESTAMP | NOT NULL | Last update |

**Indexes**:
- `idx_bookings_property_id` on `property_id`
- `idx_bookings_guest_id` on `guest_id`
- `idx_bookings_host_id` on `host_id`
- `idx_bookings_status` on `status`
- `idx_bookings_dates` on `(check_in_date, check_out_date)`
- `idx_bookings_created_at` on `created_at DESC`

---

#### `reviews`
Reviews from guests about properties and hosts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Review ID |
| booking_id | UUID | FK(bookings.id), UNIQUE, NOT NULL | Booking reviewed |
| property_id | UUID | FK(properties.id), NOT NULL | Property reviewed |
| host_id | UUID | FK(users.id), NOT NULL | Host reviewed |
| guest_id | UUID | FK(users.id), NOT NULL | Reviewer |
| rating | INTEGER | NOT NULL, CHECK 1-5 | Overall rating |
| cleanliness_rating | INTEGER | NULL, CHECK 1-5 | |
| accuracy_rating | INTEGER | NULL, CHECK 1-5 | |
| communication_rating | INTEGER | NULL, CHECK 1-5 | |
| location_rating | INTEGER | NULL, CHECK 1-5 | |
| value_rating | INTEGER | NULL, CHECK 1-5 | |
| comment | TEXT | NULL | Review text |
| is_public | BOOLEAN | DEFAULT TRUE | Visible to others |
| host_response | TEXT | NULL | Host reply |
| host_responded_at | TIMESTAMP | NULL | |
| flagged | BOOLEAN | DEFAULT FALSE | Flagged for review |
| flagged_reason | VARCHAR(255) | NULL | |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_reviews_booking_id` on `booking_id`
- `idx_reviews_property_id` on `property_id`
- `idx_reviews_host_id` on `host_id`
- `idx_reviews_guest_id` on `guest_id`

---

### 5. Financial Tables

#### `payments`
Incoming payments from guests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Payment ID |
| booking_id | UUID | FK(bookings.id), NOT NULL | Related booking |
| guest_id | UUID | FK(users.id), NOT NULL | Payer |
| amount | DECIMAL(10,2) | NOT NULL | Payment amount |
| currency | VARCHAR(3) | NOT NULL | Payment currency |
| gateway | ENUM | NOT NULL | azampay, selcom, stripe |
| gateway_reference | VARCHAR(255) | UNIQUE, NOT NULL | External payment ID |
| payment_method | ENUM | NOT NULL | mobile_money, card, bank_transfer |
| phone_number | VARCHAR(50) | NULL | Mobile money number |
| status | ENUM | NOT NULL, DEFAULT 'initiated' | initiated, pending, success, failed, cancelled |
| failure_reason | TEXT | NULL | Why failed |
| gateway_fee | DECIMAL(10,2) | DEFAULT 0.00 | Gateway charges |
| net_amount | DECIMAL(10,2) | NOT NULL | Amount - fees |
| metadata | JSONB | NULL | Gateway response |
| idempotency_key | VARCHAR(255) | UNIQUE, NOT NULL | Prevent duplicates |
| paid_at | TIMESTAMP | NULL | Successful payment timestamp |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_payments_booking_id` on `booking_id`
- `idx_payments_guest_id` on `guest_id`
- `idx_payments_status` on `status`
- `idx_payments_gateway_reference` on `gateway_reference`
- `idx_payments_idempotency_key` on `idempotency_key`

---

#### `payouts`
Outgoing payments to hosts.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Payout ID |
| host_id | UUID | FK(users.id), NOT NULL | Recipient |
| amount | DECIMAL(10,2) | NOT NULL | Payout amount |
| currency | VARCHAR(3) | NOT NULL | Payout currency |
| payout_method | ENUM | NOT NULL | mobile_money, bank_transfer |
| phone_number | VARCHAR(50) | NULL | Mobile money |
| bank_name | VARCHAR(100) | NULL | Bank name |
| account_number | VARCHAR(100) | NULL | Account number |
| account_name | VARCHAR(255) | NULL | Account holder |
| gateway | ENUM | NULL | azampay, selcom, manual |
| gateway_reference | VARCHAR(255) | UNIQUE, NULL | External payout ID |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending, processing, completed, failed, cancelled |
| failure_reason | TEXT | NULL | Why failed |
| gateway_fee | DECIMAL(10,2) | DEFAULT 0.00 | Payout fees |
| net_amount | DECIMAL(10,2) | NOT NULL | Amount - fees |
| metadata | JSONB | NULL | Gateway response |
| processed_at | TIMESTAMP | NULL | Completion timestamp |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_payouts_host_id` on `host_id`
- `idx_payouts_status` on `status`
- `idx_payouts_gateway_reference` on `gateway_reference`

---

#### `refunds`
Refunds issued to guests.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Refund ID |
| payment_id | UUID | FK(payments.id), NOT NULL | Original payment |
| booking_id | UUID | FK(bookings.id), NOT NULL | Related booking |
| guest_id | UUID | FK(users.id), NOT NULL | Recipient |
| amount | DECIMAL(10,2) | NOT NULL | Refund amount |
| currency | VARCHAR(3) | NOT NULL | Refund currency |
| reason | ENUM | NOT NULL | cancellation, dispute, damage_waiver, system_error |
| reason_detail | TEXT | NULL | Detailed reason |
| gateway | ENUM | NOT NULL | azampay, selcom, stripe |
| gateway_reference | VARCHAR(255) | UNIQUE, NULL | External refund ID |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending, processing, completed, failed |
| failure_reason | TEXT | NULL | Why failed |
| processed_by | UUID | FK(users.id), NULL | Admin who processed |
| processed_at | TIMESTAMP | NULL | |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_refunds_payment_id` on `payment_id`
- `idx_refunds_booking_id` on `booking_id`
- `idx_refunds_guest_id` on `guest_id`
- `idx_refunds_status` on `status`

---

#### `transactions`
Double-entry ledger for all financial movements.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Transaction ID |
| transaction_group_id | UUID | NOT NULL | Group related entries |
| account_type | ENUM | NOT NULL | guest_wallet, host_wallet, platform_wallet, gateway_receivable, platform_revenue, gateway_fees |
| entity_id | UUID | NULL | User ID if wallet account |
| debit | DECIMAL(10,2) | DEFAULT 0.00 | Debit amount |
| credit | DECIMAL(10,2) | DEFAULT 0.00 | Credit amount |
| currency | VARCHAR(3) | NOT NULL | Transaction currency |
| reference_type | ENUM | NOT NULL | payment, payout, refund, booking, fee |
| reference_id | UUID | NOT NULL | ID of referenced entity |
| description | VARCHAR(500) | NOT NULL | Human-readable description |
| metadata | JSONB | NULL | Additional data |
| created_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_transactions_group_id` on `transaction_group_id`
- `idx_transactions_entity_id` on `entity_id`
- `idx_transactions_reference` on `(reference_type, reference_id)`
- `idx_transactions_created_at` on `created_at DESC`

---

### 6. Support & Disputes

#### `support_tickets`
Customer support tickets.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Ticket ID |
| user_id | UUID | FK(users.id), NOT NULL | Ticket creator |
| booking_id | UUID | FK(bookings.id), NULL | Related booking |
| property_id | UUID | FK(properties.id), NULL | Related property |
| category | ENUM | NOT NULL | booking_issue, payment_issue, property_issue, account_issue, other |
| priority | ENUM | NOT NULL, DEFAULT 'medium' | low, medium, high, urgent |
| status | ENUM | NOT NULL, DEFAULT 'open' | open, in_progress, waiting_user, waiting_admin, resolved, closed |
| subject | VARCHAR(255) | NOT NULL | Ticket subject |
| description | TEXT | NOT NULL | Issue description |
| assigned_to | UUID | FK(users.id), NULL | Admin assigned |
| resolved_at | TIMESTAMP | NULL | Resolution timestamp |
| resolution_notes | TEXT | NULL | How resolved |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_support_tickets_user_id` on `user_id`
- `idx_support_tickets_status` on `status`
- `idx_support_tickets_assigned_to` on `assigned_to`
- `idx_support_tickets_created_at` on `created_at DESC`

---

#### `disputes`
Damage and refund disputes.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Dispute ID |
| booking_id | UUID | FK(bookings.id), NOT NULL | Related booking |
| claimant_id | UUID | FK(users.id), NOT NULL | Who filed |
| respondent_id | UUID | FK(users.id), NOT NULL | Who responds |
| dispute_type | ENUM | NOT NULL | damage_claim, refund_request, cancellation_dispute, other |
| claim_amount | DECIMAL(10,2) | NOT NULL | Amount claimed |
| currency | VARCHAR(3) | NOT NULL | Claim currency |
| description | TEXT | NOT NULL | Dispute description |
| evidence_urls | JSONB | NULL | Array of photo URLs |
| status | ENUM | NOT NULL, DEFAULT 'open' | open, under_review, resolved, closed |
| resolution | ENUM | NULL | approved, partial, denied |
| resolution_amount | DECIMAL(10,2) | NULL | Final amount |
| resolution_notes | TEXT | NULL | Admin decision |
| resolved_by | UUID | FK(users.id), NULL | Admin who resolved |
| resolved_at | TIMESTAMP | NULL | |
| created_at | TIMESTAMP | NOT NULL | |
| updated_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_disputes_booking_id` on `booking_id`
- `idx_disputes_claimant_id` on `claimant_id`
- `idx_disputes_status` on `status`

---

### 7. Notifications & Events

#### `notifications`
User notifications (push, SMS, email).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Notification ID |
| user_id | UUID | FK(users.id), NOT NULL | Recipient |
| type | ENUM | NOT NULL | push, sms, email |
| channel | ENUM | NOT NULL | booking, payment, message, review, marketing |
| title | VARCHAR(255) | NOT NULL | Notification title |
| body | TEXT | NOT NULL | Notification body |
| data | JSONB | NULL | Additional payload |
| status | ENUM | NOT NULL, DEFAULT 'pending' | pending, sent, failed, read |
| sent_at | TIMESTAMP | NULL | |
| read_at | TIMESTAMP | NULL | |
| error_message | TEXT | NULL | Failure reason |
| created_at | TIMESTAMP | NOT NULL | |

**Indexes**:
- `idx_notifications_user_id` on `user_id`
- `idx_notifications_status` on `status`
- `idx_notifications_created_at` on `created_at DESC`

---

#### `system_events`
Event log for business events (for analytics and automation).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Event ID |
| event_type | VARCHAR(100) | NOT NULL | booking_created, payment_completed, etc. |
| entity_type | VARCHAR(50) | NOT NULL | booking, payment, user, etc. |
| entity_id | UUID | NOT NULL | Entity ID |
| user_id | UUID | FK(users.id), NULL | User who triggered |
| metadata | JSONB | NULL | Event data |
| created_at | TIMESTAMP | NOT NULL | Event timestamp |

**Indexes**:
- `idx_system_events_type` on `event_type`
- `idx_system_events_entity` on `(entity_type, entity_id)`
- `idx_system_events_user_id` on `user_id`
- `idx_system_events_created_at` on `created_at DESC`

---

### 8. Future Tables (Prepared but not implemented in Phase 1)

These tables are designed but will be implemented in later phases:

- `access_control_devices`: Smart lock integration
- `access_codes`: Temporary access codes for bookings
- `loyalty_accounts`: Guest loyalty program
- `loyalty_transactions`: Points accrual/redemption
- `promo_codes`: Marketing discount codes
- `promo_redemptions`: Promo code usage tracking
- `property_verifications`: Inspection records
- `property_documents`: Legal documents

---

## Total Tables in Phase 1: 23 tables

1. users
2. guest_profiles
3. host_profiles
4. kyc_documents
5. properties
6. property_photos
7. amenities
8. property_amenities
9. availability_rules
10. availability_overrides
11. pricing_rules
12. bookings
13. reviews
14. payments
15. payouts
16. refunds
17. transactions
18. support_tickets
19. disputes
20. notifications
21. system_events
22. property_documents (optional in Phase 1)
23. property_verifications (optional in Phase 1)

---

## Enums Defined

```sql
-- User status
CREATE TYPE user_status AS ENUM ('active', 'suspended', 'banned');

-- Business type
CREATE TYPE business_type AS ENUM ('individual', 'business');

-- Verification status
CREATE TYPE verification_status AS ENUM ('unverified', 'pending', 'verified', 'rejected');

-- KYC document types
CREATE TYPE kyc_document_type AS ENUM ('nida', 'passport', 'business_reg', 'tax_cert', 'utility_bill');

-- Document status
CREATE TYPE document_status AS ENUM ('pending', 'approved', 'rejected');

-- Property types
CREATE TYPE property_type AS ENUM ('apartment', 'house', 'room', 'studio', 'villa');

-- Property status
CREATE TYPE property_status AS ENUM ('draft', 'pending_verification', 'verified', 'suspended', 'delisted');

-- Amenity categories
CREATE TYPE amenity_category AS ENUM ('basic', 'kitchen', 'bathroom', 'entertainment', 'safety', 'outdoor');

-- Cancellation policies
CREATE TYPE cancellation_policy AS ENUM ('flexible', 'moderate', 'strict');

-- Booking status
CREATE TYPE booking_status AS ENUM ('pending', 'awaiting_payment', 'confirmed', 'checked_in', 'checked_out', 'completed', 'cancelled', 'no_show');

-- Payment status
CREATE TYPE payment_status_enum AS ENUM ('unpaid', 'partially_paid', 'paid', 'refunded');

-- Payment gateways
CREATE TYPE payment_gateway AS ENUM ('azampay', 'selcom', 'stripe');

-- Payment methods
CREATE TYPE payment_method AS ENUM ('mobile_money', 'card', 'bank_transfer');

-- Transaction status
CREATE TYPE transaction_status AS ENUM ('initiated', 'pending', 'success', 'failed', 'cancelled');

-- Payout status
CREATE TYPE payout_status AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');

-- Payout methods
CREATE TYPE payout_method AS ENUM ('mobile_money', 'bank_transfer');

-- Refund reasons
CREATE TYPE refund_reason AS ENUM ('cancellation', 'dispute', 'damage_waiver', 'system_error');

-- Account types for ledger
CREATE TYPE account_type AS ENUM ('guest_wallet', 'host_wallet', 'platform_wallet', 'gateway_receivable', 'platform_revenue', 'gateway_fees');

-- Reference types
CREATE TYPE reference_type AS ENUM ('payment', 'payout', 'refund', 'booking', 'fee');

-- Pricing rule types
CREATE TYPE pricing_rule_type AS ENUM ('weekly_discount', 'monthly_discount', 'weekend_premium', 'seasonal');

-- Ticket categories
CREATE TYPE ticket_category AS ENUM ('booking_issue', 'payment_issue', 'property_issue', 'account_issue', 'other');

-- Priority levels
CREATE TYPE priority_level AS ENUM ('low', 'medium', 'high', 'urgent');

-- Ticket status
CREATE TYPE ticket_status AS ENUM ('open', 'in_progress', 'waiting_user', 'waiting_admin', 'resolved', 'closed');

-- Dispute types
CREATE TYPE dispute_type AS ENUM ('damage_claim', 'refund_request', 'cancellation_dispute', 'other');

-- Dispute status
CREATE TYPE dispute_status AS ENUM ('open', 'under_review', 'resolved', 'closed');

-- Dispute resolutions
CREATE TYPE dispute_resolution AS ENUM ('approved', 'partial', 'denied');

-- Notification types
CREATE TYPE notification_type AS ENUM ('push', 'sms', 'email');

-- Notification channels
CREATE TYPE notification_channel AS ENUM ('booking', 'payment', 'message', 'review', 'marketing');

-- Notification status
CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed', 'read');
```

---

## Relationships Summary

- **users** ← guest_profiles (1:1)
- **users** ← host_profiles (1:1)
- **users** ← kyc_documents (1:many)
- **users** ← properties (host_id, 1:many)
- **properties** ← property_photos (1:many)
- **properties** ← property_amenities ← amenities (many:many)
- **properties** ← availability_rules (1:many)
- **properties** ← availability_overrides (1:many)
- **properties** ← pricing_rules (1:many)
- **properties** ← bookings (1:many)
- **users** (guest) ← bookings (1:many)
- **bookings** ← reviews (1:1)
- **bookings** ← payments (1:many)
- **bookings** ← disputes (1:many)
- **users** (host) ← payouts (1:many)
- **payments** ← refunds (1:many)

---

*Schema designed for BOMA - Tanzania Short-Stay Rental Marketplace*
*Last updated: November 14, 2025*
