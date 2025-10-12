package api

import (
	"database/sql"

	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"

	"github.com/Quantum3-Labs/icp-coder/backend/internal/api/handlers"
	"github.com/Quantum3-Labs/icp-coder/backend/internal/api/middleware"
	"github.com/Quantum3-Labs/icp-coder/backend/internal/auth"

	_ "github.com/Quantum3-Labs/icp-coder/backend/docs" // Import generated docs
)

// SetupRoutes configures all API routes
func SetupRoutes(router *gin.Engine, db *sql.DB) {
	// Swagger documentation
	router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))

	// Health check (supports both GET and HEAD)
	healthHandler := func(c *gin.Context) {
		c.JSON(200, gin.H{"status": "ok"})
	}
	router.GET("/health", healthHandler)
	router.HEAD("/health", healthHandler)

	// API v1 routes
	v1 := router.Group("/api/v1")
	{
		// Authentication routes (public register/login)
		authGroup := v1.Group("/auth")
		{
			
			authGroup.POST("/register", handlers.Register(db))
			authGroup.POST("/login", handlers.Login(db))
		}

		protectedAuth := authGroup.Group("/")
		protectedAuth.Use(middleware.BasicAuth(db))
		{
			protectedAuth.POST("/keys", handlers.CreateAPIKey(db))
			protectedAuth.GET("/keys", handlers.ListAPIKeys(db))
			protectedAuth.DELETE("/keys/:id", handlers.RevokeAPIKey(db))
		}

		// Ingestion routes (Basic Auth)
		ingest := v1.Group("/ingest")
		ingest.Use(middleware.BasicAuth(db), middleware.RequireRole(auth.RoleAdmin))
		{
			ingest.POST("/clone-repos", handlers.CloneRepos(db))
			ingest.POST("/samples", handlers.IngestSamples(db))
			ingest.POST("/docs", handlers.IngestDocs(db))
			ingest.GET("/jobs", handlers.ListIngestionJobs(db))
			ingest.GET("/jobs/:id", handlers.GetIngestionJob(db))
			ingest.POST("/jobs/:id/cancel", handlers.CancelIngestionJob(db))
		}

		// RAG routes (API Key Auth)
		rag := v1.Group("/rag")
		rag.Use(middleware.APIKeyAuth(db))
		{
			rag.POST("/retrieve", handlers.RetrieveContext(db))
			rag.POST("/generate", handlers.GenerateCode(db))
		}
	}

	// OpenAI-compatible chat completions endpoint (API Key Auth)
	router.POST("/v1/chat/completions", middleware.APIKeyAuth(db), handlers.ChatCompletions(db))
}
