from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):

    def __init__(self, page_size=20, max_page_size=100, page_size_query_param='page_size'):
        super().__init__()
        self.page_size = page_size
        self.max_page_size = max_page_size
        self.page_size_query_param = page_size_query_param

    def get_paginated_response(self, queryset, request, serializer_class):
        len_queryset = len(queryset)
        if request.query_params.get(self.page_size_query_param, '0') == '0' and len_queryset != 0:
            self.page_size = len_queryset
            self.max_page_size = len_queryset

        result_page = self.paginate_queryset(queryset, request)
        serializer = serializer_class(result_page, many=True)
        response = super().get_paginated_response(serializer.data)
        return response
