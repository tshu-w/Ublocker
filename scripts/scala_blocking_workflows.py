import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parents[1]))

from src.baselines.blocking_workflows import blocking_workflows


def main():
    data_dirs = [
        d
        for d in Path("./data/blocking").iterdir()
        if d.name in ["songs", "citeseer-dblp"]
    ]
    sizes = [100, 1000, 10000, 100000, 1000000]
    # for d in data_dirs:
    #     for f in Path(d).glob("[1-2]*.csv"):
    #         df = pd.read_csv(f, low_memory=False)
    #         for i in sizes:
    #             sub_f = d / f"{f.stem}_{i}.csv"
    #             sub_df = df.head(i)
    #             sub_df.to_csv(sub_f, index=False)

    for d in data_dirs:
        print(d.name)
        for i in sizes:
            print(i)
            blocking_workflows(data_dir=d, size=str(i))


if __name__ == "__main__":
    main()
