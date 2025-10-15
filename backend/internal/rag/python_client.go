package rag

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"time"
)

// PythonClient handles communication with Python RAG retriever script
type PythonClient struct {
	scriptPath string
	timeout    time.Duration
}

// RAGRequest represents the input to the Python script
type RAGRequest struct {
	Query       string `json:"query"`
	NResults    int    `json:"n_results"`
	DocsResults int    `json:"docs_results"`
}

// RAGResponse represents the output from the Python script
type RAGResponse struct {
	CodeContexts     []string  `json:"code_contexts"`
	CodeDistances    []float64 `json:"code_distances"`
	DocsContexts     []string  `json:"docs_contexts"`
	DocsDistances    []float64 `json:"docs_distances"`
	FormattedContext string    `json:"formatted_context,omitempty"`
	Warning          string    `json:"warning,omitempty"`
	Error            string    `json:"error,omitempty"`
}

// NewPythonClient creates a new Python client for RAG operations
func NewPythonClient(scriptPath string, timeout time.Duration) *PythonClient {
	if scriptPath == "" {
		scriptPath = "./scripts/rag_retriever.py"
	}
	if timeout == 0 {
		timeout = 30 * time.Second
	}

	return &PythonClient{
		scriptPath: scriptPath,
		timeout:    timeout,
	}
}

// Retrieve calls the Python script to retrieve relevant contexts from ChromaDB
func (pc *PythonClient) Retrieve(ctx context.Context, query string, nResults int) (*RAGResponse, error) {
	// Validate inputs
	if query == "" {
		return nil, fmt.Errorf("query cannot be empty")
	}
	if nResults < 1 || nResults > 10 {
		nResults = 10
	}

	// Create request
	request := RAGRequest{
		Query:       query,
		NResults:    nResults,
		DocsResults: nResults,
	}

	requestJSON, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	// Create context with timeout
	execCtx, cancel := context.WithTimeout(ctx, pc.timeout)
	defer cancel()

	// Find Python executable
	pythonCmd := pc.findPythonExecutable()

	// Create command
	cmd := exec.CommandContext(execCtx, pythonCmd, pc.scriptPath)

	// Set up stdin, stdout, stderr
	cmd.Stdin = bytes.NewReader(requestJSON)
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr

	// Set environment variables
	cmd.Env = os.Environ()

	// Execute command
	err = cmd.Run()

	// Check for errors
	if err != nil {
		stderrStr := stderr.String()
		if stderrStr != "" {
			return nil, fmt.Errorf("python script error: %s (stderr: %s)", err, stderrStr)
		}
		return nil, fmt.Errorf("failed to execute python script: %w", err)
	}

	// Parse response
	var response RAGResponse
	if err := json.Unmarshal(stdout.Bytes(), &response); err != nil {
		return nil, fmt.Errorf("failed to parse python response: %w (output: %s)", err, stdout.String())
	}

	// Check for errors in response
	if response.Error != "" {
		return nil, fmt.Errorf("python script returned error: %s", response.Error)
	}

	return &response, nil
}

// findPythonExecutable finds the Python executable to use
func (pc *PythonClient) findPythonExecutable() string {
	// Check for PYTHON_EXECUTABLE environment variable
	if pythonExec := os.Getenv("PYTHON_EXECUTABLE"); pythonExec != "" {
		return pythonExec
	}

	// Try common Python executables in order of preference
	executables := []string{"python3", "python"}

	for _, exe := range executables {
		if _, err := exec.LookPath(exe); err == nil {
			return exe
		}
	}

	// Default to python3
	return "python3"
}

// HealthCheck verifies that the Python script is accessible and working
func (pc *PythonClient) HealthCheck(ctx context.Context) error {
	// Check if script file exists
	if _, err := os.Stat(pc.scriptPath); os.IsNotExist(err) {
		return fmt.Errorf("python script not found: %s", pc.scriptPath)
	}

	// Try a simple query to verify it works
	_, err := pc.Retrieve(ctx, "test query", 1)
	if err != nil {
		return fmt.Errorf("python script health check failed: %w", err)
	}

	return nil
}
