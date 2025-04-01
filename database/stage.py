from models import Stage


def create(pipeline_id: int, stage_index_in_pipeline: int, stage: Stage, curs=None) -> int:
    curs.execute(
        "insert into stages (pipeline_id, index_in_pipeline, type, params) values (%s, %s, %s, %s) RETURNING stage_id",
        [pipeline_id, stage_index_in_pipeline, stage.type, stage.params.toJSON()])
    stage_id = curs.fetchone()
    return stage_id
