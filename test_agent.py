from core.agent import get_response

result = get_response("_template", "What are your opening hours?")
print("Response:", result["response"])
print("Escalated:", result["escalated"])

print("\n---\n")

result2 = get_response("_template", "This is an emergency, I need help now")
print("Response:", result2["response"])
print("Escalated:", result2["escalated"])