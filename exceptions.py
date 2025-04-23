class NoStageException(Exception):
    pass


class PipelineNameConflictException(Exception):
    pass


class QueryParameterException(Exception):
    pass


class NoPipelineException(Exception):
    pass


class NoJobException(Exception):
    pass


class StageExecutionException(Exception):
    pass


class HTTPStageException(StageExecutionException):
    pass


class JQStringException(StageExecutionException):
    pass
