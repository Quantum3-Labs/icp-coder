package rag

import (
	"context"
	"fmt"
	"os"
	"time"
)

// Service provides RAG retrieval operations from ChromaDB
type Service struct {
	pythonClient *PythonClient
}

// NewService creates a new RAG service
func NewService(pythonClient *PythonClient) *Service {
	return &Service{
		pythonClient: pythonClient,
	}
}

// NewServiceFromEnv creates a new RAG service using environment variables
func NewServiceFromEnv() (*Service, error) {
	scriptPath := os.Getenv("PYTHON_SCRIPT_PATH")
	if scriptPath == "" {
		scriptPath = "./scripts/rag_retriever.py"
	}

	pythonClient := NewPythonClient(scriptPath, 30*time.Second)

	return NewService(pythonClient), nil
}

// RetrieveContext retrieves relevant Motoko code context from ChromaDB
func (s *Service) RetrieveContext(ctx context.Context, query string, nResults int) (*RAGResponse, error) {
	if nResults == 0 {
		nResults = 5
	}

	if nResults < 1 || nResults > 20 {
		return nil, fmt.Errorf("n_results must be between 1 and 20")
	}

	return s.pythonClient.Retrieve(ctx, query, nResults)
}
