# src/helpers/sql_helper.py

def read_sql_file(file_path: str) -> str:
    """
    Reads the content of a SQL file.
    """
    with open(file_path, 'r') as f:
        return f.read()

def create_query(sql_content: str, params: dict) -> str:
    """
    Replaces placeholders in a SQL query with the provided parameters.
    Placeholders should be in the format #placeholder_name.
    """
    for key, value in params.items():
        sql_content = sql_content.replace(f"#{key}", str(value))
    return sql_content
