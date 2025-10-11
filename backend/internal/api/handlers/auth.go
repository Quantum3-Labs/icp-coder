package handlers

import (
	"database/sql"
	"errors"
	"io"
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"

	"github.com/Quantum3-Labs/icp-coder/backend/internal/auth"
)

// Register handles user registration
// @Summary Register a new user
// @Description Create a new user account with default user role
// @Tags Authentication
// @Accept json
// @Produce json
// @Param request body auth.RegisterRequest true "User registration details"
// @Success 201 {object} map[string]interface{} "User created successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request"
// @Router /auth/register [post]
func Register(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req auth.RegisterRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		var email *string
		if req.Email != "" {
			email = &req.Email
		}

		// All new users are created with "user" role by default
		userID, err := auth.CreateUser(db, req.Username, req.Password, email, auth.RoleUser)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusCreated, gin.H{
			"success": true,
			"message": "User created successfully",
			"user_id": userID,
			"role":    auth.RoleUser,
		})
	}
}

// Login handles user login
// @Summary Login user
// @Description Authenticate user with username and password
// @Tags Authentication
// @Accept json
// @Produce json
// @Param request body auth.LoginRequest true "Login credentials"
// @Success 200 {object} map[string]interface{} "Authentication successful"
// @Failure 400 {object} map[string]interface{} "Invalid request"
// @Failure 401 {object} map[string]interface{} "Invalid credentials"
// @Router /auth/login [post]
func Login(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req auth.LoginRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		user, err := auth.AuthenticateUser(db, req.Username, req.Password)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"success":  true,
			"message":  "Authentication successful",
			"user_id":  user.ID,
			"username": user.Username,
		})
	}
}

// CreateAPIKey generates a new API key for the user
// @Summary Create API key
// @Description Generate a new API key for the authenticated user
// @Tags API Keys
// @Accept json
// @Produce json
// @Security BasicAuth
// @Param request body auth.CreateAPIKeyRequest false "API key name (optional)"
// @Success 201 {object} map[string]interface{} "API key created successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 500 {object} map[string]interface{} "Internal server error"
// @Router /auth/keys [post]
func CreateAPIKey(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		userIDValue, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			return
		}

		userID, ok := userIDValue.(int)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid user context"})
			return
		}

		var req auth.CreateAPIKeyRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			if !errors.Is(err, io.EOF) {
				c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
				return
			}
			req.Name = ""
		}

		apiKeyResp, err := auth.CreateAPIKey(db, userID, req.Name)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusCreated, gin.H{
			"success": true,
			"message": "API key created successfully",
			"api_key": apiKeyResp.APIKey,
			"name":    apiKeyResp.Name,
			"prefix":  apiKeyResp.Prefix,
		})
	}
}

// ListAPIKeys returns all API keys for the user
// @Summary List API keys
// @Description Get all API keys for the authenticated user
// @Tags API Keys
// @Accept json
// @Produce json
// @Security BasicAuth
// @Success 200 {array} auth.APIKeyListItem "List of API keys"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Failure 500 {object} map[string]interface{} "Internal server error"
// @Router /auth/keys [get]
func ListAPIKeys(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		userIDValue, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			return
		}

		userID, ok := userIDValue.(int)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid user context"})
			return
		}

		keys, err := auth.GetUserAPIKeys(db, userID)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, keys)
	}
}

// RevokeAPIKey revokes an API key
// @Summary Revoke API key
// @Description Permanently revoke/delete an API key
// @Tags API Keys
// @Accept json
// @Produce json
// @Security BasicAuth
// @Param id path int true "API Key ID"
// @Success 200 {object} map[string]interface{} "API key revoked successfully"
// @Failure 400 {object} map[string]interface{} "Invalid request"
// @Failure 401 {object} map[string]interface{} "Unauthorized"
// @Router /auth/keys/{id} [delete]
func RevokeAPIKey(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		userIDValue, exists := c.Get("user_id")
		if !exists {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized"})
			return
		}

		userID, ok := userIDValue.(int)
		if !ok {
			c.JSON(http.StatusInternalServerError, gin.H{"error": "Invalid user context"})
			return
		}

		keyIDStr := c.Param("id")
		keyID, err := strconv.Atoi(keyIDStr)
		if err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid API key ID"})
			return
		}

		if err := auth.RevokeAPIKey(db, userID, keyID); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"success": true,
			"message": "API key revoked successfully",
		})
	}
}
