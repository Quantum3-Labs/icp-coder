import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import chromadb
from chromadb.config import Settings
from utils.embedding import get_embedding
from sentence_transformers import SentenceTransformer

# Load once at module level for efficiency
_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding(text: str) -> list:
    return _model.encode(text).tolist()

MOTOKO_BOOK_TOC = 'https://internetcomputer.org/docs/current/motoko/main/motoko-introduction'
MOTOKO_BOOK_BASE = 'https://internetcomputer.org'

class MotokoBookIngester:
    def __init__(self, collection_name='motoko_book'):
        self.chroma_client = chromadb.Client(Settings(persist_directory="chromadb_data"))
        self.collection = self.chroma_client.get_or_create_collection(collection_name)

    def fetch_chapter_links(self):
        res = requests.get(MOTOKO_BOOK_TOC)
        soup = BeautifulSoup(res.text, 'html.parser')
        links = set()
        for a in soup.select('nav a'):
            href = a.get('href')
            if href and href.startswith('/docs/current/motoko/'):
                links.add(MOTOKO_BOOK_BASE + href)
        return sorted(list(links))

    def fetch_and_chunk(self, url):
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        main = soup.find('main')
        if not main:
            return []
        # Extract and chunk text
        chunks = []
        buffer = ''
        for el in main.find_all(['section', 'h1', 'h2', 'h3', 'p', 'li']):
            text = el.get_text(strip=True)
            if len(text) > 40:
                if len(buffer) + len(text) > 500:
                    if buffer:
                        chunks.append(buffer.strip())
                    buffer = text
                else:
                    buffer += ' ' + text
        if buffer:
            chunks.append(buffer.strip())
        return chunks

    def ingest(self):
        links = self.fetch_chapter_links()
        all_chunks = []
        metadatas = []
        print(f"Found {len(links)} chapters. Downloading and chunking...")
        for url in tqdm(links):
            try:
                chunks = self.fetch_and_chunk(url)
                all_chunks.extend(chunks)
                metadatas.extend([{'source': url}] * len(chunks))
            except Exception as e:
                print(f"Failed to process {url}: {e}")
        print(f"Total chunks: {len(all_chunks)}. Generating embeddings and storing in ChromaDB...")
        for i, chunk in enumerate(tqdm(all_chunks)):
            embedding = get_embedding(chunk)
            self.collection.add(
                documents=[chunk],
                embeddings=[embedding],
                metadatas=[metadatas[i]],
                ids=[f"motoko_{i}"]
            )
        print("Ingestion complete!") 