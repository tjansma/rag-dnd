"""Coordinating the storage of documents, chunks, and sentences."""
import logging
from typing import Any, Mapping, cast

import chromadb
from rank_bm25 import BM25Okapi

from ..config import Config
from .models import Chunk

STOP_WORDS = {
    # Dutch
    "de", "het", "een", "en", "van", "ik", "te", "dat", "die", "in", "hij", "zij", "wij", "is", 
    "niet", "zijn", "wat", "om", "ook", "als", "voor", "op", "maar", "met", "er", "aan", "mij", 
    "dit", "we", "hebt", "ben", "kan", "heb", "uit", "naar", "dan", "of", "je", "jij", "ze", "wel",
    "nog", "na", "hier", "daar", "waar", "hoe", "wie", "waarom", "toch", "al", "door", "tot",
    "jou", "uw", "u", "mijzelf", "ons", "onze", "doen", "geen", "welke",
    "heeft", "hebben", "had", "hadden", "kunnen", "zullen", "zal", "zou", "moet", "moeten",
    "mag", "mogen", "wil", "willen", "worden", "werd", "geworden", "was", "waren", "geweest",
    "bent", "hun", "haar", "hem", "hen", "jullie", "jouw", "mijn", "meer", "veel", "alles", 
    "niets", "echt", "heel", "erg", "gaan", "gaat", "ging", "komen", "komt", "kwam", "doet", "deed",
    # English
    "the", "a", "an", "and", "in", "on", "at", "to", "for", "is", "of", "it", "that", "this", 
    "what", "how", "who", "with", "but", "as", "or", "be", "are", "was", "were", "i", "you", "he",
    "she", "we", "they", "my", "your", "his", "her", "so", "do", "not"
}

logger = logging.getLogger(__name__)

