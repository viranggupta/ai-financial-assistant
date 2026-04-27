from semantic_memory import semantic_search

def is_relevant(content):
    # remove junk/system messages
    if "$caveman" in content.lower():
        return False
    if "limit" in content.lower():
        return False
    if "reset" in content.lower():
        return False

    # keep only finance-related content
    keywords = ["finance", "bank", "investment", "market", "money"]

    return any(word in content.lower() for word in keywords)


def build_context(query):
    results = semantic_search(query)

    context = ""
    for doc in results:
        content = doc["content"]

        if is_relevant(content):
            context += content + "\n\n"

    return context

def generate_response(user_query):
    context = build_context(user_query)

    prompt = f"""
You are a financial assistant.

Use ONLY relevant financial context below:
{context}

Ignore any irrelevant or system-generated messages.

Answer clearly and professionally:
{user_query}
"""

    return prompt  # replace with LLM call later


if __name__ == "__main__":
    while True:
        user_query = input("\nAsk something: ")

        if user_query.lower() == "exit":
            break

        response = generate_response(user_query)
        print("\n--- RESPONSE ---\n")
        print(response)