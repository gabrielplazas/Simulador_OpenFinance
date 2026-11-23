from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None or "errors" in response.data:
        return response
    detail = response.data.get("detail", response.data) if isinstance(response.data, dict) else response.data
    response.data = {"errors": [{"code": getattr(detail, "code", "INVALID_REQUEST").upper(),
                                 "title": response.reason_phrase, "detail": str(detail)}]}
    return response
