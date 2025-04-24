class PaginatedResponse:
    """Helper class to standardize pagination responses"""

    @staticmethod
    def create(query, schema, page=1, per_page=20):
        """
        Create a paginated response from a query

        Args:
            query: SQLAlchemy query object
            schema: Function to convert items to dict
            page: Page number
            per_page: Items per page

        Returns:
            dict: Standardized pagination response
        """
        pagination = query.paginate(page=page, per_page=per_page,error_out=False)

        return {
            'items': [schema(item) for item in pagination.items],
            'meta': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev,
                'next_page': pagination.next_num if pagination.has_next else None,
                'prev_page': pagination.prev_num if pagination.has_prev else None
            }
        }
