from abc import ABC, abstractmethod

class BaseClass(ABC):
    """template for all available ec2mc commands to follow"""

    @abstractmethod
    def main(self, kwargs):
        """overridden by child class to describe command's functionality"""
        pass


    def add_documentation(self, argparse_obj):
        """initialize child's argparse entry and help"""
        return argparse_obj.add_parser(
            self.module_name(), help=self.docstring())


    def blocked_actions(self, kwargs):
        """return list of denied IAM actions needed for the child's main"""
        return []


    def module_name(self):
        """convert child class' __module__ to its module name"""
        return self.__class__.__module__.rsplit('.', 1)[-1]


    def docstring(self):
        """return main's docstring's first line for use in argparse"""
        return self.main.__doc__.splitlines()[0]
