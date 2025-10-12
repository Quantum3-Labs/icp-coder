package middleware

import (
	"crypto/sha256"
	"database/sql"
	"encoding/base64"
	"encoding/hex"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"github.com/Quantum3-Labs/icp-coder/backend/internal/auth"
)

// BasicAuth middleware for username/password authentication
func BasicAuth(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Authorization header required"})
			c.Abort()
			return
		}

		// Parse Basic Auth header
		const prefix = "Basic "
		if !strings.HasPrefix(authHeader, prefix) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization header"})
			c.Abort()
			return
		}

		decoded, err := base64.StdEncoding.DecodeString(authHeader[len(prefix):])
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid authorization header"})
			c.Abort()
			return
		}

		credentials := strings.SplitN(string(decoded), ":", 2)
		if len(credentials) != 2 {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials format"})
			c.Abort()
			return
		}

		username := credentials[0]
		password := credentials[1]

		user, err := auth.AuthenticateUser(db, username, password)
		if err != nil {
			c.Header("WWW-Authenticate", "Basic realm=Restricted")
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid credentials"})
			c.Abort()
			return
		}

		// Store useful user info in context
		c.Set("username", user.Username)
		c.Set("user_id", user.ID)
		c.Set("user_role", user.Role)

		c.Next()
	}
}

// APIKeyAuth middleware for API key authentication
func APIKeyAuth(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		apiKey := c.GetHeader("x-api-key")
		if apiKey == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "API key required"})
			c.Abort()
			return
		}

		// Hash the API key
		hash := sha256.Sum256([]byte(apiKey))
		keyHash := hex.EncodeToString(hash[:])

		// Verify API key exists and is valid
		var keyID, userID int
		var expiresAt sql.NullTime
		err := db.QueryRow(`
			SELECT id, user_id, expires_at
			FROM api_keys
			WHERE api_key_hash = ?
		`, keyHash).Scan(&keyID, &userID, &expiresAt)

		if err == sql.ErrNoRows {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Invalid API key"})
			c.Abort()
			return
		}
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Database error"})
			c.Abort()
			return
		}

		// Check if key is expired
		if expiresAt.Valid && expiresAt.Time.Before(time.Now()) {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "API key expired"})
			c.Abort()
			return
		}

		// Update last_used_at
		_, _ = db.Exec(`UPDATE api_keys SET last_used_at = ? WHERE id = ?`, time.Now(), keyID)

		// Store user_id in context for handlers to use
		c.Set("user_id", userID)
		c.Set("api_key_id", keyID)

		c.Next()
	}
}

// RequireRole ensures the authenticated user has the specified role.
func RequireRole(role string) gin.HandlerFunc {
	return func(c *gin.Context) {
		roleValue, exists := c.Get("user_role")
		if !exists {
			c.JSON(http.StatusForbidden, gin.H{"error": "insufficient permissions"})
			c.Abort()
			return
		}

		roleStr, ok := roleValue.(string)
		if !ok || roleStr != role {
			c.JSON(http.StatusForbidden, gin.H{"error": "insufficient permissions"})
			c.Abort()
			return
		}

		c.Next()
	}
}
