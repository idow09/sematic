# Third-party
import datetime
import os
import pandas
import json

# Sematic
from sematic.types.serialization import get_json_encodable_summary
from sematic.db.models.factories import make_artifact


def test_dataframe_summary():
    df = pandas.read_csv(
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "cirrhosis.csv"),
        index_col=["ID"],
    )

    summary = get_json_encodable_summary(df, pandas.DataFrame)
    assert summary["shape"] == df.shape
    assert len(summary["dataframe"]) == 19
    assert len(list(summary["dataframe"].values())[0]) == 5
    assert len(summary["describe"]) == 12
    assert len(summary["isna"]) == 19


def test_dataframe_datetime():
    timestamp = datetime.datetime.now()
    df = pandas.DataFrame([dict(a=timestamp)])

    artifact = make_artifact(df, pandas.DataFrame)

    assert json.loads(artifact.json_summary)["dataframe"] == {
        "a": {"0": str(timestamp)}
    }
