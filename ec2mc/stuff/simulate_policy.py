import boto3

from ec2mc.stuff import quit_out

def blocked(user_info, *, actions=None, resources=None, context=None):
    """Tests whether IAM user is able to use AWS actions in actions.

    Args:
        user_info (dict): iam_id, iam_secret, and iam_arn are needed.
        actions (list): AWS action(s) to verify the IAM user can use.
        resources (list): Check if action(s) can be used on specific resources. 
            If None, action(s) must be usable on all resources.
        context (dict): Check if actions can be used with specific contexts. 
            If None, it is expected that no context restrictions were set.

    Returns:
        list: Actions denied by IAM due to insufficient permissions.
    """

    if actions is None:
        quit_out.q(["Error: Actions list required for simulate_policy"])

    if resources is None:
        resources = ["*"]

    if context is not None:
        # Convert dict to what ContextEntries expects.
        context_temp = []
        for context_key in context:
            context_temp.append({
                "ContextKeyName": context_key, 
                "ContextKeyValues": context[context_key], 
                "ContextKeyType": "string"
            })
        context = context_temp
    else:
        context = [{}]

    results = boto3.client("iam", 
        aws_access_key_id=user_info["iam_id"], 
        aws_secret_access_key=user_info["iam_secret"]
    ).simulate_principal_policy(
        PolicySourceArn=user_info["iam_arn"], 
        ActionNames=actions, 
        ResourceArns=resources, 
        ContextEntries=context
    )["EvaluationResults"]

    blocked_actions = []
    for result in results:
        if result["EvalDecision"] != "allowed":
            blocked_actions.append(result["EvalActionName"])

    return blocked_actions
