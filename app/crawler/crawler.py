import sqlite3
import asyncio
import wikipediaapi

def init_db():
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_db(doc: dict):
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT OR IGNORE INTO documents (url, title, content) VALUES (?, ?, ?)",
            (doc["url"], doc["title"], doc["content"])
        )
        conn.commit()
    finally:
        conn.close()

def fetch_page(wiki, topic: str) -> dict:
    page = wiki.page(topic)
    if page.exists():
        return {
            "url": page.fullurl,
            "title": page.title,
            "content": page.text
        }
    return {"url": "", "title": topic, "content": ""}

async def crawl_all(topics: list[str]):
    init_db()
    wiki = wikipediaapi.Wikipedia(
        language="en",
        user_agent="SemanticSearchEngine/1.0 (ekta.learning.project@gmail.com)"
    )
    for topic in topics:
        print(f"Crawling: {topic}")
        doc = fetch_page(wiki, topic)
        if len(doc["content"]) > 100:
            save_to_db(doc)
            print(f"Saved: {doc['title']} — {len(doc['content'])} chars")
        else:
            print(f"Skipped (empty): {topic}")
        await asyncio.sleep(2)

if __name__ == "__main__":
    topics = [
        "Machine learning", "Deep learning", "Neural network",
        "Natural language processing", "Transformer (machine learning model)",
        "Large language model", "Retrieval-augmented generation",
        "Vector database", "FastAPI", "LangChain"
    ]
    asyncio.run(crawl_all(topics))