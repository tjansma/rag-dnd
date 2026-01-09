from config import Config
from rag import Chunker, Embedding

def main():
    config = Config()

    chunker = Chunker(strategy="heading2")
    chunks = chunker.chunk(text=open(config.session_log).read())

    embedding = Embedding()
    vector = embedding.embed_sentences(chunks[-1])
    print(chunks[-1])
    print(vector)

if __name__ == "__main__":
    main()
