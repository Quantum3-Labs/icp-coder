package codegen

import (
	"context"
	"os"
	"strings"
)

const (
	ProviderGemini = "gemini"
	ProviderOpenAI = "openai"
	ProviderClaude = "claude"
)

// Service describes a generic code generation provider.
type Service interface {
	GenerateCode(ctx context.Context, query string, codeContexts []string, docContexts []string, temperature float64, maxTokens int) (*CodeGenerationResponse, error)
}

// ProviderFromEnv determines which provider is configured via environment variables.
func ProviderFromEnv() string {
	provider := strings.TrimSpace(strings.ToLower(os.Getenv("CODEGEN_PROVIDER")))
	switch provider {
	case ProviderOpenAI, ProviderClaude, ProviderGemini:
		return provider
	default:
		return ProviderGemini
	}
}
