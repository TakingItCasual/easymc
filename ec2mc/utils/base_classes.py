"""base classes to be inherited from for various purposes"""

from abc import ABC
from abc import abstractmethod
import argparse

from ec2mc.validate import validate_perms

class CommandBase(ABC):
    """base class for most ec2mc command classes to inherit from"""
    _module_postfix = "_cmd"

    def __init__(self, cmd_args):
        pass


    @abstractmethod
    def main(self, cmd_args):
        """overridden by child class to implement command's functionality"""
        pass


    @classmethod
    def add_documentation(cls, argparse_obj):
        """initialize child's argparse entry and help"""
        return argparse_obj.add_parser(cls.cmd_name(), help=cls.cmd_doc())


    def blocked_actions(self, cmd_args):
        """return list of denied IAM actions needed for child's main"""
        return []


    @classmethod
    def cmd_name(cls):
        """convert child class' __module__ to name of argparse command"""
        name_str = cls.__module__.rsplit('.', 1)[-1]
        if not name_str.endswith(cls._module_postfix):
            raise ImportError(f"{name_str} module name must end with "
                f"\"{cls._module_postfix}\".")
        return name_str[:-len(cls._module_postfix)]


    @classmethod
    def cmd_doc(cls):
        """return first line of main method's docstring"""
        return cls.main.__doc__.split("\n", 1)[0]


class ParentCommand(CommandBase):
    """base class for command which just acts as parent for other commands"""
    _module_postfix = "_cmds"
    sub_commands = []

    def __init__(self, cmd_args):
        self.chosen_cmd = next(cmd(cmd_args) for cmd in self.sub_commands
            if cmd.cmd_name() == cmd_args['subcommand'])


    def main(self, cmd_args):
        """Execute chosen subcommand"""
        self.chosen_cmd.main(cmd_args)


    @classmethod
    def add_documentation(cls, argparse_obj):
        """set up argparse for command and all of its subcommands"""
        cmd_parser = super().add_documentation(argparse_obj)
        subcommands = cmd_parser.add_subparsers(
            title="subcommands", metavar="<subcommand>", dest="subcommand")
        subcommands.required = True
        for sub_command in cls.sub_commands:
            sub_command.add_documentation(subcommands)


    def blocked_actions(self, cmd_args):
        """pass along selected subcommand's denied IAM actions"""
        return self.chosen_cmd.blocked_actions(cmd_args)


class ComponentSetup(ABC):
    """base class for aws_setup component checking/uploading/deleting"""
    describe_actions = []
    upload_actions = []
    delete_actions = []

    def __init__(self, config_aws_setup):
        pass


    @abstractmethod
    def check_component(self):
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


    @classmethod
    @abstractmethod
    def blocked_actions(cls, sub_command):
        """check whether IAM user is allowed to perform actions on component

        Should be overridden by child classes in the following fashion:
            @classmethod
            def blocked_actions(cls, sub_command):
                cls.describe_actions = []
                cls.upload_actions = []
                cls.delete_actions = []
                return super().blocked_actions(sub_command)
        """
        needed_actions = cls.describe_actions
        if sub_command == "upload":
            needed_actions.extend(cls.upload_actions)
        elif sub_command == "delete":
            needed_actions.extend(cls.delete_actions)
        return validate_perms.blocked(actions=needed_actions)


class ProperIndentParser(argparse.ArgumentParser):
    """Use formatter_class that properly indents help in subparsers"""

    def __init__(self, *args, **kwargs):
        formatter_class = lambda prog: ProperIndentFormatter(prog)
        argparse.ArgumentParser.__init__(
            self, *args, **kwargs, formatter_class=formatter_class)


class ProperIndentFormatter(argparse.HelpFormatter):
    """Corrected _max_action_length for the indenting of subactions

    Source: https://stackoverflow.com/a/32891625/2868017
    """

    def add_argument(self, action):
        if action.help is not argparse.SUPPRESS:
            # find all invocations
            get_invocation = self._format_action_invocation
            invocations = [get_invocation(action)]
            current_indent = self._current_indent
            for subaction in self._iter_indented_subactions(action):
                # compensate for the indent that will be added
                indent_chg = self._current_indent - current_indent
                added_indent = "x"*indent_chg
                invocations.append(added_indent + get_invocation(subaction))

            # update the maximum item length
            invocation_length = max([len(s) for s in invocations])
            action_length = invocation_length + self._current_indent
            self._action_max_length = max(
                self._action_max_length, action_length)

            # add the item to the list
            self._add_item(self._format_action, [action])
