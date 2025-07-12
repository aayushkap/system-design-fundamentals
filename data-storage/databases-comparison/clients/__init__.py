class DBClient:
    def create_schema(self):
        raise NotImplementedError("This method should be overridden by subclasses")

    def get_all_tables(self):
        raise NotImplementedError("This method should be overridden by subclasses")

    def execute_query(self, query):
        raise NotImplementedError("This method should be overridden by subclasses")