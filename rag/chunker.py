"""
Chunker for markdown text based on headers.
"""
from hashlib import sha256
from typing import get_args,List, Literal

from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents.base import Document

from .models import Document, Chunk, Sentence
from .services import load_document_text

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
        valid_strategies = get_args(ChunkingStrategy)
        if strategy not in valid_strategies:
            raise ValueError(
                f"Unknown strategy: {strategy}. Valid strategies: "
                f"{valid_strategies}")
        
        self.strategy = strategy

    def chunk(self, document: Document) -> List[Chunk]:
        """
        Chunks the text based on the strategy.
        
        Args:
            text (str): The text to chunk.
        
        Returns:
            List[Chunk]: A list of chunks.
        """
        try:
            text = load_document_text(document)
        except FileNotFoundError:
            raise FileNotFoundError(f"Document {document.file_name} not found.")

        # Define the headers to split on
        headers_to_split_on = [
            ("#", "Header 1")
        ]
        if self.strategy == "heading2":
            headers_to_split_on.append(("##", "Header 2"))
        if self.strategy == "heading3":
            headers_to_split_on.append(("##", "Header 2"))
            headers_to_split_on.append(("###", "Header 3"))

        markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
        langchain_docs = markdown_splitter.split_text(text)

        # Create chunks
        chunks = []
        for langchain_doc in langchain_docs:
            chunk = Chunk(parent_document=document,
                          text=langchain_doc.page_content,
                          chunk_hash=sha256(
                            langchain_doc.page_content.encode()).hexdigest())
            
            # Create sentences
            chunk.sentences = []
            for line in chunk.text.split("\n"):
                if line.strip() != "":
                    sentence = Sentence(text=line.strip(), chunk=chunk)
                    chunk.sentences.append(sentence)

            chunks.append(chunk)

        return chunks
