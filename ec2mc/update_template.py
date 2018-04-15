from abc import ABC, abstractmethod

from ec2mc.stuff import simulate_policy

class BaseClass(ABC):
    """template for aws_setup component verifying/uploading/deleting"""

    @abstractmethod
    def verify_component(self):
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
    def delete_component(self, component_info):
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
        return simulate_policy.blocked(actions=needed_actions)
