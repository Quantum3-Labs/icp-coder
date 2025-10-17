package middleware

import (
	"net/http"
	"sync/atomic"

	"github.com/gin-gonic/gin"
)

var (
	maintenanceEnabled atomic.Bool
	maintenanceMessage atomic.Value
)

const defaultMaintenanceMessage = "Service is temporarily unavailable while initialization is in progress. Please try again shortly."

func init() {
	maintenanceMessage.Store(defaultMaintenanceMessage)
}

// SetMaintenanceMode toggles maintenance mode and optionally updates the message returned to clients.
func SetMaintenanceMode(enabled bool, message ...string) {
	maintenanceEnabled.Store(enabled)
	if len(message) > 0 && message[0] != "" {
		maintenanceMessage.Store(message[0])
	} else if !enabled {
		maintenanceMessage.Store("")
	}
}

// SetMaintenanceMessage updates the message returned while maintenance mode is active.
func SetMaintenanceMessage(message string) {
	if message == "" {
		maintenanceMessage.Store(defaultMaintenanceMessage)
		return
	}
	maintenanceMessage.Store(message)
}

// IsMaintenanceMode reports whether maintenance mode is currently active.
func IsMaintenanceMode() bool {
	return maintenanceEnabled.Load()
}

// MaintenanceModeMiddleware blocks requests while maintenance mode is active.
func MaintenanceModeMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		if maintenanceEnabled.Load() {
			msg, _ := maintenanceMessage.Load().(string)
			if msg == "" {
				msg = defaultMaintenanceMessage
			}

			c.AbortWithStatusJSON(http.StatusServiceUnavailable, gin.H{
				"error":   "maintenance_mode",
				"message": msg,
			})
			return
		}

		c.Next()
	}
}
