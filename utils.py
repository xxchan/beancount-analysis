import csv
import io
from decimal import Decimal
import datetime

# copied from fava


def _result_array(types, rows) -> list[list[str]]:
    result_array = [[name for name, t in types]]
    for row in rows:
        result_array.append(_row_to_pyexcel(row, types))
    return result_array


def _row_to_pyexcel(row, header) -> list[str]:
    result = []
    for idx, column in enumerate(header):
        value = row[idx]
        if not value:
            result.append(value)
            continue
        type_ = column[1]
        if type_ == Decimal:
            result.append(float(value))
        elif type_ == int:
            result.append(value)
        elif type_ == set:
            result.append(" ".join(value))
        elif type_ == datetime.date:
            result.append(str(value))
        else:
            if not isinstance(value, str):
                raise TypeError(f"unexpected type {type(value)}")
            result.append(value)
    return result


def to_csv(types, rows) -> io.BytesIO:
    """Save result to CSV.

    Args:
        types: query result_types.
        rows: query result_rows.

    Returns:
        The (binary) file contents.
    """
    resp = io.StringIO()
    result_array = _result_array(types, rows)
    csv.writer(resp).writerows(result_array)
    return io.BytesIO(resp.getvalue().encode("utf-8"))
