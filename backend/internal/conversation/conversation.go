package conversation

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
	"unicode"
)

// Turn represents a single exchange in the conversation.
type Turn struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// Conversation captures the state of a chat between a user and the assistant.
type Conversation struct {
	ID         int64
	UserID     int
	History    []Turn
	NewMessage string
	CreatedAt  time.Time
	UpdatedAt  time.Time
}

// New returns a conversation initialised for the supplied user.
func New(userID int) *Conversation {
	return &Conversation{
		UserID:  userID,
		History: make([]Turn, 0),
	}
}

// AddTurn appends a turn to the conversation history.
func (c *Conversation) AddTurn(role, content string) {
	c.History = append(c.History, Turn{
		Role:    role,
		Content: content,
	})
}

// SerializeHistory marshals the conversation history to a JSON string.
func (c *Conversation) SerializeHistory() (string, error) {
	data, err := json.Marshal(c.History)
	if err != nil {
		return "", fmt.Errorf("marshal history: %w", err)
	}
	return string(data), nil
}

// DeserializeHistory converts a JSON string into conversation turns.
func DeserializeHistory(history string) ([]Turn, error) {
	if strings.TrimSpace(history) == "" {
		return []Turn{}, nil
	}
	var turns []Turn
	if err := json.Unmarshal([]byte(history), &turns); err != nil {
		return nil, fmt.Errorf("unmarshal history: %w", err)
	}
	return turns, nil
}

// BuildHistoryPrompt renders the conversation history into a readable prompt segment.
func (c *Conversation) BuildHistoryPrompt() string {
	if len(c.History) == 0 {
		return ""
	}

	var builder strings.Builder
	builder.WriteString("Previous conversation:\n")
	for _, turn := range c.History {
		builder.WriteString(fmt.Sprintf("%s: %s\n", capitaliseRole(turn.Role), turn.Content))
	}
	builder.WriteString("\n")
	return builder.String()
}

func capitaliseRole(role string) string {
	if role == "" {
		return role
	}
	runes := []rune(role)
	runes[0] = unicode.ToUpper(runes[0])
	return string(runes)
}
