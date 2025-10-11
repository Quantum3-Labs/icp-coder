package codegen

import (
	"fmt"
	"strings"
)

// assembleContextPrompt creates a RAG-enhanced prompt with code contexts.
func assembleContextPrompt(query string, contexts []string) string {
	var promptBuilder strings.Builder

	promptBuilder.WriteString("You are an expert Motoko programmer. ")
	promptBuilder.WriteString("Use the provided Motoko code examples as context to answer the user's question.\n\n")

	if len(contexts) > 0 {
		promptBuilder.WriteString("## Context Examples:\n\n")
		for i, context := range contexts {
			promptBuilder.WriteString(fmt.Sprintf("### Example %d:\n```motoko\n%s\n```\n\n", i+1, context))
		}
	}

	promptBuilder.WriteString("## User Question:\n")
	promptBuilder.WriteString(query)
	promptBuilder.WriteString("\n\n")

	promptBuilder.WriteString("## Instructions:\n")
	promptBuilder.WriteString("Provide a clear, working Motoko code solution based on the examples above. ")
	promptBuilder.WriteString("Include a brief explanation of how the code works. ")
	promptBuilder.WriteString("Format your response as:\n\n")
	promptBuilder.WriteString("**Code:**\n```motoko\n[your code here]\n```\n\n")
	promptBuilder.WriteString("**Explanation:**\n[your explanation here]\n")

	return promptBuilder.String()
}
