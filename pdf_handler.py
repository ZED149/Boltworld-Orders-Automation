
# Imports!
import PyPDF2 as pdf2
import regex as re
from datetime import datetime

# PDFHandler
class PDFHandler:
    """Responsible for handling PDF's.
    """

    # private data members
    __pdf_name: str = None                                      # Name of the PDF
    reader = None                                         # Instance to handle pdf
    _orders_types_lists = ['web', 'ebay', 'payslips']           # A list containing all types of order names

    # constructor
    def __init__(self, filename: str):

        # Validations!
        assert type(filename) == str, "filename needs to be string"
        assert filename != "", "filename cannot be none"
        
        # initializing
        self.__pdf_name = filename
    
    # open
    def open(self):
        """Opens a PDF file.
        """
        with open(self.__pdf_name, 'rb') as file:
            self.reader = pdf2.PdfReader(self.__pdf_name, strict=False)

        # return self.reader
    
    # fetch_order_details
    def fetch_order_details(self, o_type: str) -> list:
        """Reads the PDF and fetch the details as specidifed by the order type.

        Args:
            o_type (str): Type of the order.
            It can be either ["web", "ebay", "payslips"]

        Returns:
            list: A list containing order details as per specified.
        """
        order_details = []
        from os import getlogin
        logged_in_user = getlogin()

        # validating o_type
        assert o_type != "", "o_type cannot be none"
        assert o_type in self._orders_types_lists

        for page in self.reader.pages:
            content = page.extract_text()
            if o_type == 'web':
                # using regex to extract order number patter
                data = re.search(string=content, pattern='Order[ ]Number..+[0-9]')
                if data:
                    date = datetime.now().date().strftime("%d-%m-%Y")
                    time = datetime.now().time().strftime("%I:%M %p")
                    # if a matching pattern is found, append the details to the list
                    order_details.append([data.group(0), date, time, logged_in_user])
            elif o_type == 'ebay':
                raise NotImplemented
            elif o_type == 'payslips':
                raise NotImplemented
            
        # splitting the list and then converting order numbers into int just to contain numbers only in integer format
        for order in order_details:
            order[0] = order[0].split(': ')[1]
            order[0] = int(order[0])
        
        return order_details
            
