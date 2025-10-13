package auth

import (
	"crypto/rand"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"errors"
	"math/big"
	"time"

	"golang.org/x/crypto/bcrypt"
)

const (
	apiKeyCharset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
	apiKeyLength  = 32
	apiKeyPrefix  = "mk_"
)

// HashPassword hashes a password using bcrypt.
func HashPassword(password string) (string, error) {
	hashed, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return "", err
	}
	return string(hashed), nil
}

// GenerateAPIKey returns a random API key with the configured prefix.
func GenerateAPIKey() (string, error) {
	buf := make([]byte, apiKeyLength)
	for i := range buf {
		num, err := rand.Int(rand.Reader, big.NewInt(int64(len(apiKeyCharset))))
		if err != nil {
			return "", err
		}
		buf[i] = apiKeyCharset[num.Int64()]
	}

	return apiKeyPrefix + string(buf), nil
}

// HashAPIKey hashes the plain-text API key for storage.
func HashAPIKey(apiKey string) string {
	hash := sha256.Sum256([]byte(apiKey))
	return hex.EncodeToString(hash[:])
}

// GetAPIKeyPrefix returns the prefix that can be shown to the user.
func GetAPIKeyPrefix(apiKey string) string {
	if len(apiKey) < 8 {
		return apiKey
	}
	return apiKey[:8]
}

// CreateUser creates a new user record after validating and hashing credentials.
func CreateUser(db *sql.DB, username, password string, email *string, role string) (int, error) {
	if len(username) < 3 {
		return 0, errors.New("username must be at least 3 characters")
	}
	if len(password) < 6 {
		return 0, errors.New("password must be at least 6 characters")
	}

	if role == "" {
		role = RoleUser
	}
	if role != RoleUser && role != RoleAdmin {
		return 0, errors.New("invalid role")
	}

	var exists bool
	err := db.QueryRow("SELECT EXISTS(SELECT 1 FROM users WHERE username = ?)", username).Scan(&exists)
	if err != nil {
		return 0, err
	}
	if exists {
		return 0, errors.New("username already exists")
	}

	passwordHash, err := HashPassword(password)
	if err != nil {
		return 0, err
	}
	result, err := db.Exec(`
		INSERT INTO users (username, password_hash, email, role)
		VALUES (?, ?, ?, ?)
	`, username, passwordHash, email, role)
	if err != nil {
		return 0, err
	}

	userID, err := result.LastInsertId()
	if err != nil {
		return 0, err
	}

	return int(userID), nil
}

// AuthenticateUser validates the provided credentials and returns the user.
func AuthenticateUser(db *sql.DB, username, password string) (*User, error) {
	var user User
	err := db.QueryRow(`
		SELECT id, username, password_hash, email, created_at, is_active, role
		FROM users
		WHERE username = ? AND is_active = 1
	`, username).Scan(
		&user.ID,
		&user.Username,
		&user.PasswordHash,
		&user.Email,
		&user.CreatedAt,
		&user.IsActive,
		&user.Role,
	)

	if err == sql.ErrNoRows {
		return nil, errors.New("invalid username or password")
	}
	if err != nil {
		return nil, err
	}

	if err := bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password)); err != nil {
		return nil, errors.New("invalid username or password")
	}

	user.PasswordHash = ""
	return &user, nil
}

// CreateAPIKey creates a new API key for the given user.
func CreateAPIKey(db *sql.DB, userID int, name string) (*APIKeyResponse, error) {
	var (
		apiKey string
		err    error
	)

	for attempt := 0; attempt < 10; attempt++ {
		apiKey, err = GenerateAPIKey()
		if err != nil {
			return nil, err
		}

		keyHash := HashAPIKey(apiKey)
		var exists bool
		err = db.QueryRow("SELECT EXISTS(SELECT 1 FROM api_keys WHERE api_key_hash = ?)", keyHash).Scan(&exists)
		if err != nil {
			return nil, err
		}
		if !exists {
			break
		}

		if attempt == 9 {
			return nil, errors.New("failed to generate unique API key")
		}
	}

	if name == "" {
		name = "API Key " + time.Now().Format("2006-01-02 15:04")
	}

	keyHash := HashAPIKey(apiKey)
	keyPrefix := GetAPIKeyPrefix(apiKey)

	result, err := db.Exec(`
		INSERT INTO api_keys (user_id, api_key_hash, api_key_prefix, name)
		VALUES (?, ?, ?, ?)
	`, userID, keyHash, keyPrefix, name)
	if err != nil {
		return nil, err
	}

	keyID, err := result.LastInsertId()
	if err != nil {
		return nil, err
	}

	return &APIKeyResponse{
		ID:        int(keyID),
		APIKey:    apiKey,
		Name:      name,
		Prefix:    keyPrefix,
		CreatedAt: time.Now(),
	}, nil
}

// ValidateAPIKey verifies the provided API key and returns the associated user ID.
func ValidateAPIKey(db *sql.DB, apiKey string) (int, error) {
	keyHash := HashAPIKey(apiKey)

	var (
		userID    int
		isActive  bool
		expiresAt sql.NullTime
	)

	err := db.QueryRow(`
		SELECT user_id, is_active, expires_at
		FROM api_keys
		WHERE api_key_hash = ?
	`, keyHash).Scan(&userID, &isActive, &expiresAt)
	if err == sql.ErrNoRows {
		return 0, errors.New("invalid API key")
	}
	if err != nil {
		return 0, err
	}

	if !isActive {
		return 0, errors.New("API key has been revoked")
	}

	if expiresAt.Valid && expiresAt.Time.Before(time.Now()) {
		return 0, errors.New("API key has expired")
	}

	_, _ = db.Exec("UPDATE api_keys SET last_used_at = ? WHERE api_key_hash = ?", time.Now(), keyHash)

	return userID, nil
}

// CompareAPIKey checks whether the provided key matches an active key for the user.
func CompareAPIKey(db *sql.DB, userID int, apiKey string) (bool, error) {
	if apiKey == "" {
		return false, errors.New("API key cannot be empty")
	}

	keyHash := HashAPIKey(apiKey)

	var exists bool
	err := db.QueryRow(`
		SELECT EXISTS(
			SELECT 1
			FROM api_keys
			WHERE user_id = ? AND api_key_hash = ? AND is_active = 1
		)
	`, userID, keyHash).Scan(&exists)
	if err != nil {
		return false, err
	}

	return exists, nil
}

// GetUserAPIKeys returns the active API keys owned by the user.
func GetUserAPIKeys(db *sql.DB, userID int) ([]APIKeyListItem, error) {
	rows, err := db.Query(`
		SELECT id, name, api_key_prefix, created_at, last_used_at, is_active
		FROM api_keys
		WHERE user_id = ? AND is_active = 1
		ORDER BY created_at DESC
	`, userID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var keys []APIKeyListItem
	for rows.Next() {
		var key APIKeyListItem
		if err := rows.Scan(&key.ID, &key.Name, &key.Prefix, &key.CreatedAt, &key.LastUsedAt, &key.IsActive); err != nil {
			return nil, err
		}
		keys = append(keys, key)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return keys, nil
}

// RevokeAPIKey marks the specified API key as inactive for the user.
func RevokeAPIKey(db *sql.DB, userID, keyID int) error {
	result, err := db.Exec(`
		UPDATE api_keys
		SET is_active = 0
		WHERE id = ? AND user_id = ?
	`, keyID, userID)
	if err != nil {
		return err
	}

	rowsAffected, err := result.RowsAffected()
	if err != nil {
		return err
	}

	if rowsAffected == 0 {
		return errors.New("API key not found or not owned by user")
	}

	return nil
}
