package handlers

import (
	"database/sql"
	"errors"
	"log"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"

	"github.com/Quantum3-Labs/icp-coder/backend/internal/codegen"
	"github.com/Quantum3-Labs/icp-coder/backend/internal/conversation"
)

// ChatMessage represents a message in the chat
type ChatMessage struct {
	Role    string `json:"role" binding:"required"`
	Content string `json:"content" binding:"required"`
}

// ChatCompletionRequest represents an OpenAI-compatible chat completion request
type ChatCompletionRequest struct {
	Model          string        `json:"model"`
	Messages       []ChatMessage `json:"messages" binding:"required"`
	Temperature    float64       `json:"temperature"`
	MaxTokens      int           `json:"max_tokens"`
	ConversationID *int64        `json:"conversation_id,omitempty"`
}

// ChatCompletionResponse represents an OpenAI-compatible chat completion response
type ChatCompletionResponse struct {
	ID             string                 `json:"id"`
	Object         string                 `json:"object"`
	Created        int64                  `json:"created"`
	Model          string                 `json:"model"`
	Choices        []ChatCompletionChoice `json:"choices"`
	Usage          ChatCompletionUsage    `json:"usage"`
	ConversationID int64                  `json:"conversation_id,omitempty"`
}

// ChatCompletionChoice represents a choice in the chat completion response
type ChatCompletionChoice struct {
	Index        int         `json:"index"`
	Message      ChatMessage `json:"message"`
	FinishReason string      `json:"finish_reason"`
}

// ChatCompletionUsage represents token usage information
type ChatCompletionUsage struct {
	PromptTokens     int `json:"prompt_tokens"`
	CompletionTokens int `json:"completion_tokens"`
	TotalTokens      int `json:"total_tokens"`
}

// ChatCompletions handles OpenAI-compatible chat completion requests
func ChatCompletions(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req ChatCompletionRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "Invalid request: " + err.Error(),
			})
			return
		}

		// Validate messages
		if len(req.Messages) == 0 {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "At least one message is required",
			})
			return
		}

		// Extract the last user message as the query
		var query string
		for i := len(req.Messages) - 1; i >= 0; i-- {
			if req.Messages[i].Role == "user" {
				query = req.Messages[i].Content
				break
			}
		}

		if query == "" {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "No user message found in messages array",
			})
			return
		}

		userID, ok := extractUserID(c)
		if !ok {
			c.JSON(http.StatusUnauthorized, gin.H{
				"error": "Unable to resolve authenticated user",
			})
			return
		}

		repo := conversation.NewRepository(db)
		convo, err := loadConversation(c, repo, req.ConversationID, userID)
		if err != nil {
			if errors.Is(err, conversation.ErrConversationNotFound) {
				c.JSON(http.StatusNotFound, gin.H{
					"error": "Conversation not found",
				})
				return
			}
			log.Printf("Failed to load conversation: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to load conversation",
			})
			return
		}

		convo.NewMessage = query
		conversationAwareQuery := buildConversationAwareQuery(convo, query)

		// Get services
		ragService, err := getRAGService()
		if err != nil {
			log.Printf("Failed to initialize RAG service: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to initialize RAG service: " + err.Error(),
			})
			return
		}

		// Step 1: Retrieve context from ChromaDB
		ragResponse, err := ragService.RetrieveContext(c.Request.Context(), query, 5)
		if err != nil {
			log.Printf("Failed to retrieve context: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to retrieve context: " + err.Error(),
			})
			return
		}

		provider := codegen.ProviderFromEnv()
		codegenService, err := getCodegenService(provider)
		if err != nil {
			log.Printf("Failed to initialize %s service: %v", provider, err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to initialize code generation service: " + err.Error(),
			})
			return
		}

		// Step 2: Generate response using configured provider with context
		codeGenResponse, err := codegenService.GenerateCode(
			c.Request.Context(),
			conversationAwareQuery,
			ragResponse.CodeContexts,
			req.Temperature,
			req.MaxTokens,
		)
		if err != nil {
			log.Printf("Failed to generate response: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to generate response: " + err.Error(),
			})
			return
		}

		// Step 3: Format response in OpenAI format
		assistantMessage := codeGenResponse.Explanation
		if codeGenResponse.Code != "" {
			assistantMessage = codeGenResponse.Explanation + "\n\n```motoko\n" + codeGenResponse.Code + "\n```"
		}

		convo.AddTurn("user", query)
		convo.AddTurn("assistant", assistantMessage)

		// Create OpenAI-compatible response
		response := ChatCompletionResponse{
			ID:      "chatcmpl-" + uuid.New().String(),
			Object:  "chat.completion",
			Created: time.Now().Unix(),
			Model:   resolveModel(req.Model, provider),
			Choices: []ChatCompletionChoice{
				{
					Index: 0,
					Message: ChatMessage{
						Role:    "assistant",
						Content: assistantMessage,
					},
					FinishReason: "stop",
				},
			},
			Usage: ChatCompletionUsage{
				PromptTokens:     estimateTokens(conversationAwareQuery),
				CompletionTokens: estimateTokens(assistantMessage),
				TotalTokens:      estimateTokens(conversationAwareQuery) + estimateTokens(assistantMessage),
			},
		}

		if err := repo.Save(c.Request.Context(), convo); err != nil {
			log.Printf("Failed to persist conversation: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to persist conversation",
			})
			return
		}

		response.ConversationID = convo.ID

		c.JSON(http.StatusOK, response)
	}
}

// estimateTokens provides a rough estimate of token count
func estimateTokens(text string) int {
	// Rough estimation: ~4 characters per token
	return len(text) / 4
}

func extractUserID(c *gin.Context) (int, bool) {
	value, exists := c.Get("user_id")
	if !exists {
		return 0, false
	}

	switch v := value.(type) {
	case int:
		return v, true
	case int64:
		return int(v), true
	case float64:
		return int(v), true
	default:
		return 0, false
	}
}

func loadConversation(c *gin.Context, repo *conversation.Repository, idPtr *int64, userID int) (*conversation.Conversation, error) {
	if idPtr == nil || *idPtr == 0 {
		convo := conversation.New(userID)
		return convo, nil
	}

	convo, err := repo.Get(c.Request.Context(), *idPtr, userID)
	if err != nil {
		return nil, err
	}

	return convo, nil
}

func buildConversationAwareQuery(convo *conversation.Conversation, query string) string {
	history := strings.TrimSpace(convo.BuildHistoryPrompt())
	if history == "" {
		return query
	}

	var builder strings.Builder
	builder.WriteString(history)
	builder.WriteString("Current user request:\n")
	builder.WriteString(query)
	return builder.String()
}

func resolveModel(requested string, provider string) string {
	if strings.TrimSpace(requested) != "" {
		return requested
	}

	switch provider {
	case codegen.ProviderOpenAI:
		return "openai"
	case codegen.ProviderClaude:
		return "claude"
	default:
		return "gemini"
	}
}
