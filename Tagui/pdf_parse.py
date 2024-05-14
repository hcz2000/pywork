from io import StringIO
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import process_pdf
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
import re

def read_from_pdf(path):
    with open(path) as file:
        rm=PDFResourceManager()
        ret_str=StringIO()
        params=LAParams()
        converter=TextConverter(rm,ret_str,laparams=params)
        process_pdf(rm,converter,pdf)
        converter.close()
        content=ret_str.getvalue()




