from ec2mc import update_template

class IAMGroupSetup(update_template.BaseClass):

    def verify_component(self):
        pass


    def notify_state(self):
        pass


    def upload_component(self):
        pass


    def delete_component(self):
        pass


    def blocked_actions(self, kwargs):
        self.check_actions = []
        self.upload_actions = []
        self.delete_actions = []
        return simulate_policy.blocked(actions=super().blocked_actions(kwargs))
