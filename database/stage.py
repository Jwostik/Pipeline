from pypika import PostgreSQLQuery, Table

from models import Stage


def create(pipeline_id: int, stage_index_in_pipeline: int, stage: Stage, curs=None) -> int:
    curs.execute(
        PostgreSQLQuery.into('stages').columns('pipeline_id', 'index_in_pipeline', 'type', 'params').insert(pipeline_id,
                                                                                                            stage_index_in_pipeline,
                                                                                                            stage.type,
                                                                                                            stage.params.toJSON()).returning(
            'stage_id').get_sql())
    stage_id, = curs.fetchone()
    return stage_id


def execute(stage_id, data, curs=None):
    '''
    Выполнение стадии
    '''
    stage_table = Table('stages')
    curs.execute(PostgreSQLQuery.from_(stage_table).select('pipeline_id', 'index_in_pipeline', 'params').where(
        stage_table.stage_id == stage_id).get_sql())
    pipeline_id, index_in_pipeline, params = curs.fetchone()
    curs.execute(PostgreSQLQuery.from_(stage_table).select('stage_id').where(
        stage_table.pipeline_id == pipeline_id and stage_table.index_in_pipeline == index_in_pipeline + 1).get_sql())
    fetch_result = curs.fetchone()
    if fetch_result is None:
        next_stage = -1
    else:
        next_stage = fetch_result[0]
    data["stage_" + str(index_in_pipeline)] = 'completed'
    return next_stage, data
