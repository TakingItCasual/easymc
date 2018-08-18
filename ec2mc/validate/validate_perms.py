from ec2mc import config
from ec2mc.utils import aws

def blocked(actions, resources=None, context=None):
    """test whether IAM user is able to use specified AWS action(s)

    Args:
        actions (list): AWS action(s) to validate IAM user can use.
        resources (list): Check if action(s) can be used on resource(s). 
            If None, action(s) must be usable on all resources ("*").
        context (dict): Check if action(s) can be used with context(s). 
            If None, it is expected that no context restrictions were set.

    Returns:
        list: Actions denied by IAM due to insufficient permissions.
    """
    if not actions:
        return []
    actions = list(set(actions))

    if resources is None:
        resources = ["*"]

    if context is not None:
        # Convert context dict to what ContextEntries expects.
        context_temp = []
        for context_key in context:
            context_temp.append({
                'ContextKeyName': context_key,
                'ContextKeyValues': [str(val) for val in context[context_key]],
                'ContextKeyType': "string"
            })
        context = context_temp
    else:
        context = [{}]

    results = aws.iam_client().simulate_principal_policy(
        PolicySourceArn=config.IAM_ARN,
        ActionNames=actions,
        ResourceArns=resources,
        ContextEntries=context
    )['EvaluationResults']

    blocked_actions = []
    for result in results:
        if result['EvalDecision'] != "allowed":
            blocked_actions.append(result['EvalActionName'])

    return sorted(blocked_actions)
