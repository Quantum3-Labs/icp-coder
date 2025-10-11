package codegen

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"
)

const (
	defaultOpenAIModel         = "gpt-3.5-turbo"
	defaultOpenAIEndpoint      = "https://api.openai.com/v1/chat/completions"
	defaultOpenAISystemMessage = "You are a Motoko expert."
)

// OpenAIService handles code generation using OpenAI chat completions API.
type OpenAIService struct {
	apiKey        string
	model         string
	baseURL       string
	systemMessage string
	httpClient    *http.Client
}

// OpenAIMessage represents a chat message for OpenAI requests.
type OpenAIMessage struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

// openAIRequest models the JSON payload for OpenAI chat completions.
type openAIRequest struct {
	Model       string          `json:"model"`
	Messages    []OpenAIMessage `json:"messages"`
	Temperature float64         `json:"temperature,omitempty"`
	MaxTokens   int             `json:"max_tokens,omitempty"`
}

// openAIChoice represents a single completion choice.
type openAIChoice struct {
	Index   int           `json:"index"`
	Message OpenAIMessage `json:"message"`
}

// openAIResponse models the OpenAI chat completions response.
type openAIResponse struct {
	Choices []openAIChoice `json:"choices"`
}

// NewOpenAIService creates a new OpenAI service instance.
func NewOpenAIService(apiKey, model, baseURL, systemMessage string) *OpenAIService {
	if model == "" {
		model = defaultOpenAIModel
	}
	if baseURL == "" {
		baseURL = defaultOpenAIEndpoint
	}
	if systemMessage == "" {
		systemMessage = defaultOpenAISystemMessage
	}

	return &OpenAIService{
		apiKey:        apiKey,
		model:         model,
		baseURL:       baseURL,
		systemMessage: systemMessage,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// NewOpenAIServiceFromEnv loads OpenAI configuration from environment variables.
func NewOpenAIServiceFromEnv() (*OpenAIService, error) {
	apiKey := os.Getenv("OPENAI_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("OPENAI_API_KEY environment variable not set")
	}

	model := os.Getenv("OPENAI_MODEL")
	baseURL := os.Getenv("OPENAI_BASE_URL")
	systemMessage := os.Getenv("OPENAI_SYSTEM_MESSAGE")

	return NewOpenAIService(apiKey, model, baseURL, systemMessage), nil
}

// GenerateCode calls the OpenAI API to generate code using provided contexts.
func (s *OpenAIService) GenerateCode(ctx context.Context, query string, contexts []string, temperature float64, maxTokens int) (*CodeGenerationResponse, error) {
	if temperature == 0 {
		temperature = 0.7
	}
	if maxTokens == 0 {
		maxTokens = 512
	}

	prompt := assembleContextPrompt(query, contexts)

	reqPayload := openAIRequest{
		Model: s.model,
		Messages: []OpenAIMessage{
			{Role: "system", Content: s.systemMessage},
			{Role: "user", Content: prompt},
		},
		Temperature: temperature,
		MaxTokens:   maxTokens,
	}

	body, err := json.Marshal(reqPayload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal OpenAI request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, s.baseURL, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create OpenAI request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", "Bearer "+s.apiKey)

	resp, err := s.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute OpenAI request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read OpenAI response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("openai API returned status %d: %s", resp.StatusCode, string(respBody))
	}

	var openAIResp openAIResponse
	if err := json.Unmarshal(respBody, &openAIResp); err != nil {
		return nil, fmt.Errorf("failed to parse OpenAI response: %w", err)
	}

	if len(openAIResp.Choices) == 0 {
		return nil, fmt.Errorf("openai response contained no choices")
	}

	assistantText := openAIResp.Choices[0].Message.Content

	code := extractCodeBlock(assistantText, "motoko")
	if code == "" {
		code = extractCodeBlock(assistantText, "")
	}

	explanation := removeCodeBlocks(assistantText)

	return &CodeGenerationResponse{
		Code:        code,
		Explanation: explanation,
	}, nil
}
