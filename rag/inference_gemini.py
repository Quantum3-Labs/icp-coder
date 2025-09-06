import os
from dotenv import load_dotenv
import requests
import textwrap
from base import retrieve_context, build_context_prompt

# Try to import the Gemini SDK
try:
    import google.generativeai as genai

    GEMINI_SDK_AVAILABLE = True
except ImportError:
    GEMINI_SDK_AVAILABLE = False

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini inference parameters
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.9,
    "top_k": 64,
    "max_output_tokens": 8192,
}
MODEL_NAME = "models/gemini-2.5-flash"  # Gemini Flash 2.5


def count_tokens_gemini_sdk(model, prompt):
    # Use the Gemini SDK to count tokens
    try:
        return model.count_tokens(prompt).total_tokens
    except Exception:
        return None


def answer_with_gemini_sdk(query, retrieved_data):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME, generation_config=GENERATION_CONFIG)
    prompt = build_context_prompt(retrieved_data, query)
    num_tokens = count_tokens_gemini_sdk(model, prompt)
    response = model.generate_content(prompt)
    return response.text, num_tokens


def answer_with_gemini_rest(query, retrieved_data):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
    headers = {"Content-Type": "application/json"}
    params = {"key": GEMINI_API_KEY}
    prompt = build_context_prompt(retrieved_data, query)
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": GENERATION_CONFIG,
    }
    resp = requests.post(url, headers=headers, params=params, json=data)
    if resp.ok:
        # Gemini REST API does not return token count directly
        answer = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        return answer, None
    else:
        return f"Gemini API error: {resp.text}", None


def main():
    query = input("Enter your Motoko-related question: ")

    # Retrieve combined context
    retrieved_data = retrieve_context(query)

    print("\nRetrieved context:")
    print(f"Documentation chunks: {len(retrieved_data['doc_docs'])}")
    print(f"Code examples: {len(retrieved_data['code_docs'])}")

    # Show documentation context
    if retrieved_data["doc_docs"]:
        print("\n=== DOCUMENTATION RESULTS ===")
        doc_results = list(
            zip(
                retrieved_data["doc_docs"],
                retrieved_data["doc_metas"],
                retrieved_data["doc_distances"],
            )
        )
        doc_results.sort(key=lambda x: x[2])  # Sort by distance

        for i, (doc, meta, distance) in enumerate(doc_results[:3]):  # Show top 3
            similarity = 1 - distance if distance <= 1 else 0
            print(
                f"[DOC {i+1}] {meta.get('chunk_title', 'Untitled')} (Score: {similarity:.3f})"
            )
            print(f"Source: {meta.get('source_file', 'Unknown')}")
            print(f"Content: {doc[:150]}...")
            print()

    # Show code context
    if retrieved_data["code_docs"]:
        print("=== CODE EXAMPLES ===")
        code_results = list(
            zip(
                retrieved_data["code_docs"],
                retrieved_data["code_metas"],
                retrieved_data["code_distances"],
            )
        )
        code_results.sort(key=lambda x: x[2])  # Sort by distance

        for i, (code, meta, distance) in enumerate(code_results[:2]):  # Show top 2
            similarity = 1 - distance if distance <= 1 else 0
            print(
                f"[CODE {i+1}] {meta.get('filename', 'Unknown')} (Score: {similarity:.3f})"
            )
            print(f"Path: {meta.get('rel_path', 'Unknown')}")
            print(f"Content: {code[:150]}...")
            print()

    print("\n" + "=" * 60)
    print(f"Gemini model: {MODEL_NAME}")
    print("\nGemini response:")

    if GEMINI_SDK_AVAILABLE:
        answer, num_tokens = answer_with_gemini_sdk(query, retrieved_data)
        if num_tokens is not None:
            print(f"[Token count for prompt: {num_tokens}]")
    else:
        answer, _ = answer_with_gemini_rest(query, retrieved_data)
        print("[Token count not available: Gemini SDK not installed]")

    print(answer)


if __name__ == "__main__":
    main()
