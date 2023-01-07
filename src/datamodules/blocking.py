import os
import warnings
from pathlib import Path
from typing import Optional

import pandas as pd
from pytorch_lightning import LightningDataModule
from pytorch_lightning.utilities.types import TRAIN_DATALOADERS
from torch.utils.data import ConcatDataset, DataLoader, Dataset

from src.models import DeepBlocker
from src.utils import dict2tuples
from src.utils.sequential_loader import SequentialLoader

os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings(
    "ignore", ".*Consider increasing the value of the `num_workers` argument*"
)


class TableDataset(Dataset):
    def __init__(
        self,
        table_path: Path,
        index_col: str = "id",
    ):
        self.df = pd.read_csv(table_path, low_memory=False)
        self.df = self.df.fillna("")
        columns = list(self.df.columns)
        columns.remove(index_col)
        self.df[columns] = self.df[columns].astype(str)
        self.index_col = index_col

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, index) -> list[tuple]:
        return dict2tuples(self.df.iloc[index].to_dict(), ignored_cols=[self.index_col])


class Blocking(LightningDataModule):
    def __init__(
        self,
        data_dir: str = "./data/blocking/walmart-amazon_heter",
        index_col: str = "id",
        batch_size: int = 32,
        num_workers: int = 0,
        pin_memory: bool = False,
    ):
        super().__init__()
        self.save_hyperparameters()

        self.table_paths = sorted(Path(data_dir).glob("[1-2]*.csv"))
        self.matches_path = Path(data_dir) / "matches.csv"

    def setup(self, stage: Optional[str] = None) -> None:
        if not hasattr(self, "datasets"):
            self.datasets = [
                TableDataset(t, index_col=self.hparams.index_col)
                for t in self.table_paths
            ]

            if (
                isinstance(self.trainer.model, DeepBlocker)
                and self.trainer.model.hparams.aggregator_type == "sif"
            ):
                self.trainer.model.collate_fn.prepare(ConcatDataset(self.datasets))

        if not hasattr(self, "matches"):
            self.matches = set(
                pd.read_csv(self.matches_path).itertuples(index=False, name=None)
            )

        self.collate_fn = getattr(self.trainer.model, "collate_fn", None)

    def train_dataloader(self) -> TRAIN_DATALOADERS:
        dataloaders = (
            DataLoader(
                dataset=dataset,
                batch_size=self.hparams.batch_size,
                num_workers=self.hparams.num_workers,
                pin_memory=self.hparams.pin_memory,
                collate_fn=self.collate_fn,
                persistent_workers=self.hparams.num_workers > 0,
                shuffle=True,
            )
            for dataset in self.datasets
        )
        return SequentialLoader(*dataloaders)


class Blockings(LightningDataModule):
    def __init__(
        self,
        data_dir: str = "./data/blocking",
        batch_size: int = 32,
        num_workers: int = 0,
        pin_memory: bool = False,
    ):
        super().__init__()
        self.save_hyperparameters()
        self.data_dir = Path(data_dir)

    def setup(self, stage: Optional[str] = None) -> None:
        if not hasattr(self, "tables"):
            self.tables = []
            for d in self.data_dir.iterdir():
                if d.name not in ["songs", "citeseer-dblp"]:
                    table_paths = sorted(Path(d).glob("[1-2]*.csv"))
                    self.tables.extend([TableDataset(t) for t in table_paths])

        self.collate_fn = getattr(self.trainer.model, "collate_fn", None)
        self.hparams.num_workers = self.trainer.num_devices * 4

    def train_dataloader(self) -> TRAIN_DATALOADERS:
        dataloaders = (
            DataLoader(
                dataset=table,
                batch_size=self.hparams.batch_size,
                num_workers=self.hparams.num_workers,
                pin_memory=self.hparams.pin_memory,
                collate_fn=self.collate_fn,
                persistent_workers=self.hparams.num_workers > 0,
                shuffle=True,
            )
            for table in self.tables
        )
        return SequentialLoader(*dataloaders)
