from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 100


def paginate_queryset_response(request, queryset, serializer_class, *, context=None, extra_data=None):
    """
    Helper that paginates a queryset for APIView-based endpoints.
    """
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(page, many=True, context=context)
    response = paginator.get_paginated_response(serializer.data)

    if extra_data:
        # Ensure we don't mutate the response object in place without copying.
        response.data.update(extra_data)
    return response


