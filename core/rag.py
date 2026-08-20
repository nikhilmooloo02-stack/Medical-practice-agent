import json
import chromadb
from pathlib import Path


def load_client_config(client_id: str) -> dict:
    """Load a client's config.json"""
    config_path = Path(f"clients/{client_id}/config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_knowledge_chunks(config: dict) -> list[str]:
    """Turn a client's config into small text chunks for retrieval"""
    chunks = []

    chunks.append(f"Practice name: {config['practice_name']}. {config['tagline']}")

    contact = config["contact"]
    chunks.append(
        f"Contact info: Phone {contact['phone']}, WhatsApp {contact['whatsapp']}, "
        f"Email {contact['email']}, Address {contact['address']}, Website {contact['website']}"
    )

    hours_lines = [f"{day.capitalize()}: {time}" for day, time in config["hours"].items()]
    chunks.append("Operating hours: " + "; ".join(hours_lines))

    for service in config["services"]:
        chunks.append(
            f"Service: {service['name']}. {service['description']}. "
            f"Price range: {service['price_range']}"
        )

    for staff in config["staff"]:
        chunks.append(
            f"Staff member: {staff['name']}, {staff['role']}. {staff['bio']}"
        )

    chunks.append(f"Important disclaimer: {config['compliance']['disclaimer_text']}")

    return chunks


def build_client_index(client_id: str):
    """Build (or rebuild) a ChromaDB collection for one client"""
    config = load_client_config(client_id)
    chunks = build_knowledge_chunks(config)

    chroma_client = chromadb.PersistentClient(path=f"clients/{client_id}/chroma_db")

    try:
        chroma_client.delete_collection(name="knowledge")
    except Exception:
        pass

    collection = chroma_client.create_collection(name="knowledge")

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, ids=ids)

    print(f"Indexed {len(chunks)} chunks for client '{client_id}'")
    return collection


def query_knowledge(client_id: str, question: str, n_results: int = 3) -> list[str]:
    """Retrieve the most relevant chunks for a given question"""
    chroma_client = chromadb.PersistentClient(path=f"clients/{client_id}/chroma_db")
    collection = chroma_client.get_collection(name="knowledge")

    results = collection.query(query_texts=[question], n_results=n_results)
    return results["documents"][0]