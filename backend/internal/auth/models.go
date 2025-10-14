package auth

import "time"

const (
	// RoleAdmin identifies administrator accounts.
	RoleAdmin = "admin"
	// RoleUser identifies standard user accounts.
	RoleUser = "user"
)

// User represents an application user account.
type User struct {
	ID           int
	Username     string
	PasswordHash string
	Email        *string
	CreatedAt    time.Time
	IsActive     bool
	Role         string
}

// APIKey contains metadata about a stored API key.
type APIKey struct {
	ID           int
	UserID       int
	APIKeyHash   string
	APIKeyPrefix string
	Name         string
	CreatedAt    time.Time
	LastUsedAt   *time.Time
	ExpiresAt    *time.Time
	IsActive     bool
}

// RegisterRequest encapsulates the payload for user registration.
type RegisterRequest struct {
	Username string `json:"username" binding:"required,min=3,max=50"`
	Password string `json:"password" binding:"required,min=6"`
	Email    string `json:"email,omitempty" binding:"omitempty,email"`
}

// LoginRequest encapsulates login credentials.
type LoginRequest struct {
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
}

// CreateAPIKeyRequest is the request payload for API key creation.
type CreateAPIKeyRequest struct {
	Name string `json:"name,omitempty"`
}

// APIKeyResponse contains API key details returned to the client.
type APIKeyResponse struct {
	ID        int       `json:"id"`
	APIKey    string    `json:"api_key"`
	Name      string    `json:"name"`
	Prefix    string    `json:"prefix"`
	CreatedAt time.Time `json:"created_at"`
}

// APIKeyListItem is used when returning a list of API keys (without the secret).
type APIKeyListItem struct {
	ID         int        `json:"id"`
	Name       string     `json:"name"`
	Prefix     string     `json:"prefix"`
	CreatedAt  time.Time  `json:"created_at"`
	LastUsedAt *time.Time `json:"last_used_at,omitempty"`
	IsActive   bool       `json:"is_active"`
}
