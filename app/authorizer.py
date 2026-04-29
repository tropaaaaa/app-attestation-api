import os


def _policy(effect: str, method_arn: str):
    return {
        "principalId": "local-user",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [{
                "Action": "execute-api:Invoke",
                "Effect": effect,
                "Resource": method_arn,
            }],
        },
        "context": {"auth": "local-x-api-key"},
    }


def handler(event, context):
    headers = event.get("headers") or {}
    provided = (
        headers.get("x-api-key")
        or headers.get("X-Api-Key")
        or headers.get("X-API-KEY")
    )

    expected = os.environ.get("LOCAL_X_API_KEY", "")

    if expected and provided == expected:
        return _policy("Allow", event["methodArn"])

    return _policy("Deny", event["methodArn"])
