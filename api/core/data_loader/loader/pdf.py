import logging
from pprint import pprint
from typing import List, Optional

from langchain.document_loaders import PyPDFium2Loader, PDFPlumberLoader
import camelot
from langchain.document_loaders.base import BaseLoader
from langchain.schema import Document

from extensions.ext_storage import storage
from models.model import UploadFile

logger = logging.getLogger(__name__)


class PdfLoader(BaseLoader):
    """Load pdf files.


    Args:
        file_path: Path to the file to load.
    """

    def __init__(
        self,
        file_path: str,
        upload_file: Optional[UploadFile] = None
    ):
        """Initialize with file path."""
        self._file_path = file_path
        self._upload_file = upload_file

    def load(self) -> List[Document]:
        plaintext_file_key = ''
        plaintext_file_exists = False
        if self._upload_file:
            if self._upload_file.hash:
                plaintext_file_key = 'upload_files/' + self._upload_file.tenant_id + '/' \
                                     + self._upload_file.hash + '.0625.plaintext'
                try:
                    text = storage.load(plaintext_file_key).decode('utf-8')
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
                print(len(tables))
                for index, t in enumerate(tables):
                    # print(t.df)
                    # 转化为文本，表格内\n替换
                    # print(t.df.to_string(index=False))
                    print(DataFrame(t.df).shape)
                    _str = ""
                    for _, row in t.df.iterrows():
                        _str += "\t".join(row.values) + "\n\n"
                    _str = _str.rstrip("\n\n")
                    print(len(_str.split("\n\n")))
                    documents.append(Document(page_content=_str, metadata={"source": self._file_path,
                                                                           "page": index}))
        else:
            documents = PyPDFium2Loader(file_path=self._file_path).load()
        text_list = []

        # print(f"tables: {tables}")
        # old_document_length = len(documents)

        for document in documents:
            text_list.append(document.page_content)
        text = "\n\n".join(text_list)

        # save plaintext file for caching
        if not plaintext_file_exists and plaintext_file_key:
            storage.save(plaintext_file_key, text.encode('utf-8'))
        return documents


if __name__ == '__main__':
    # loader = PdfLoader(file_path='./Student Personal Info Form - Alexa Caramazza.pdf')
    # loader = PyPDFLoader(file_path='./Student Personal Info Form - Alexa Caramazza.pdf')
    # loader = PDFMinerLoader(file_path='./Student Personal Info Form - Alexa Caramazza.pdf')
    # loader = PDFMinerPDFasHTMLLoader(file_path='./Student Personal Info Form - Alexa Caramazza.pdf')
    # loader = PyMuPDFLoader(file_path='./Student Personal Info Form - Alexa Caramazza.pdf')
    # loader = PDFPlumberLoader(file_path='./Alexa Caramazza _ All Data (meetings) .pdf')
    # print(loader.load())
    # import camelot

    # tables = camelot.read_pdf('./Alexa Caramazza _ All Data (meetings) .pdf',
    #                           # strip_text='\n',
    #                           # line_tol=6,
    #                           # line_scale=60)
    #                           pages='1-end',
    #                           compress=True)
    # from pandas import DataFrame
    #
    # print(len(tables))
    # for t in tables:
    #     # print(t.df)
    #     # 转化为文本，表格内\n替换
    #     # print(t.df.to_string(index=False))
    #     print(DataFrame(t.df).shape)
    #     _str = ""
    #     for _, row in t.df.iterrows():
    #         _str += " ".join(row.values) + "\n\n"
    #     # 去掉最后的\n\n
    #     _str = _str.rstrip("\n\n")
    #     print(len(_str.split("\n\n")))
    # pass
    # documents = PdfLoader(file_path='./Alexa Caramazza _ All Data (meetings) .pdf').load()
    documents = PdfLoader(file_path='./Student Personal Info Form - Alexa Caramazza.pdf').load()
    # documents = PdfLoader(file_path='./Maria Arabo - Sheet 1.pdf').load()
    pprint(documents)

