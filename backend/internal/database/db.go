package database

import (
	"database/sql"
	"fmt"
	"os"
	"strings"

	_ "github.com/mattn/go-sqlite3"
)

// InitDB initializes the database connection and runs migrations
func InitDB() (*sql.DB, error) {
	dbPath := os.Getenv("DATABASE_PATH")
	if dbPath == "" {
		dbPath = "./data/motoko_coder.db"
	}

	// Ensure the directory exists
	dbDir := strings.TrimSuffix(dbPath, "/motoko_coder.db")
	if err := os.MkdirAll(dbDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create database directory: %w", err)
	}

	db, err := sql.Open("sqlite3", dbPath)
	if err != nil {
		return nil, err
	}

	// Test connection
	if err := db.Ping(); err != nil {
		return nil, err
	}

	// Run migrations
	if err := runMigrations(db); err != nil {
		return nil, err
	}

	return db, nil
}

// runMigrations creates the necessary database tables
func runMigrations(db *sql.DB) error {
	migrations := []string{
		// Users table (full schema)
		`CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			username TEXT UNIQUE NOT NULL,
			password_hash TEXT NOT NULL,
			email TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			is_active BOOLEAN DEFAULT 1,
			role TEXT NOT NULL DEFAULT 'user'
		)`,
		// API Keys table (full schema)
		`CREATE TABLE IF NOT EXISTS api_keys (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			api_key_hash TEXT UNIQUE NOT NULL,
			api_key_prefix TEXT NOT NULL,
			name TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			last_used_at TIMESTAMP,
			expires_at TIMESTAMP,
			is_active BOOLEAN DEFAULT 1,
			FOREIGN KEY (user_id) REFERENCES users(id)
		)`,
		// Ingestion Jobs table
		`CREATE TABLE IF NOT EXISTS ingestion_jobs (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			job_type TEXT NOT NULL,
			status TEXT NOT NULL,
			progress INTEGER DEFAULT 0,
			total_items INTEGER DEFAULT 0,
			processed_items INTEGER DEFAULT 0,
			error_message TEXT,
			started_at TIMESTAMP,
			completed_at TIMESTAMP,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)`,
		// Conversations table for chat history
		`CREATE TABLE IF NOT EXISTS conversations (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			history TEXT NOT NULL DEFAULT '[]',
			new_message TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (user_id) REFERENCES users(id)
		)`,
	}

	for _, migration := range migrations {
		if _, err := db.Exec(migration); err != nil {
			return err
		}
	}

	// Rename old columns if present.
	renameStatements := []string{
		"ALTER TABLE api_keys RENAME COLUMN key_hash TO api_key_hash",
		"ALTER TABLE api_keys RENAME COLUMN key_prefix TO api_key_prefix",
	}

	for _, stmt := range renameStatements {
		if err := tryExec(db, stmt); err != nil {
			return err
		}
	}

	// Backfill missing columns for existing tables.
	columnAdds := []string{
		"ALTER TABLE users ADD COLUMN email TEXT",
		"ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1",
		"ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'user'",
		"ALTER TABLE api_keys ADD COLUMN api_key_hash TEXT",
		"ALTER TABLE api_keys ADD COLUMN api_key_prefix TEXT",
		"ALTER TABLE api_keys ADD COLUMN name TEXT",
		"ALTER TABLE api_keys ADD COLUMN last_used_at TIMESTAMP",
		"ALTER TABLE api_keys ADD COLUMN expires_at TIMESTAMP",
		"ALTER TABLE api_keys ADD COLUMN is_active BOOLEAN DEFAULT 1",
	}

	for _, stmt := range columnAdds {
		if err := tryExec(db, stmt); err != nil {
			return err
		}
	}

	// Ensure NOT NULL + UNIQUE constraints for api_key_hash on legacy tables.
	if err := ensureUniqueConstraint(db, "api_keys", "api_key_hash"); err != nil {
		return err
	}

	return nil
}

func tryExec(db *sql.DB, statement string) error {
	if _, err := db.Exec(statement); err != nil {
		msg := strings.ToLower(err.Error())
		if strings.Contains(msg, "duplicate column name") ||
			strings.Contains(msg, "already exists") ||
			strings.Contains(msg, "no such column") {
			return nil
		}
		return err
	}
	return nil
}

func ensureUniqueConstraint(db *sql.DB, table, column string) error {
	query := fmt.Sprintf(`CREATE UNIQUE INDEX IF NOT EXISTS idx_%s_%s ON %s(%s)`, table, column, table, column)
	_, err := db.Exec(query)
	return err
}
