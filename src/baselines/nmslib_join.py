from pathlib import Path
from typing import Callable, Optional

import nmslib
import pandas as pd
from jsonargparse import CLI
from rich import print

from src.utils import evaluate
from src.utils.nnblocker import NMSLIBIndexer, NNBlocker, SparseVectorizer


def nmslib_join(
    data_dir: str = "./data/blocking/cora",
    size: str = "",
    index_col: str = "id",
    tokenizer: Optional[Callable] = None,
    n_neighbors: int = 100,
    M: int = 30,
    efC: int = 1000,
    threads: int = 12,
):
    table_paths = sorted(Path(data_dir).glob(f"[1-2]*{size}.csv"))
    dfs = [pd.read_csv(p, index_col=index_col) for p in table_paths]

    vectorizer = SparseVectorizer(dfs[-1], vectorizer_kwargs={"tokenizer": tokenizer})
    indexer = NMSLIBIndexer(
        init_kwargs={
            "method": "hnsw",
            "space": "cosinesimil_sparse",
            "data_type": nmslib.DataType.SPARSE_VECTOR,
        },
        index_params={"M": M, "indexThreadQty": threads, "efConstruction": efC},
        query_params={},
        threads=threads,
    )
    blocker = NNBlocker(dfs, vectorizer, indexer)
    candidates = blocker(k=n_neighbors)

    if size != "":
        # shortcut for scalability experiments
        return

    matches_path = Path(data_dir) / "matches.csv"
    matches = set(pd.read_csv(matches_path).itertuples(index=False, name=None))
    metrics = evaluate(candidates, matches)

    print(metrics)
    return metrics


if __name__ == "__main__":
    CLI(nmslib_join)
