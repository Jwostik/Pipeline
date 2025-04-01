from fastapi_classes import Stage
import exceptions


def validate_stages(stages: dict[str, Stage]) -> bool:
    try:
        idxs = set(map(int, stages.keys()))
        if len(idxs) == 0:
            raise exceptions.NoStageException("There is no stages in pipeline")
        for i in range(len(idxs)):
            if i + 1 not in idxs:
                raise exceptions.InvalidStageNumerationException("Invalid stage numeration")
        return True
    except ValueError as e:
        raise exceptions.InvalidStageKeyException("Invalid stage key: " + str(e).split(': ')[-1])


