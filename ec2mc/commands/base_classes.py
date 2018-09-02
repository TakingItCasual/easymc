"""base classes to be inherited from for various purposes"""

from abc import ABC
from abc import abstractmethod

from ec2mc.validate import validate_perms

class CommandBase(ABC):
    """base class for most ec2mc command classes to inherit from"""

    @abstractmethod
    def main(self, kwargs):
        """overridden by child class to implement command's functionality"""
        pass


    def add_documentation(self, argparse_obj):
        """initialize child's argparse entry and help"""
        return argparse_obj.add_parser(
            self.module_name(), help=self.docstring())


    def blocked_actions(self, kwargs):
        """return list of denied IAM actions needed for child's main"""
        return []


    def module_name(self):
        """convert child class' __module__ to its module name"""
        return self.__class__.__module__.rsplit('.', 1)[-1]


    def docstring(self):
        """return main's docstring's first line (for use in argparse)"""
        return self.main.__doc__.splitlines()[0]


class ParentCommand(CommandBase):
    """base class for command which just acts as parent for other commands"""

    def main(self, kwargs):
        """Execute subcommand (action) based on argparse input (kwargs)"""
        chosen_cmd = next(cmd for cmd in self.sub_commands
            if cmd.module_name() == kwargs['action'])
        chosen_cmd.main(kwargs)


    def add_documentation(self, argparse_obj):
        """set up argparse for command and all of its subcommands"""
        cmd_parser = super().add_documentation(argparse_obj)
        actions = cmd_parser.add_subparsers(metavar="{action}", dest="action")
        actions.required = True
        for sub_command in self.sub_commands:
            sub_command.add_documentation(actions)


    def blocked_actions(self, kwargs):
        """pass along selected subcommand's required permissions"""
        chosen_cmd = next(cmd for cmd in self.sub_commands
            if cmd.module_name() == kwargs['action'])
        return chosen_cmd.blocked_actions(kwargs)


class ComponentSetup(ABC):
    """base class for aws_setup component checking/uploading/deleting"""

    @abstractmethod
    def check_component(self, config_aws_setup):
        """check if AWS already has component, and if it is up to date"""
        pass


    @abstractmethod
    def notify_state(self, component_info):
        """print the component's status relative to AWS"""
        pass


    @abstractmethod
    def upload_component(self, component_info):
        """create component on AWS if not present, update if present"""
        pass


    @abstractmethod
    def delete_component(self):
        """remove component from AWS if present"""
        pass


    @abstractmethod
    def blocked_actions(self, sub_command):
        """check whether IAM user is allowed to perform actions on component

        Must be overridden by child classes in the following fashion:
            def blocked_actions(self, sub_command):
                self.describe_actions = []
                self.upload_actions = []
                self.delete_actions = []
                return super().blocked_actions(sub_command)
        """
        needed_actions = self.describe_actions
        if sub_command == "upload":
            needed_actions.extend(self.upload_actions)
        elif sub_command == "delete":
            needed_actions.extend(self.delete_actions)
        return validate_perms.blocked(actions=needed_actions)
