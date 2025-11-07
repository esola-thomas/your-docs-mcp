---
title: "API Authentication"
tags: ["api", "authentication", "security", "auth", "oauth", "jwt"]
category: "API Reference"
order: 1
---

# API Authentication

Learn how to authenticate with the API and secure your requests.

## Overview

The API supports multiple authentication methods:

- **API Keys**: Simple key-based authentication
- **OAuth 2.0**: Industry-standard authorization framework
- **JWT Tokens**: Stateless authentication with JSON Web Tokens

## API Keys

The simplest authentication method for server-to-server communication.

### Getting an API Key

1. Log into your account dashboard
2. Navigate to Settings > API Keys
3. Click "Generate New API Key"
4. Copy and securely store your key

### Using API Keys

Include the API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.example.com/v1/users
```

### API Key Best Practices

- Never commit API keys to version control
- Rotate keys regularly (every 90 days)
- Use different keys for different environments
- Store keys in environment variables

```bash
# Store in environment
export API_KEY=your_api_key_here

# Use in requests
curl -H "Authorization: Bearer $API_KEY" \
  https://api.example.com/v1/users
```

## OAuth 2.0

For web applications that need user-delegated access.

### Authorization Flow

1. **User Authorization**: Redirect user to authorization endpoint
2. **Callback**: Receive authorization code via callback URL
3. **Token Exchange**: Exchange code for access token
4. **API Access**: Use access token for API requests

### Example: Authorization Code Flow

```javascript
// Step 1: Redirect to authorization endpoint
const authUrl = 'https://api.example.com/oauth/authorize?' +
  'client_id=YOUR_CLIENT_ID&' +
  'redirect_uri=https://yourapp.com/callback&' +
  'response_type=code&' +
  'scope=read write';

window.location.href = authUrl;

// Step 2: Handle callback
// User is redirected to: https://yourapp.com/callback?code=AUTH_CODE

// Step 3: Exchange code for token
const response = await fetch('https://api.example.com/oauth/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    grant_type: 'authorization_code',
    code: 'AUTH_CODE',
    client_id: 'YOUR_CLIENT_ID',
    client_secret: 'YOUR_CLIENT_SECRET',
    redirect_uri: 'https://yourapp.com/callback'
  })
});

const { access_token, refresh_token } = await response.json();

// Step 4: Use access token
const apiResponse = await fetch('https://api.example.com/v1/users', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Refresh Tokens

Access tokens expire after 1 hour. Use refresh tokens to get new access tokens:

```javascript
const response = await fetch('https://api.example.com/oauth/token', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    grant_type: 'refresh_token',
    refresh_token: 'YOUR_REFRESH_TOKEN',
    client_id: 'YOUR_CLIENT_ID',
    client_secret: 'YOUR_CLIENT_SECRET'
  })
});

const { access_token } = await response.json();
```

## JWT Tokens

For stateless authentication in microservices architectures.

### Getting a JWT

Authenticate with credentials to receive a JWT:

```bash
curl -X POST https://api.example.com/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user@example.com",
    "password": "your_password"
  }'
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2024-12-31T23:59:59Z",
  "refresh_token": "refresh_token_here"
}
```

### Using JWTs

Include the JWT in the Authorization header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  https://api.example.com/v1/users
```

### Token Validation

Tokens are validated on each request. If expired, you'll receive:

```json
{
  "error": "token_expired",
  "message": "The access token has expired",
  "code": 401
}
```

Use the refresh token to get a new access token.

## Security Best Practices

### Secure Storage

- **Browser**: Use httpOnly cookies for tokens
- **Mobile**: Use secure keychain/keystore
- **Server**: Use environment variables or secret managers

### Token Handling

```javascript
// Good: Store in httpOnly cookie
document.cookie = `token=${jwt}; Secure; HttpOnly; SameSite=Strict`;

// Bad: Store in localStorage (vulnerable to XSS)
localStorage.setItem('token', jwt);
```

### HTTPS Only

Always use HTTPS for API requests. Never send credentials over HTTP.

### Rate Limiting

The API enforces rate limits per authentication method:

- **API Keys**: 1000 requests/hour
- **OAuth**: 5000 requests/hour
- **JWT**: 2000 requests/hour

## Error Handling

### Common Authentication Errors

| Status Code | Error | Description |
|-------------|-------|-------------|
| 401 | `invalid_token` | Token is malformed or invalid |
| 401 | `token_expired` | Token has expired |
| 401 | `invalid_credentials` | Username or password incorrect |
| 403 | `insufficient_scope` | Token lacks required permissions |
| 429 | `rate_limit_exceeded` | Too many requests |

### Example Error Response

```json
{
  "error": "invalid_token",
  "message": "The provided token is invalid or has expired",
  "code": 401,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Testing Authentication

### Using cURL

```bash
# Test API key
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.example.com/v1/auth/verify

# Test JWT
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.example.com/v1/auth/verify
```

## Expected Response

```json
{
  "authenticated": true,
  "user_id": "12345",
  "scopes": ["read", "write"],
  "expires_at": "2024-12-31T23:59:59Z"
}
```

## Next Steps

- Explore [API Endpoints](endpoints.md) for available operations
- Review [OpenAPI Specification](openapi.yaml) for complete API reference
- Learn about [Rate Limiting and Quotas](#) in the API guide
