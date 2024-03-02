"""Abstract interface for document loader implementations."""
from collections.abc import Iterator
from typing import Optional

import camelot

from core.rag.extractor.blod.blod import Blob
from core.rag.extractor.extractor_base import BaseExtractor
from core.rag.models.document import Document
from extensions.ext_storage import storage
from mylogger import logger


class PdfExtractor(BaseExtractor):
    """Load pdf files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
            self,
            file_path: str,
            file_cache_key: Optional[str] = None
    ):
        """Initialize with file path."""
        self._file_path = file_path
        self._file_cache_key = file_cache_key

    def extract(self) -> list[Document]:
        plaintext_file_key = ''
        plaintext_file_exists = False
        if self._file_cache_key:
            try:
                text = storage.load(self._file_cache_key).decode('utf-8')
                plaintext_file_exists = True
                return [Document(page_content=text)]
            except FileNotFoundError:
                pass
        if "table" in self._file_path.lower() or "form" in self._file_path.lower() or "chart" in self._file_path.lower() \
                or "sheet" in self._file_path.lower():
            documents = []
            tables = camelot.read_pdf(self._file_path,
                                      # strip_text='\n',
                                      # line_tol=6,
                                      # line_scale=60)
                                      pages='1-end',
                                      compress=True)
            if tables:
                from pandas import DataFrame
                logger.info(len(tables))
                for index, t in enumerate(tables):
                    # print(t.df)
                    # 转化为文本，表格内\n替换
                    # print(t.df.to_string(index=False))
                    logger.info(DataFrame(t.df).shape)
                    _str = ""
                    for _, row in t.df.iterrows():
                        _str += "\t".join(row.values) + "\n\n"
                    _str = _str.rstrip("\n\n")
                    logger.info(len(_str.split("\n\n")))
                    documents.append(Document(page_content=_str, metadata={"source": self._file_path,
                                                                           "page": index}))
        else:
            documents = list(self.load())
        text_list = []
        for document in documents:
            text_list.append(document.page_content)
        text = "\n\n".join(text_list)

        # save plaintext file for caching
        if not plaintext_file_exists and plaintext_file_key:
            storage.save(plaintext_file_key, text.encode('utf-8'))

        return documents

    def load(
            self,
    ) -> Iterator[Document]:
        """Lazy load given path as pages."""
        blob = Blob.from_path(self._file_path)
        yield from self.parse(blob)

    def parse(self, blob: Blob) -> Iterator[Document]:
        """Lazily parse the blob."""
        import pypdfium2

        with blob.as_bytes_io() as file_path:
            pdf_reader = pypdfium2.PdfDocument(file_path, autoclose=True)
            try:
                for page_number, page in enumerate(pdf_reader):
                    text_page = page.get_textpage()
                    content = text_page.get_text_range()
                    text_page.close()
                    page.close()
                    metadata = {"source": blob.source, "page": page_number}
                    yield Document(page_content=content, metadata=metadata)
            finally:
                pdf_reader.close()
