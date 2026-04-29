from constants import HttpStatus


class HealthCheckService:
    @staticmethod
    def get_details(event, context):
        status_code = HttpStatus.HTTP_200
        request_id = event.get("requestContext", {}).get("requestId")
        result = {"message": "OK", "request_id": request_id}
        return status_code, result
