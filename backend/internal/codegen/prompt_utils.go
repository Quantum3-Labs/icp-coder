package codegen

import (
	"fmt"
	"strings"
)

func buildCodeGenerationInstruction(query string, codeContexts, docContexts []string) string {
	var promptBuilder strings.Builder

	promptBuilder.WriteString("You are an expert Motoko programmer. ")
	promptBuilder.WriteString("Use the provided Motoko code examples and documentation excerpts as context to answer the user's question.\n\n")

	if len(codeContexts) > 0 {
		promptBuilder.WriteString("## Code Examples:\n\n")
		for i, context := range codeContexts {
			promptBuilder.WriteString(fmt.Sprintf("### Code Example %d:\n```motoko\n%s\n```\n\n", i+1, context))
		}
	}

	if len(docContexts) > 0 {
		promptBuilder.WriteString("## Documentation Excerpts:\n\n")
		for i, doc := range docContexts {
			promptBuilder.WriteString(fmt.Sprintf("### Doc Excerpt %d:\n```text\n%s\n```\n\n", i+1, doc))
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
