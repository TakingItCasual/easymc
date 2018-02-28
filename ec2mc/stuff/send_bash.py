from ec2mc.verify import verify_aws

def main(instance_id, cmd_list):
    """Send bash commands to an instance via SSM"""
    quit_out.assert_empty(simulate_policy.blocked(actions=[
        "ssm:SendCommand"
    ]))
    
    ssm_client = verify_aws.ssm_client()
    response = ssm_client.send_command(
        InstanceIds=[
            instance_id
        ],
        DocumentName="AWS-RunShellScript",
        Parameters={
            "commands":[
                "ifconfig"
            ]
        }
    )
    command_id = response["Command"]["CommandId"]
    output = ssm_client.get_command_invocation(
        CommandId=command_id,
        InstanceId=instance_id,
    )
    print(output)
