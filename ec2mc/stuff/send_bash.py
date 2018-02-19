import boto3

def main(user_info, instance_id, cmd_list):
    ssm_client = boto3.client("ssm",
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"]
    )
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
