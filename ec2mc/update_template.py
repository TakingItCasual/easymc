from abc import ABC, abstractmethod

class BaseClass(ABC):
    """template for aws_setup component verifying/uploading/deleting"""

    def __init__(self):
        super().__init__()


    @abstractmethod
    def verify_component(self):
        """check if AWS already has component, and if it is up-to-date"""
        pass


    @abstractmethod
    def upload_component(self):
        """create component on AWS if it doesn't exist, update if it exists"""
        pass


    @abstractmethod
    def delete_component(self):
        """remove component from AWS if it exists"""
        pass


    @abstractmethod
    def blocked_actions(self, kwargs):
        """check that IAM user is allowed to perform actions on component"""
        needed_actions = self.check_actions
        if kwargs["action"] == "upload":
            needed_actions.extend(self.upload_actions)
        elif kwargs["action"] == "delete":
            needed_actions.extend(self.delete_actions)
        return needed_actions
