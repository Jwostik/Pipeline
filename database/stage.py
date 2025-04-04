from models import Stage
from pypika import PostgreSQLQuery


def create(pipeline_id: int, stage_index_in_pipeline: int, stage: Stage, curs=None) -> int:
    curs.execute(PostgreSQLQuery.into('stages').columns('pipeline_id', 'index_in_pipeline', 'type', 'params').insert(pipeline_id,
                                                                                                           stage_index_in_pipeline,
                                                                                                           stage.type,
                                                                                                           stage.params.toJSON()).returning(
        'stage_id').get_sql())
    stage_id, = curs.fetchone()
    return stage_id
