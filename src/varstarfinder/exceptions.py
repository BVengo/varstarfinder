class OrderError(Exception):
    def __init__(self, func_flags: dict, missing_func: str):
        """
        Raised when functions are called out of order
        :param func_flags: A dictionary of flags named in the order of the functions to be called.
        :param missing_func: A function that should have been called previously
        """
        super().__init__(f"Messages are called out of order! The required previous function {missing_func} has not been"
                         f" used. The correct order should be {func_flags}")

