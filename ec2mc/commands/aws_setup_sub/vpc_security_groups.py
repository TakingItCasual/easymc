#from ec2mc import config
from ec2mc import update_template
#from ec2mc.stuff import aws
from ec2mc.stuff import simulate_policy
#from ec2mc.stuff import quit_out

class VPCSecurityGroupSetup(update_template.BaseClass):

    def verify_component(self):

        sg_names = {
            "AWSExtra": [],
            "ToCreate": [],
            "ToUpdate": [],
            "UpToDate": []
        }

        return sg_names


    def notify_state(self, component_info):
        pass


    def upload_component(self, component_info):
        pass


    def delete_component(self, component_info):
        pass


    def blocked_actions(self, kwargs):
        self.describe_actions = [
            "ec2:DescribeVpcs"
        ]
        self.upload_actions = [
            "ec2:CreateSecurityGroup",
            "ec2:AuthorizeSecurityGroupIngress"
        ]
        self.delete_actions = []
        return simulate_policy.blocked(actions=super().blocked_actions(kwargs))