class VectorStore:
    """Vector store for chunks (Hybrid: ChromaDB + BM25)."""
    def __init__(self, config: Config, collection_name: str) -> None:
        """
        Initialize the vector store.
        
        Args:
            config (Config): The configuration.
            
        Returns:
            None
        """
        self.config = config

        logger.info(f"Initializing Hybrid Vector Store: {config.vector_database}")
        self.client = chromadb.PersistentClient(config.vector_database,
                                                settings=chromadb.Settings(
                                                    anonymized_telemetry=False))

        logger.debug(f"Initializing collection: {collection_name}")
        self.collection = self.client.get_or_create_collection(
            name=collection_name)

        # Initialize BM25 index
        self.bm25: BM25Okapi | None = None
        self.doc_texts: list[str] = []
        self.chunk_id_map: list[int] = []

        self._build_bm25_index()

    def _build_bm25_index(self) -> None:
        """
        Load all documents from ChromaDB and build in-memory BM25 index.
        """
        logger.info("Building BM25 index from existing ChromaDB chunks...")
        # Get all documents and metadata
        result = self.collection.get(include=["documents", "metadatas"])

        self.doc_texts = result.get("documents") or []
        metadatas = result.get("metadatas", [])

        if not self.doc_texts:
            logger.warning("No documents found in ChromaDB. BM25 index is empty.")
            return

        # Map list index to chunk_id (from metadata)
        self.chunk_id_map = []
        if metadatas:
            for metadata in metadatas:
                # Check if metadata is valid and has key
                if metadata and "chunk_id" in metadata:
                    chunk_id = metadata["chunk_id"]
                    # Store as int for consistent lookup
                    self.chunk_id_map.append(int(cast(Any, chunk_id)) \
                                            if chunk_id is not None else -1)
                else:
                    self.chunk_id_map.append(-1)

        # Tokenize (simple split by whitespace)
        tokenized_corpus = [doc.lower().split() for doc in self.doc_texts]
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"Built BM25 index with {len(self.doc_texts)} chunks.")

    def rebuild_bm25_index(self) -> None:
        """
        Rebuild the BM25 index.
        """
        logger.info("Rebuilding BM25 index...")
        self._build_bm25_index()
        logger.info("BM25 index rebuilt.")

    def add_chunk(self, chunk: Chunk) -> None:
        """
        Add a chunk to the vector store.
        
        Args:
            chunk (Chunk): The chunk to add.
            
        Returns:
            None
        """
        logger.info(f"Adding chunk: {chunk.id}")
        ids: list[str] = []
        texts: list[str] = []
        metadatas: list[Mapping[str, Any]] = []
        embeddings: list[list[float]] = []

        for index, sentence in enumerate(chunk.sentences):
            logger.debug(f"\tAdding sentence {index}: {sentence.text}")
            if sentence.embedding_vector is None:
                raise ValueError("Sentence embedding vector is None.")
            
            ids.append(f"{chunk.id}_{index}")
            texts.append(sentence.text)
            metadatas.append({"chunk_id": chunk.id})
            embeddings.append(sentence.embedding_vector)    # type: ignore

        logger.debug(f"Adding {len(ids)} sentences to vector store.")
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=cast(Any, embeddings)
            )
            # NOTE: BM25 index is NOT updated dynamically.
            # Restart required to index new content.
        except Exception as e:
            logger.error(f"Failed to add chunk to vector store: {e}")
            raise

    def hybrid_search(self,
                      query_text: str,
                      query_embedding: list[float],
                      k: int = 5) -> tuple[int, ...]:
        """
        Perform hybrid search (semantic + keyword) using reciprocal rank fusion.
        
        Args:
            query_text (str): The query text.
            query_embedding (list[float]): The query embedding.
            k (int): The number of results to return.
            
        Returns:
            tuple[int, ...]: The relevant chunk ids.
        """
        logger.info(f"Performing hybrid search for '{query_text}' (Top-{k})")

        # 1. Semantic search (Chroma)
        # Fetch more results initially to ensure we have enough candidates after filtering
        fetch_k = max(2*k, 20)
        semantic_results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=fetch_k
        )

        semantic_ranks = {}
        valid_semantic_chunk_ids = set()
        
        # Parse result: metadatas and distances
        if semantic_results["metadatas"] and semantic_results["distances"]:
            metadatas = semantic_results["metadatas"][0]
            distances = semantic_results["distances"][0]
            
            rank = 0
            for meta, distance in zip(metadatas, distances):
                chunk_id_val = meta.get("chunk_id")
                if chunk_id_val is not None:
                    chunk_id = int(cast(Any, chunk_id_val))
                    if distance <= self.config.relevance_threshold:
                        if chunk_id not in semantic_ranks:
                            semantic_ranks[chunk_id] = rank
                            rank += 1
                        valid_semantic_chunk_ids.add(chunk_id)
                    else:
                        logger.debug(f"Skipping semantic chunk {chunk_id} with distance {distance:.4f} > {self.config.relevance_threshold}")

        # If absolutely no semantic candidates passed the threshold, we return empty early.
        # This prevents returning entirely irrelevant results based solely on noise in BM25.
        if not valid_semantic_chunk_ids:
            logger.info(f"No semantic results passed the relevance threshold ({self.config.relevance_threshold}).")
            # We DONT return early anymore! BM25 might still find a strong keyword match.

        # 2. Keyword search (BM25)
        keyword_ranks = {}
        if self.bm25:
            # Strip stop words from the query! This prevents false positives on "wat is de".
            tokenized_query = [w for w in query_text.lower().split() if w not in STOP_WORDS]
            
            if tokenized_query:
                # Get scores
                scores = self.bm25.get_scores(tokenized_query)
                # Get top indices sorted by score descending
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:fetch_k]

                rank = 0
                for index in top_indices:
                    score = scores[index]
                    # A BM25 score > 2.0 acts as a reliable baseline filter.
                    if score > 3.0:       
                        if index < len(self.chunk_id_map):
                            chunk_id = self.chunk_id_map[index]
                            if chunk_id != -1:
                                if chunk_id not in keyword_ranks:
                                    keyword_ranks[chunk_id] = rank
                                    rank += 1

        # 3. Reciprocal Rank Fusion (RRF)
        # score = 1 / (rank + k_const)
        rrf_k = 60
        combined_scores = {}

        # We consider chunk_ids that are EITHER semantically valid OR strong keyword matches!
        all_ids = set(semantic_ranks.keys()) | set(keyword_ranks.keys())
        
        if not all_ids:
            logger.info("No candidates passed either the semantic threshold or the BM25 noise filter. Returning 0 results.")
            return tuple()

        logger.debug(f"RRF Scoring (Top candidates):")
        for chunk_id in all_ids:
            semantic_rank = semantic_ranks.get(chunk_id, fetch_k)  # Default penalty
            keyword_rank = keyword_ranks.get(chunk_id, fetch_k)
            score = (1.0 / (semantic_rank + rrf_k)) + (1.0 / (keyword_rank + rrf_k))
            combined_scores[chunk_id] = score

            # DEBUG LOGGING: Show detail only for top contenders to keep logs readable
            if semantic_rank < k or keyword_rank < k:
                logger.debug(f"  Chunk {chunk_id}: SemRank={semantic_rank}, KeyRank={keyword_rank} -> RRF={score:.6f}")

        # 4. Sort by RRF score descending
        sorted_results = sorted(combined_scores.items(),
                                key=lambda x: x[1], 
                                reverse=True)
        
        # 5. Return top k chunk_ids
        top_ids = [chunk_id for chunk_id, score in sorted_results[:k]]

        logger.info(f"Hybrid search filtered down to {len(top_ids)} relevant final candidates.")
        return tuple(top_ids)
        

    def query_chunk_ids(self, query_embedding: list[float], k: int = 5) -> tuple[int, ...]:
        """
        Query the vector store.
        
        Args:
            query_embedding (list[float]): The query embedding.
            k (int): The number of results to return.
            
        Returns:
            tuple[int, ...]: The relevant chunk ids.
        """
        logger.info(f"Querying vector store for {k} results.")
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=k
        )
        logger.debug(f"Query results: {results}")

        # Retrieve the relevant chunks from the results
        metadatas = results["metadatas"]
        distances = results["distances"]
        if not metadatas or not distances:
            return tuple(())
        
        relevant_chunk_ids: list[int] = []
        for meta_list, distance_list in zip(metadatas, distances):
            for metadata, distance in zip(meta_list, distance_list):
                if distance <= self.config.relevance_threshold:
                    relevant_chunk_ids.append(cast(int, metadata["chunk_id"]))
                else:
                    logger.debug(f"Skipping chunk {metadata['chunk_id']} with distance {distance:.4f} > {self.config.relevance_threshold}")
        
        logger.debug(f"Relevant chunk ids: {relevant_chunk_ids}")
        return tuple(set(relevant_chunk_ids))

    def delete_chunks_by_id(self, chunk_ids: tuple[int, ...]):
        """
        Delete chunks from the vector store.
        
        Args:
            chunk_ids (tuple[int, ...]): The ids of the chunks to delete.
            
        Returns:
            None
        """
        logger.debug(f"Deleting chunks: {chunk_ids}")
        for chunk_id in chunk_ids:
            logger.debug(f"\tDeleting chunk: {chunk_id}")
            self.collection.delete(
                where={"chunk_id": chunk_id}
            )
        logger.info(f"Deleted embeddings for {len(chunk_ids)} chunks.")

_vector_store_instances: dict[str, VectorStore] = {}

def get_vector_store(collection_name: str,
                     config: Config | None = None) -> VectorStore:
    """
    Get the vector store instance.
    
    Args:
        collection_name (str): The collection name.
        config (Config): The configuration.
        
    Returns:
        VectorStore: The vector store instance.
    """
    global _vector_store_instances

    logger.debug(f"Getting vector store instance for collection '{collection_name}'.")

    if config is None:
        config = Config.load()

    if collection_name not in _vector_store_instances:
        logger.debug(f"Creating new vector store instance for collection '{collection_name}'.")
        _vector_store_instances[collection_name] = VectorStore(config, collection_name)
    else:
        logger.debug(f"Using existing vector store instance for collection '{collection_name}'.")

    return _vector_store_instances[collection_name]
