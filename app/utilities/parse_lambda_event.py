import json
import base64


class ParseLambdaEvent:

    @staticmethod
    def get_request_body_dict(event):
        content_type = ParseLambdaEvent.get_request_content_type_str(event)
        body = event.get("body") or ""

        if event.get("isBase64Encoded", False):
            body_bytes = base64.b64decode(body)
        else:
            body_bytes = body.encode("utf-8")

        if content_type and "application/json" in content_type.lower():
            try:
                return json.loads(body_bytes)
            except json.JSONDecodeError:
                return None
        else:
            return body_bytes

    @staticmethod
    def get_request_header_dict(event):
        headers = event.get("headers") or {}
        return headers

    @staticmethod
    def get_request_content_type_str(event):
        headers = event.get("headers") or {}
        content_type = headers.get("content-type") or headers.get("Content-Type")
        return content_type

    @staticmethod
    def get_http_method_str(event):
        return event.get("httpMethod")

    @staticmethod
    def get_path_str(event):
        return event.get("path")

    @staticmethod
    def get_request_id(event):
        return event.get("requestContext", {}).get("requestId")

    @staticmethod
    def get_request_query_params(event):
        return event.get("queryStringParameters")
