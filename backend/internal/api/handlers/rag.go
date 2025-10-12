package handlers

import (
	"database/sql"
	"log"
	"net/http"
	"strings"

	"github.com/Quantum3-Labs/icp-coder/backend/internal/codegen"
	"github.com/Quantum3-Labs/icp-coder/backend/internal/rag"
	"github.com/gin-gonic/gin"
)

// RetrieveContextRequest represents a context retrieval request
type RetrieveContextRequest struct {
	Query    string `json:"query" binding:"required"`
	NResults int    `json:"n_results"`
}

// GenerateCodeRequest represents a code generation request
type GenerateCodeRequest struct {
	Query       string  `json:"query" binding:"required"`
	Temperature float64 `json:"temperature"`
	MaxTokens   int     `json:"max_tokens"`
}

// Service singletons
var (
	ragServiceInstance      *rag.Service
	codegenServiceInstances map[string]codegen.Service
)

// getRAGService creates or returns a RAG service instance
func getRAGService() (*rag.Service, error) {
	if ragServiceInstance == nil {
		service, err := rag.NewServiceFromEnv()
		if err != nil {
			return nil, err
		}
		ragServiceInstance = service
	}
	return ragServiceInstance, nil
}

// getCodegenService creates or returns a code generation service instance for the provider.
func getCodegenService(provider string) (codegen.Service, error) {
	if codegenServiceInstances == nil {
		codegenServiceInstances = make(map[string]codegen.Service)
	}

	normalized := strings.ToLower(provider)
	if service, ok := codegenServiceInstances[normalized]; ok {
		return service, nil
	}

	var (
		service codegen.Service
		err     error
	)

	switch normalized {
	case codegen.ProviderOpenAI:
		service, err = codegen.NewOpenAIServiceFromEnv()
	case codegen.ProviderClaude:
		service, err = codegen.NewClaudeServiceFromEnv()
	default:
		normalized = codegen.ProviderGemini
		service, err = codegen.NewGeminiServiceFromEnv()
	}
	if err != nil {
		return nil, err
	}

	codegenServiceInstances[normalized] = service
	return service, nil
}

// RetrieveContext retrieves relevant Motoko code context from ChromaDB
func RetrieveContext(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req RetrieveContextRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "Invalid request: " + err.Error(),
			})
			return
		}

		// Get RAG service
		service, err := getRAGService()
		if err != nil {
			log.Printf("Failed to initialize RAG service: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to initialize RAG service: " + err.Error(),
			})
			return
		}

		// Set default n_results if not provided
		if req.NResults == 0 {
			req.NResults = 5
		}

		// Retrieve context
		response, err := service.RetrieveContext(c.Request.Context(), req.Query, req.NResults)
		if err != nil {
			log.Printf("Failed to retrieve context: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to retrieve context: " + err.Error(),
			})
			return
		}

		c.JSON(http.StatusOK, response)
	}
}

// GenerateCode generates Motoko code using RAG + Gemini
func GenerateCode(db *sql.DB) gin.HandlerFunc {
	return func(c *gin.Context) {
		var req GenerateCodeRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{
				"error": "Invalid request: " + err.Error(),
			})
			return
		}

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
		ragResponse, err := ragService.RetrieveContext(c.Request.Context(), req.Query, 5)
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

		// Step 2: Generate code using the configured provider with the retrieved context
		response, err := codegenService.GenerateCode(
			c.Request.Context(),
			req.Query,
			ragResponse.CodeContexts,
			req.Temperature,
			req.MaxTokens,
		)
		if err != nil {
			log.Printf("Failed to generate code: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{
				"error": "Failed to generate code: " + err.Error(),
			})
			return
		}

		c.JSON(http.StatusOK, response)
	}
}
