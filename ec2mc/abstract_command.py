from abc import ABC, abstractmethod

class CommandBase(ABC):
    """Template for (most of) the available script commands to follow."""

    def __init__(self):
        super().__init__()


    @abstractmethod
    def main(self):
        """Overridden by child class to describe command's functionality."""
        pass


    @abstractmethod
    def add_documentation(self, argparse_obj):
        """Initializes child's argparse entry and help."""
        module_name = self.module_name()
        return argparse_obj.add_parser(module_name, 
            usage="ec2mc " + module_name + " [-h] [<args>]", 
            help=self.main.__doc__.splitlines()[0])


    @abstractmethod
    def blocked_actions(self, user_info):
        """Returns list of denied IAM actions needed for the child's main."""
        pass


    @abstractmethod
    def module_name(self, name):
        """Gets module name. Child class needs to pass its __name__ to name."""
        return name.rsplit('.', 1)[-1]


def args_to_filter_instances(cmd_parser):
    """Initializes arguments for argparse that verify_instances:main needs."""
    cmd_parser.add_argument(
        "-r", dest="regions", nargs="+", metavar="", 
        help=("AWS EC2 region(s) to probe for instances. If not set, all "
            "regions will be probed."))
    cmd_parser.add_argument(
        "-t", dest="tagfilter", action="append", nargs="+", metavar="", 
        help=("Instance tag filter. First value is the tag key, with "
            "proceeding value(s) as the tag value(s). If not set, no filter "
            "will be applied. If tag value(s) not specified, only the tag key "
            "will be filtered for."))