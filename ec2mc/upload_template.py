from abc import ABC, abstractmethod

class BaseClass(ABC):
    """template for aws_setup component verifying/uploading to follow"""

    def __init__(self):
        super().__init__()


    @abstractmethod
    def verify(self, upload_confirmed):
        """check if AWS already has component, and if it needs updating"""
        pass


    @abstractmethod
    def upload(self):
        """create component on AWS if it doesn't exist, update if it exists"""
        pass
