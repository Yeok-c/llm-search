import shutil
from pathlib import Path
from typing import List

from langchain.vectorstores import Chroma
from loguru import logger

from llmsearch.config import EmbeddingModel
from llmsearch.embeddings import get_embedding_model
from llmsearch.parsers.splitter import Document


class VectorStoreChroma:
    def __init__(self, persist_folder: str, embeddings_model_config: EmbeddingModel):
        self._persist_folder = persist_folder
        self._embeddings = get_embedding_model(embeddings_model_config)
        self.embeddings_model_config = embeddings_model_config

    def create_index_from_documents(
        self,
        all_docs: List[Document],
        clear_persist_folder: bool = True,
    ):
        if clear_persist_folder:
            pf = Path(self._persist_folder)
            if pf.exists() and pf.is_dir():
                logger.warning(f"Deleting the content of: {pf}")
                shutil.rmtree(pf)

        logger.info("Generating and persisting the embeddings..")
        vectordb = Chroma.from_documents(all_docs, self._embeddings, persist_directory=self._persist_folder)
        vectordb.persist()

    def load_retriever(self, **kwargs):
        vectordb = Chroma(persist_directory=self._persist_folder, embedding_function=self._embeddings)
        retriever = vectordb.as_retriever(**kwargs)
        return retriever
