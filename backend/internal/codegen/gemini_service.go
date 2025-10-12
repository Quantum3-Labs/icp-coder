package codegen

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"
)

// GeminiService handles code generation using Gemini API
type GeminiService struct {
	apiKey     string
	httpClient *http.Client
}

// CodeGenerationRequest represents a code generation request
type CodeGenerationRequest struct {
	Query       string  `json:"query"`
	Temperature float64 `json:"temperature,omitempty"`
	MaxTokens   int     `json:"max_tokens,omitempty"`
}

// CodeGenerationResponse represents a code generation response
type CodeGenerationResponse struct {
	Code        string `json:"code"`
	Explanation string `json:"explanation"`
}

// NewGeminiService creates a new Gemini service
func NewGeminiService(apiKey string) *GeminiService {
	return &GeminiService{
		apiKey: apiKey,
		httpClient: &http.Client{
			Timeout: 60 * time.Second,
		},
	}
}

// NewGeminiServiceFromEnv creates a new Gemini service using environment variables
func NewGeminiServiceFromEnv() (*GeminiService, error) {
	apiKey := os.Getenv("GEMINI_API_KEY")
	if apiKey == "" {
		return nil, fmt.Errorf("GEMINI_API_KEY environment variable not set")
	}

	return NewGeminiService(apiKey), nil
}

// GenerateCode generates Motoko code using Gemini with provided context
func (s *GeminiService) GenerateCode(ctx context.Context, query string, contexts []string, temperature float64, maxTokens int) (*CodeGenerationResponse, error) {
	// Assemble prompt with context
	prompt := assembleContextPrompt(query, contexts)

	// Set defaults
	if temperature == 0 {
		temperature = 0.7
	}
	if maxTokens == 0 {
		maxTokens = 2000
	}

	// Call Gemini API
	geminiResponse, err := s.callGemini(ctx, prompt, temperature, maxTokens)
	if err != nil {
		return nil, fmt.Errorf("failed to call Gemini API: %w", err)
	}

	// Parse and return response
	return s.parseGeminiResponse(geminiResponse)
}

// GeminiRequest represents a request to the Gemini API
type GeminiRequest struct {
	Contents []GeminiContent        `json:"contents"`
	Config   GeminiGenerationConfig `json:"generationConfig"`
}

// GeminiContent represents content in a Gemini request
type GeminiContent struct {
	Parts []GeminiPart `json:"parts"`
}

// GeminiPart represents a part in Gemini content
type GeminiPart struct {
	Text string `json:"text"`
}

// GeminiGenerationConfig represents generation configuration for Gemini
type GeminiGenerationConfig struct {
	Temperature     float64 `json:"temperature"`
	MaxOutputTokens int     `json:"maxOutputTokens"`
}

// GeminiResponse represents a response from the Gemini API
type GeminiResponse struct {
	Candidates []GeminiCandidate `json:"candidates"`
}

// GeminiCandidate represents a candidate in the Gemini response
type GeminiCandidate struct {
	Content GeminiContent `json:"content"`
}

// callGemini calls the Gemini API
func (s *GeminiService) callGemini(ctx context.Context, prompt string, temperature float64, maxTokens int) (string, error) {
	// Construct Gemini API URL (using Gemini 2.0 Flash as specified in PLAN.md)
	url := fmt.Sprintf("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=%s", s.apiKey)

	// Prepare request
	geminiReq := GeminiRequest{
		Contents: []GeminiContent{
			{
				Parts: []GeminiPart{
					{Text: prompt},
				},
			},
		},
		Config: GeminiGenerationConfig{
			Temperature:     temperature,
			MaxOutputTokens: maxTokens,
		},
	}

	reqBody, err := json.Marshal(geminiReq)
	if err != nil {
		return "", fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create HTTP request
	httpReq, err := http.NewRequestWithContext(ctx, "POST", url, bytes.NewReader(reqBody))
	if err != nil {
		return "", fmt.Errorf("failed to create request: %w", err)
	}

	httpReq.Header.Set("Content-Type", "application/json")

	// Execute request
	resp, err := s.httpClient.Do(httpReq)
	if err != nil {
		return "", fmt.Errorf("failed to execute request: %w", err)
	}
	defer resp.Body.Close()

	// Read response body
	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read response: %w", err)
	}

	// Check status code
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("gemini API returned status %d: %s", resp.StatusCode, string(respBody))
	}

	// Parse response
	var geminiResp GeminiResponse
	if err := json.Unmarshal(respBody, &geminiResp); err != nil {
		return "", fmt.Errorf("failed to parse response: %w", err)
	}

	// Extract text from first candidate
	if len(geminiResp.Candidates) == 0 || len(geminiResp.Candidates[0].Content.Parts) == 0 {
		return "", fmt.Errorf("no content in gemini response")
	}

	return geminiResp.Candidates[0].Content.Parts[0].Text, nil
}

// parseGeminiResponse extracts code and explanation from Gemini's response
func (s *GeminiService) parseGeminiResponse(response string) (*CodeGenerationResponse, error) {
	// Try to extract code block
	code := extractCodeBlock(response, "motoko")
	if code == "" {
		code = extractCodeBlock(response, "")
	}

	// Extract explanation (everything outside code blocks)
	explanation := removeCodeBlocks(response)

	return &CodeGenerationResponse{
		Code:        code,
		Explanation: strings.TrimSpace(explanation),
	}, nil
}
