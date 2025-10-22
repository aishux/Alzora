from alzora_agent.setup import *

def get_available_items(patient_id: int):
    available_items = get_bigquery_data(f'''
        SELECT DISTINCT(item_name) from alzora_datawarehouse.usual_spots WHERE patient_id={patient_id};
    ''')

    result = []

    for row in available_items:
        result.append(row.item_name)

    return result


def get_item_spots(item_name:str, patient_id:int):
    item_spots = get_bigquery_data(f'''
        SELECT location_description, created_at, updated_at 
        from alzora_datawarehouse.usual_spots 
        WHERE patient_id={patient_id} AND
        item_name='{item_name}'
        ORDER BY updated_at,created_at DESC;
    ''')

    return [dict(row) for row in item_spots]