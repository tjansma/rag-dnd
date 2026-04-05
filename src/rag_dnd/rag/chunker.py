"""
Chunker for markdown text based on headers.
"""
from hashlib import sha256
from pathlib import Path
import logging
from typing import get_args,List, Literal

from langchain_text_splitters import MarkdownHeaderTextSplitter
import nltk

from .models import RAGDocument, Chunk, Sentence

def load_document_text(source_file: Path) -> str:
    """
    Load the text of a text-document.
    
    Args:
        source_file (Path): The path to the document file.
        
    Returns:
        str: The text of the document.
    """
    logger.debug(f"Loading document text: {source_file}")
    with open(source_file, "r") as f:
        return f.read()

logger = logging.getLogger(__name__)

ChunkingStrategy = Literal["heading1", "heading2", "heading3"]


class Chunker:
    """
    A class for chunking markdown text based on headers.
    """
    def __init__(self, strategy: ChunkingStrategy = "heading1") -> None:
        """
        Initialize the Chunker with a specific strategy.
        
        Args:
            strategy (str): The strategy to use for chunking. 
                            Must be one of the known strategies.
        """
        logger.debug(f"Initializing Chunker with strategy: {strategy}")
        
        # Zorg dat NLTK eenmalig zijn model pakt zonder interactieve terminal balkjes
        try:
            nltk.data.find('tokenizers/punkt_tab')
        except LookupError:
            logger.info("Downloading NLTK punkt_tab tokenizer for first usage...")
            nltk.download('punkt_tab', quiet=True)
            
        valid_strategies = get_args(ChunkingStrategy)
        if strategy not in valid_strategies:
            logger.error(
                f"Unknown strategy: {strategy}. Valid strategies: "
                f"{valid_strategies}")
            raise ValueError(
                f"Unknown strategy: {strategy}. Valid strategies: "
                f"{valid_strategies}")
        
        self.strategy = strategy

    def chunk(self, document: RAGDocument, source_file: Path) -> List[Chunk]:
        """
        Chunks the text based on the strategy.
        
        Args:
            document (RAGDocument): The document to chunk.
            source_file (Path): The path to the source file on disk.
        
        Returns:
            List[Chunk]: A list of chunks.
            
        Raises:
            FileNotFoundError: If the source file is not found.
        """
        logger.debug(f"Chunking document: {document.custom_filename}")
        try:
            text = load_document_text(source_file)
        except FileNotFoundError:
            logger.error(f"Source file {source_file} not found.")
            raise

        # Define the headers to split on
        headers_to_split_on = [
            ("#", "Header 1")
        ]
        if self.strategy == "heading2":
            headers_to_split_on.append(("##", "Header 2"))
        elif self.strategy == "heading3":
            headers_to_split_on.append(("##", "Header 2"))
            headers_to_split_on.append(("###", "Header 3"))

        logger.debug(f"Splitting text into chunks with headers: {headers_to_split_on}")
        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        langchain_docs = markdown_splitter.split_text(text)
        logger.debug(f"Split text into {len(langchain_docs)} chunks.")

        logger.debug(f"Creating chunks from {len(langchain_docs)} documents.")
        chunks = []
        for langchain_doc in langchain_docs:
            chunk = Chunk(parent_rag_document=document,
                          text=langchain_doc.page_content,
                          chunk_hash=sha256(
                            langchain_doc.page_content.encode()).hexdigest())
            
            # Create sentences
            logger.debug(f"Creating sentences from chunk: {chunk.id}")
            chunk.sentences = []
            
            # Split text into sentences using NLTK NLP models
            sentences_text = nltk.sent_tokenize(chunk.text, language="dutch")
            logger.debug(f"Split text into {len(sentences_text)} sentences.")
            
            for s_text in sentences_text:
                if s_text.strip() != "":
                    sentence = Sentence(text=s_text.strip(), chunk=chunk)
                    chunk.sentences.append(sentence)

            chunks.append(chunk)

        logger.info(f"Created {len(chunks)} chunks.")
        return chunks
