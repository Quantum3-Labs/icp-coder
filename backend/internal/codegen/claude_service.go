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
	defaultClaudeModel         = "claude-3-opus-20240229"
	defaultClaudeEndpoint      = "https://api.anthropic.com/v1/messages"
	defaultClaudeAPIVersion    = "2023-06-01"
	defaultClaudeSystemMessage = "You are an expert Motoko programmer."
	defaultClaudeMaxTokens     = 512
	defaultClaudeTemperature   = 0.7
)

// ClaudeService handles code generation using Anthropic Claude API.
type ClaudeService struct {
	apiKey        string
	model         string
	baseURL       string
	apiVersion    string
	systemMessage string
	httpClient    *http.Client
}

type claudeMessageContent struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type claudeMessage struct {
	Role    string                 `json:"role"`
	Content []claudeMessageContent `json:"content"`
}

type claudeRequest struct {
	Model       string          `json:"model"`
	System      string          `json:"system,omitempty"`
	MaxTokens   int             `json:"max_tokens"`
	Temperature float64         `json:"temperature,omitempty"`
	Messages    []claudeMessage `json:"messages"`
}

type claudeContentBlock struct {
	Type string `json:"type"`
	Text string `json:"text"`
}

type claudeResponse struct {
	Content []claudeContentBlock `json:"content"`
}

// NewClaudeService creates a new Claude service instance.
func NewClaudeService(apiKey, model, baseURL, apiVersion, systemMessage string) *ClaudeService {
	if model == "" {
		model = defaultClaudeModel
	}
	if baseURL == "" {
		baseURL = defaultClaudeEndpoint
	}
	if apiVersion == "" {
		apiVersion = defaultClaudeAPIVersion
	}
	if systemMessage == "" {
		systemMessage = defaultClaudeSystemMessage
	}

	return &ClaudeService{
		apiKey:        apiKey,
		model:         model,
		baseURL:       baseURL,
		apiVersion:    apiVersion,
		systemMessage: systemMessage,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// NewClaudeServiceFromEnv loads Claude configuration from environment variables.
func NewClaudeServiceFromEnv() (*ClaudeService, error) {
	apiKey := os.Getenv("CLAUDE_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("CLAUDE_API_KEY environment variable not set")
	}

	model := os.Getenv("CLAUDE_MODEL")
	baseURL := os.Getenv("CLAUDE_BASE_URL")
	apiVersion := os.Getenv("CLAUDE_API_VERSION")
	systemMessage := os.Getenv("CLAUDE_SYSTEM_MESSAGE")

	return NewClaudeService(apiKey, model, baseURL, apiVersion, systemMessage), nil
}

// GenerateCode calls Anthropic Claude API to generate code with provided contexts.
func (s *ClaudeService) GenerateCode(ctx context.Context, query string, contexts []string, temperature float64, maxTokens int) (*CodeGenerationResponse, error) {
	if temperature == 0 {
		temperature = defaultClaudeTemperature
	}
	if maxTokens == 0 {
		maxTokens = defaultClaudeMaxTokens
	}

	prompt := assembleContextPrompt(query, contexts)

	reqPayload := claudeRequest{
		Model:       s.model,
		System:      s.systemMessage,
		MaxTokens:   maxTokens,
		Temperature: temperature,
		Messages: []claudeMessage{
			{
				Role: "user",
				Content: []claudeMessageContent{
					{Type: "text", Text: prompt},
				},
			},
		},
	}

	body, err := json.Marshal(reqPayload)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal Claude request: %w", err)
	}

	httpReq, err := http.NewRequestWithContext(ctx, http.MethodPost, s.baseURL, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create Claude request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("x-api-key", s.apiKey)
	httpReq.Header.Set("anthropic-version", s.apiVersion)

	resp, err := s.httpClient.Do(httpReq)
	if err != nil {
		return nil, fmt.Errorf("failed to execute Claude request: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read Claude response: %w", err)
	}

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("claude API returned status %d: %s", resp.StatusCode, string(respBody))
	}

	var claudeResp claudeResponse
	if err := json.Unmarshal(respBody, &claudeResp); err != nil {
		return nil, fmt.Errorf("failed to parse Claude response: %w", err)
	}

	if len(claudeResp.Content) == 0 {
		return nil, fmt.Errorf("claude response contained no content")
	}

	assistantText := claudeResp.Content[0].Text

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
