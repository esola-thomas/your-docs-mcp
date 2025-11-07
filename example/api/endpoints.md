---
title: API Endpoints Reference
tags: [api, endpoints, reference, rest]
category: "API Reference"
order: 2
---

# API Endpoints Reference

Complete reference for all available API endpoints.

## Base URL

All API requests should be made to:

```text
https://api.example.com/v1
```

## Authentication

All endpoints require authentication unless marked as public. See [Authentication Guide](authentication.md) for details.

## Users

### List Users

Get a paginated list of users.

**Endpoint:** `GET /users`

**Authentication:** Required

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Results per page (default: 20, max: 100) |
| `sort` | string | No | Sort field (default: created_at) |
| `order` | string | No | Sort order: `asc` or `desc` (default: desc) |

**Example Request:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/v1/users?page=1&limit=20"
```

**Example Response:**

```json
{
  "data": [
    {
      "id": "usr_1234567890",
      "email": "user@example.com",
      "name": "John Doe",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Get User

Retrieve a specific user by ID.

**Endpoint:** `GET /users/{user_id}`

**Authentication:** Required

**Example Request:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.example.com/v1/users/usr_1234567890
```

**Example Response:**

```json
{
  "id": "usr_1234567890",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "https://example.com/avatars/user.jpg",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "plan": "pro",
    "verified": true
  }
}
```

### Create User

Create a new user account.

**Endpoint:** `POST /users`

**Authentication:** Admin only

**Request Body:**

```json
{
  "email": "newuser@example.com",
  "name": "Jane Smith",
  "password": "secure_password_here",
  "metadata": {
    "plan": "free"
  }
}
```

**Example Response:**

```json
{
  "id": "usr_0987654321",
  "email": "newuser@example.com",
  "name": "Jane Smith",
  "created_at": "2024-01-15T11:00:00Z",
  "updated_at": "2024-01-15T11:00:00Z"
}
```

### Update User

Update an existing user.

**Endpoint:** `PATCH /users/{user_id}`

**Authentication:** Required (self or admin)

**Request Body:**

```json
{
  "name": "Jane Doe",
  "metadata": {
    "plan": "pro"
  }
}
```

**Example Response:**

```json
{
  "id": "usr_0987654321",
  "email": "newuser@example.com",
  "name": "Jane Doe",
  "updated_at": "2024-01-15T11:30:00Z"
}
```

### Delete User

Delete a user account.

**Endpoint:** `DELETE /users/{user_id}`

**Authentication:** Admin only

**Example Request:**

```bash
curl -X DELETE \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.example.com/v1/users/usr_1234567890
```

**Example Response:**

```json
{
  "deleted": true,
  "id": "usr_1234567890"
}
```

## Documents

### List Documents

Get all documents accessible to the authenticated user.

**Endpoint:** `GET /documents`

**Authentication:** Required

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `limit` | integer | No | Results per page (default: 20) |
| `category` | string | No | Filter by category |
| `tags` | string | No | Comma-separated tags |

**Example Request:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/v1/documents?category=guides&tags=tutorial,beginner"
```

### Search Documents

Full-text search across all documents.

**Endpoint:** `GET /documents/search`

**Authentication:** Required

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `q` | string | Yes | Search query |
| `limit` | integer | No | Max results (default: 10) |
| `category` | string | No | Filter by category |

**Example Request:**

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://api.example.com/v1/documents/search?q=authentication&limit=5"
```

**Example Response:**

```json
{
  "results": [
    {
      "id": "doc_123",
      "title": "API Authentication",
      "excerpt": "Learn how to authenticate with the API...",
      "category": "api",
      "tags": ["api", "authentication", "security"],
      "score": 0.95,
      "url": "docs://api/authentication"
    }
  ],
  "total": 3,
  "query": "authentication"
}
```

## Projects

### List Projects

Get all projects for the authenticated user.

**Endpoint:** `GET /projects`

**Authentication:** Required

**Example Response:**

```json
{
  "data": [
    {
      "id": "prj_123456",
      "name": "My Project",
      "description": "A sample project",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:00:00Z",
      "owner": {
        "id": "usr_1234567890",
        "name": "John Doe"
      }
    }
  ]
}
```

### Create Project

Create a new project.

**Endpoint:** `POST /projects`

**Authentication:** Required

**Request Body:**

```json
{
  "name": "New Project",
  "description": "Project description here",
  "settings": {
    "public": false,
    "collaborators": ["usr_0987654321"]
  }
}
```

## Webhooks

### List Webhooks

Get all configured webhooks.

**Endpoint:** `GET /webhooks`

**Authentication:** Required

### Create Webhook

Register a new webhook endpoint.

**Endpoint:** `POST /webhooks`

**Request Body:**

```json
{
  "url": "https://yourapp.com/webhooks",
  "events": ["user.created", "document.updated"],
  "secret": "webhook_secret_here"
}
```

## Rate Limits

All endpoints are subject to rate limiting. Current limits:

- **Standard**: 1000 requests/hour
- **Premium**: 5000 requests/hour
- **Enterprise**: 10000 requests/hour

Rate limit information is included in response headers:

```text
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640000000
```

## Error Responses

All endpoints return errors in a consistent format:

```json
{
  "error": "resource_not_found",
  "message": "The requested user was not found",
  "code": 404,
  "details": {
    "resource_type": "user",
    "resource_id": "usr_invalid"
  }
}
```

### Common Error Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | `bad_request` | Invalid request parameters |
| 401 | `unauthorized` | Authentication required |
| 403 | `forbidden` | Insufficient permissions |
| 404 | `not_found` | Resource not found |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Server error |

## Pagination

List endpoints support pagination using page and limit parameters:

```bash
GET /users?page=2&limit=50
```

Pagination metadata is included in responses:

```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 50,
    "total": 150,
    "pages": 3,
    "has_next": true,
    "has_prev": true
  }
}
```

## Next Steps

- Review [Authentication Guide](authentication.md) for auth details
- Download the [OpenAPI Specification](openapi.yaml)
- Explore [Code Examples](#) in various languages
