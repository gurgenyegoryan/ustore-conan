import json
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.csv as csv
import pyarrow.dataset as ds
import ukv.umem as ukv
pa.get_include()


def test_table():
    db = ukv.DataBase()
    col = db.main

    docs = col.docs
    docs[0] = {'name': 'Lex', 'lastname': 'Fridman', 'tweets': 2221}
    docs[1] = {'name': 'Andrew', 'lastname': 'Huberman', 'tweets': 3935}
    docs[2] = {'name': 'Joe', 'lastname': 'Rogan', 'tweets': 45900}

    table = col.table

    # Tweets
    df_tweets = pd.DataFrame({'tweets': [2221, 3935, 45900]}, dtype=np.int32)
    assert table[['tweets']].astype('int32').loc([0, 1, 2]).to_arrow() \
        == pa.RecordBatch.from_pandas(df_tweets)

    # Names
    df_names = pd.DataFrame({'name': [b'Lex', b'Andrew', b'Joe']})
    assert table[['name']].astype(
        'bytes').to_arrow() == pa.RecordBatch.from_pandas(df_names)

    # Tweets and Names
    df_names_and_tweets = pd.DataFrame([
        {'name': 'Lex', 'tweets': 2221},
        {'name': 'Andrew', 'tweets': 3935},
        {'name': 'Joe', 'tweets': 45900}
    ])
    schema = pa.schema([
        pa.field('name', pa.binary()),
        pa.field('tweets', pa.int32())])

    assert table.astype({'name': 'bytes', 'tweets': 'int32'}
                        ).to_arrow() == pa.RecordBatch.from_pandas(df_names_and_tweets, schema)

    # Surnames and Names
    df_names_and_tweets = pd.DataFrame([
        {'name': 'Lex', 'lastname': 'Fridman'},
        {'name': 'Andrew', 'lastname': 'Huberman'},
        {'name': 'Joe', 'lastname': 'Rogan'}
    ])
    schema = pa.schema([
        pa.field('name', pa.binary()),
        pa.field('lastname', pa.binary())])

    assert table.astype({'name': 'bytes', 'lastname': 'bytes'}
                        ).to_arrow() == pa.RecordBatch.from_pandas(df_names_and_tweets, schema)

    # All
    all = pd.DataFrame([
        {'name': 'Lex', 'tweets': 2221, 'lastname': 'Fridman'},
        {'name': 'Andrew', 'tweets': 3935, 'lastname': 'Huberman'},
        {'name': 'Joe', 'tweets': 45900, 'lastname': 'Rogan'}
    ])
    schema = pa.schema([
        pa.field('name', pa.binary()),
        pa.field('tweets', pa.int32()),
        pa.field('lastname', pa.binary())])

    assert table.astype({'name': 'bytes', 'tweets': 'int32', 'lastname': 'bytes'}
                        ).to_arrow() == pa.RecordBatch.from_pandas(all, schema)

    # Update
    tweets = pa.array([2, 4, 5])
    names = pa.array(["Jack", "Charls", "Sam"])
    column_names = ["tweets", "name"]

    modifier = pa.RecordBatch.from_arrays([tweets, names], names=column_names)

    table.loc(slice(0, 2)).update(modifier)
    assert docs[0] == {'name': 'Jack', 'lastname': 'Fridman', 'tweets': 2}
    assert docs[1] == {'name': 'Charls', 'lastname': 'Huberman', 'tweets': 4}
    assert docs[2] == {'name': 'Sam', 'lastname': 'Rogan', 'tweets': 5}

    # CSV
    table.astype({'name': 'str', 'tweets': 'int64'}
                 ).to_csv("tmp/pandas.csv")

    df = table.astype({'name': 'str', 'tweets': 'int64'}
                      ).to_arrow()

    exported_df = csv.read_csv("tmp/pandas.csv").to_batches()[0]
    assert df == exported_df

    # Parquet
    table.astype({'name': 'str', 'tweets': 'int32'}
                 ).to_parquet("tmp/pandas.parquet")

    df = table.astype({'name': 'str', 'tweets': 'int32'}
                      ).to_arrow()

    exported_df = next(ds.dataset("tmp/pandas.parquet",
                       format="parquet").to_batches())
    assert df == exported_df

    # JSON
    expected_json = '''{"name":{"0":"Jack","1":"Charls","2":"Sam"},"tweets":{"0":2,"1":4,"2":5}}'''
    exported_json = table.to_json()
    assert exported_json == expected_json

    table.to_json("tmp/pandas.json")
    expected_json = json.loads(expected_json)
    f = open("tmp/pandas.json")
    exported_json = json.load(f)
    f.close()
    assert exported_json == expected_json
