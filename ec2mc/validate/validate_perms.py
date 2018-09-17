from ec2mc import consts
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
        # Convert context dict to list[dict] expected by ContextEntries.
        context = [{
            'ContextKeyName': context_key,
            'ContextKeyValues': [str(val) for val in context_values],
            'ContextKeyType': "string"
        } for context_key, context_values in context.items()]
    else:
        context = [{}]

    results = aws.iam_client().simulate_principal_policy(
        PolicySourceArn=consts.IAM_ARN,
        ActionNames=actions,
        ResourceArns=resources,
        ContextEntries=context
    )['EvaluationResults']

    return sorted([result['EvalActionName'] for result in results
        if result['EvalDecision'] != "allowed"])
