package codegen

import "strings"

// extractCodeBlock extracts code from markdown code blocks.
func extractCodeBlock(text, language string) string {
	var startMarker, endMarker string

	if language != "" {
		startMarker = "```" + language
	} else {
		startMarker = "```"
	}
	endMarker = "```"

	startIdx := strings.Index(text, startMarker)
	if startIdx == -1 {
		return ""
	}

	// Move past the start marker and newline
	startIdx += len(startMarker)
	if startIdx < len(text) && text[startIdx] == '\n' {
		startIdx++
	}

	endIdx := strings.Index(text[startIdx:], endMarker)
	if endIdx == -1 {
		return ""
	}

	return strings.TrimSpace(text[startIdx : startIdx+endIdx])
}

// removeCodeBlocks removes all markdown code blocks from text.
func removeCodeBlocks(text string) string {
	result := text

	for {
		startIdx := strings.Index(result, "```")
		if startIdx == -1 {
			break
		}

		endIdx := strings.Index(result[startIdx+3:], "```")
		if endIdx == -1 {
			break
		}

		// Remove the code block
		result = result[:startIdx] + result[startIdx+3+endIdx+3:]
	}

	return strings.TrimSpace(result)
}
