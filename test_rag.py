from core.rag import build_client_index, query_knowledge

build_client_index("_template")

results = query_knowledge("_template", "What are your opening hours?")
print("\nTop matching chunks:")
for r in results:
    print("-", r)