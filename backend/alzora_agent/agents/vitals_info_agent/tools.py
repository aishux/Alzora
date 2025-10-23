from alzora_agent.setup import get_bigquery_data


def query_information_database(sql_query: str):
    """To get the information from bigquery database"""
    sql_query = sql_query.replace("```", "").replace("sql","")
    try:
        search_results = get_bigquery_data(sql_query)
        return [dict(row) for row in search_results]
    except Exception as e:
        print("Exception is: " + str(e))
        return "Couldn't parse your image file"