from pathlib import Path
from typing import Callable, List

from llama_index.data_structs.node import Node, DocumentRelationship

# from llama_index.data_structs.node import DocumentRelationship, Node

from loguru import logger

def get_nodes_from_documents(document_paths: List[Path], chunk_parser: Callable[[Path], List[str]]) -> List[Node]:
    """Gets list of nodes from a collection of documents

    Examples: https://gpt-index.readthedocs.io/en/stable/guides/primer/usage_pattern.html
    """

    all_nodes = []

    for path in document_paths:
        parsed_text_chunks = chunk_parser(path)  # Recieves list of text chunks as a result
        ids = [f"id_{path.name}_{i}" for i in range(len(parsed_text_chunks))]

        # Construct nodes from documents
        nodes = [Node(text=chunk, doc_id=id) for chunk, id in zip(parsed_text_chunks, ids)]

        for prev_node, next_node in zip(nodes[:-1], nodes[1:]):
            prev_node.relationships[DocumentRelationship.NEXT] = next_node.get_doc_id()
            next_node.relationships[DocumentRelationship.PREVIOUS] = prev_node.get_doc_id()

        all_nodes = all_nodes + nodes

    logger.info(f"Got {len(all_nodes)} nodes.")
    return all_nodes


def get_documents_from_langchain_splitter(document_paths: List[Path], splitter) -> List[Node]:
    """Gets list of nodes from a collection of documents

    Examples: https://gpt-index.readthedocs.io/en/stable/guides/primer/usage_pattern.html
    """

    all_docs = []

    for path in document_paths:
        logger.info(f"Processing path: {path}")
        with open(path, "r") as f:
            text = f.read()
            
        docs = splitter.create_documents([text])
        for d in docs:
            d.metadata = {"source": str(path)}
        all_docs.extend(docs)
        
    logger.info(f"Got {len(all_docs)} nodes.")
    return all_docs