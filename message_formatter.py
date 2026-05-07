# Created:  at 18-10-2025, Sat    (D,M,Y)
# Author:   Salman Ahmad

from abc import ABC, abstractmethod

# MessageFormatter
class MessageFormatter(ABC):
    """Abstract class for the message formatter of any type

    Args:
        ABC (_type_): _description_
    """
    
    @abstractmethod
    def format(self):
        pass
