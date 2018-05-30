from ec2mc.utils import aws
from ec2mc.utils import halt
from ec2mc.verify import verify_perms

def main(instance_id, cmd_list):
    """send bash command(s) to an instance via SSM"""
    halt.assert_empty(verify_perms.blocked(actions=[
        "ssm:SendCommand",
        "ssm:GetCommandInvocation"
    ]))

    ssm_client = aws.ssm_client()
    command_id = ssm_client.send_command(
        InstanceIds=[
            instance_id
        ],
        DocumentName="AWS-RunShellScript",
        Parameters={
            "commands": cmd_list
        }
    )["Command"]["CommandId"]
    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id,
    )
    print(output)
