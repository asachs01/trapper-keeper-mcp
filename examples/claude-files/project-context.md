# Example CLAUDE.md File

This is an example CLAUDE.md file showing how Trapper Keeper can help organize large context files.

## 🏗️ Architecture

### System Overview
Our application follows a microservices architecture with the following key components:

- **API Gateway**: Routes requests to appropriate services
- **Authentication Service**: Handles user authentication and JWT token generation
- **User Service**: Manages user profiles and preferences
- **Payment Service**: Processes payments through Stripe and PayPal
- **Notification Service**: Sends emails, SMS, and push notifications

### Design Patterns
We implement several design patterns throughout the codebase:

- **Repository Pattern**: All data access goes through repository interfaces
- **Observer Pattern**: Used for real-time event notifications
- **Factory Pattern**: Creating service instances based on configuration
- **Strategy Pattern**: Payment processing with multiple providers

### Technology Stack
- **Backend**: Node.js with TypeScript
- **Database**: PostgreSQL for relational data, Redis for caching
- **Message Queue**: RabbitMQ for async communication
- **Container**: Docker with Kubernetes orchestration

## 🔐 Security

### Authentication Flow
1. User submits credentials to `/auth/login`
2. Credentials verified against database (bcrypt)
3. JWT token generated with user claims
4. Token returned with refresh token
5. Client includes token in Authorization header

### Security Measures
- **Password Requirements**: Minimum 12 characters, complexity rules
- **Rate Limiting**: 5 login attempts per 15 minutes
- **Session Management**: Tokens expire after 1 hour
- **2FA Support**: TOTP-based two-factor authentication
- **API Keys**: Separate keys for different environments

### Vulnerability Management
Regular security audits conducted quarterly. All dependencies scanned with:
- npm audit for Node.js packages
- Trivy for container scanning
- OWASP ZAP for API testing

## ✅ Features

### User Management
Complete user lifecycle management including:

- **Registration**: Email verification required
- **Profile Management**: Avatar upload, preferences
- **Password Reset**: Secure token-based reset flow
- **Account Deletion**: GDPR-compliant data removal

### Payment Processing
Multiple payment methods supported:

- **Credit Cards**: Stripe integration with PCI compliance
- **PayPal**: Express checkout and subscriptions
- **Invoicing**: PDF generation and email delivery
- **Refunds**: Automated refund processing

### Real-time Features
WebSocket-based real-time updates:

- **Live Notifications**: Instant push notifications
- **Presence System**: Online/offline status
- **Collaborative Editing**: Multiple users can edit simultaneously
- **Live Analytics**: Real-time dashboard updates

## 🌐 API

### RESTful Endpoints

#### User Endpoints
```
GET    /api/users          - List all users (admin only)
POST   /api/users          - Create new user
GET    /api/users/:id      - Get user details
PUT    /api/users/:id      - Update user
DELETE /api/users/:id      - Delete user
GET    /api/users/me       - Get current user
```

#### Payment Endpoints
```
POST   /api/payments/charge      - Process payment
POST   /api/payments/subscribe   - Create subscription
DELETE /api/payments/subscribe   - Cancel subscription
GET    /api/payments/history     - Payment history
POST   /api/payments/refund      - Process refund
```

### GraphQL API
Alternative GraphQL endpoint at `/graphql`:

```graphql
type Query {
  user(id: ID!): User
  users(limit: Int, offset: Int): [User!]!
  currentUser: User
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
  deleteUser(id: ID!): Boolean!
}
```

### Webhooks
Configurable webhooks for events:
- `user.created`
- `user.updated`
- `payment.completed`
- `subscription.cancelled`

## 📋 Setup

### Prerequisites
- Node.js 18+ (use nvm for version management)
- PostgreSQL 14+
- Redis 6+
- Docker and Docker Compose
- Git

### Environment Variables
Create `.env` file with:
```
NODE_ENV=development
PORT=3000
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-secret-key
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Installation Steps
1. Clone repository: `git clone <repo-url>`
2. Install dependencies: `npm install`
3. Set up database: `npm run db:setup`
4. Run migrations: `npm run db:migrate`
5. Seed data: `npm run db:seed`
6. Start server: `npm run dev`

### Docker Setup
```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🧪 Testing

### Test Strategy
We maintain high test coverage with:
- Unit tests for business logic
- Integration tests for API endpoints
- E2E tests for critical user flows
- Performance tests for load scenarios

### Running Tests
```bash
# Unit tests
npm run test:unit

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# All tests with coverage
npm run test:coverage

# Watch mode
npm run test:watch
```

### Test Configuration
- **Test Framework**: Jest with TypeScript
- **API Testing**: Supertest
- **E2E Testing**: Playwright
- **Mocking**: MSW for API mocking
- **Coverage Target**: 80% minimum

## ⚡ Performance

### Optimization Strategies
- **Database Indexing**: Indexes on frequently queried fields
- **Query Optimization**: N+1 query prevention
- **Caching Strategy**: Redis for session and API responses
- **CDN Integration**: Static assets served via CloudFront
- **Code Splitting**: Lazy loading for frontend modules

### Performance Metrics
Target metrics:
- API Response Time: < 200ms (p95)
- Database Queries: < 50ms average
- Cache Hit Rate: > 90%
- Error Rate: < 0.1%

### Monitoring
- **APM**: New Relic for application monitoring
- **Logging**: ELK stack (Elasticsearch, Logstash, Kibana)
- **Metrics**: Prometheus with Grafana dashboards
- **Alerts**: PagerDuty integration for critical issues

## 🚀 Deployment

### CI/CD Pipeline
GitHub Actions workflow:
1. Run tests on PR
2. Build Docker images
3. Deploy to staging
4. Run E2E tests
5. Deploy to production (manual approval)

### Environments
- **Development**: Local development
- **Staging**: https://staging.example.com
- **Production**: https://api.example.com

### Deployment Checklist
- [ ] All tests passing
- [ ] Database migrations reviewed
- [ ] Environment variables updated
- [ ] Feature flags configured
- [ ] Monitoring alerts set up
- [ ] Rollback plan documented

### Rollback Procedure
1. Identify issue in monitoring
2. Trigger rollback in CI/CD
3. Verify previous version deployed
4. Investigate root cause
5. Implement fix and redeploy

## 📚 Documentation

### API Documentation
- Swagger UI: https://api.example.com/docs
- Postman Collection: [Download](./postman-collection.json)
- API Changelog: [CHANGELOG.md](./CHANGELOG.md)

### Developer Guides
- [Contributing Guide](./CONTRIBUTING.md)
- [Code Style Guide](./docs/style-guide.md)
- [Architecture Decision Records](./docs/adr/)

### Support Resources
- Internal Wiki: https://wiki.example.com
- Slack Channel: #dev-support
- Office Hours: Thursdays 2-3 PM

---

This file tends to grow large over time. Use Trapper Keeper to organize it into manageable sections!