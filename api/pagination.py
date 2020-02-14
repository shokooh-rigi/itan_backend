from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    _page_size_temp = 0
    _max_page_size_temp = 0

    def __init__(self, page_size=20, max_page_size=100, page_size_query_param='page_size'):
        super().__init__()
        self.page_size = page_size
        self.max_page_size = max_page_size
        self.page_size_query_param = page_size_query_param

    def _backup_page_size(self):
        self._page_size_temp = self.page_size
        self._max_page_size_temp = self.max_page_size

    def _restore_page_size(self):
        self.page_size = self._page_size_temp
        self.max_page_size = self._max_page_size_temp

    def _set_page_size(self, page_size, max_page_size):
        self.page_size = page_size
        self.max_page_size = max_page_size

    def get_paginated_response(self, queryset, request, map_func, serializer_class):
        self._backup_page_size()
        len_queryset = len(queryset)
        if request.query_params.get(self.page_size_query_param, '0') == '0' and len_queryset != 0:
            self._set_page_size(len_queryset, len_queryset)

        result_page = self.paginate_queryset(queryset, request)
        results = result_page if map_func is None else map_func(result_page)
        serializer = serializer_class(results, many=True)
        response = super().get_paginated_response(serializer.data)
        self._restore_page_size()
        return response
