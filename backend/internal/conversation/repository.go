package conversation

import (
	"context"
	"database/sql"
	"errors"
	"fmt"
	"time"
)

// ErrConversationNotFound signals that the requested conversation does not exist.
var ErrConversationNotFound = errors.New("conversation not found")

// Repository provides persistence for chat conversations.
type Repository struct {
	db *sql.DB
}

// NewRepository returns a repository backed by the supplied sql.DB handle.
func NewRepository(db *sql.DB) *Repository {
	return &Repository{db: db}
}

// Get loads a conversation ensuring it belongs to the specified user.
func (r *Repository) Get(ctx context.Context, id int64, userID int) (*Conversation, error) {
	const query = `
		SELECT id, user_id, history, COALESCE(new_message, ''), created_at, updated_at
		FROM conversations
		WHERE id = ? AND user_id = ?
	`

	var (
		convo       Conversation
		historyJSON string
	)

	err := r.db.QueryRowContext(ctx, query, id, userID).Scan(
		&convo.ID,
		&convo.UserID,
		&historyJSON,
		&convo.NewMessage,
		&convo.CreatedAt,
		&convo.UpdatedAt,
	)

	if errors.Is(err, sql.ErrNoRows) {
		return nil, ErrConversationNotFound
	}
	if err != nil {
		return nil, fmt.Errorf("query conversation: %w", err)
	}

	turns, err := DeserializeHistory(historyJSON)
	if err != nil {
		return nil, fmt.Errorf("parse history: %w", err)
	}
	convo.History = turns

	return &convo, nil
}

// Save inserts or updates the conversation record.
func (r *Repository) Save(ctx context.Context, convo *Conversation) error {
	historyJSON, err := convo.SerializeHistory()
	if err != nil {
		return err
	}

	now := time.Now().UTC()

	if convo.ID == 0 {
		const insert = `
			INSERT INTO conversations (user_id, history, new_message, created_at, updated_at)
			VALUES (?, ?, ?, ?, ?)
		`
		res, err := r.db.ExecContext(ctx, insert, convo.UserID, historyJSON, convo.NewMessage, now, now)
		if err != nil {
			return fmt.Errorf("insert conversation: %w", err)
		}

		convoID, err := res.LastInsertId()
		if err != nil {
			return fmt.Errorf("fetch conversation id: %w", err)
		}
		convo.ID = convoID
		convo.CreatedAt = now
		convo.UpdatedAt = now
		return nil
	}

	const update = `
		UPDATE conversations
		SET history = ?, new_message = ?, updated_at = ?
		WHERE id = ? AND user_id = ?
	`
	if _, err := r.db.ExecContext(ctx, update, historyJSON, convo.NewMessage, now, convo.ID, convo.UserID); err != nil {
		return fmt.Errorf("update conversation: %w", err)
	}
	convo.UpdatedAt = now
	return nil
}
