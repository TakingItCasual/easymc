from abc import ABC, abstractmethod

class BaseClass(ABC):
    """template for all available ec2mc commands to follow"""

    def __init__(self):
        super().__init__()


    @abstractmethod
    def main(self, kwargs):
        """overridden by child class to describe command's functionality"""
        pass


    @abstractmethod
    def add_documentation(self, argparse_obj):
        """initialize child's argparse entry and help"""
        module_name = self.module_name()
        return argparse_obj.add_parser(module_name,
            help=self.main.__doc__.splitlines()[0])


    @abstractmethod
    def blocked_actions(self, kwargs):
        """return list of denied IAM actions needed for the child's main"""
        pass


    @abstractmethod
    def module_name(self, name):
        """convert child class' __name__ to its module name

        Must be overridden in the child class like this:
            def module_name(self):
                return super().module_name(__name__)
        """
        return name.rsplit('.', 1)[-1]


    def docstring(self):
        """return main's docstring's first line for use in argparse"""
        return self.main.__doc__.splitlines()[0]
