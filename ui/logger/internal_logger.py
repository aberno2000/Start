class InternalLogger:
    
    @staticmethod
    def pretty_function_details() -> str:
        """
        Prints the details of the calling function in the format:
        <file name>: line[<line number>]: <func name>(<args>)
        """
        from inspect import currentframe, getargvalues

        current_frame = currentframe()
        caller_frame = current_frame.f_back.f_back
        function_name = caller_frame.f_code.co_name
        args, _, _, values = getargvalues(caller_frame)
        function_file = caller_frame.f_code.co_filename
        formatted_args = ', '.join([f"{arg}={values[arg]}" for arg in args])
        return f"{function_file}: {function_name}({formatted_args})"

    @staticmethod
    def get_warning_none_result():
        return f"Warning, {InternalLogger.pretty_function_details()} returned '{None}' result"

    @staticmethod
    def get_warning_none_result_with_exception_msg(exmsg: str):
        return f"Warning, {InternalLogger.pretty_function_details()} returned '{None}' result. Exception: {exmsg}"
