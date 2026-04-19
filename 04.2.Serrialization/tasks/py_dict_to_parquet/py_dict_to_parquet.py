import pyarrow as pa
import pyarrow.parquet as pq


ValueType = int | list[int] | str | dict[str, str]

def _infer_type(value):
    if isinstance(value, int):
        return pa.int64()
    elif isinstance(value, str):
        return pa.string()
    elif isinstance(value, list):
        if all(isinstance(x, int) for x in value):
            return pa.list_(pa.int64())
    elif isinstance(value, dict):
        if all(isinstance(k, str) and isinstance(v, str) for k, v in value.items()):
            return pa.map_(pa.string(), pa.string())
    return 0

def save_rows_to_parquet(rows: list[dict[str, ValueType]], output_filepath: str) -> None:
    """
    Save rows to parquet file.

    :param rows: list of rows containing data.
    :param output_filepath: local filepath for the resulting parquet file.
    :return: None.
    """
    field_order = []
    field_types = {}
    field_presence = {}

    for row in rows:
        for key, value in row.items():
            if key not in field_types:
                field_order.append(key)
                field_types[key] = _infer_type(value)
                field_presence[key] = 1
            else:
                inferred = _infer_type(value)
                if not field_types[key].equals(inferred):
                    raise TypeError(f"Field {key} has different types")
                field_presence[key] += 1

    total_rows = len(rows)

    fields = []
    for key in field_order:
        nullable = field_presence[key] < total_rows
        fields.append(pa.field(key, field_types[key], nullable=nullable))

    schema = pa.schema(fields)

    columns = {key: [] for key in field_order}

    for row in rows:
        for key in field_order:
            columns[key].append(row.get(key, None))

    arrays = [pa.array(columns[key], type=field_types[key]) for key in field_order]

    table = pa.Table.from_arrays(arrays=arrays, schema=schema)

    pq.write_table(table, output_filepath)
