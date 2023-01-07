import random
from collections.abc import Callable

import nlpaug.augmenter.char as nac
import nlpaug.augmenter.word as naw
import nltk
from scipy.stats import bernoulli

nltk.data.path.append("./data/nltk")


class Augmenter(Callable):
    actions = [
        nac.OcrAug(),
        nac.KeyboardAug(),
        nac.RandomCharAug(action="insert"),
        nac.RandomCharAug(action="substitute"),
        nac.RandomCharAug(action="swap"),
        nac.RandomCharAug(action="delete"),
        naw.SpellingAug(),
        # naw.WordEmbsAug(model_type="fasttext", model=nlpaug.model.word_embs.Fasttext()),
        # naw.ContextualWordEmbsAug(
        #     model_type="roberta",
        #     model_path="./models/roberta-base",
        #     action="insert",
        # ),
        # naw.ContextualWordEmbsAug(
        #     model_type="roberta",
        #     model_path="./models/roberta-base",
        #     action="substitute",
        # ),
        naw.SynonymAug(aug_src="wordnet"),
        naw.RandomWordAug(action="substitute"),
        naw.RandomWordAug(action="swap"),
        naw.RandomWordAug(action="delete"),
        naw.RandomWordAug(action="crop"),
        naw.SplitAug(),
    ]

    def __init__(
        self,
        probability: float = 0.15,
    ) -> None:
        self.probability = probability

    def __call__(self, record: list[tuple]) -> list[tuple]:
        augmented_record = record.copy()
        if bernoulli.rvs(self.probability):
            try:
                action = random.choice(self.actions)
                idx = random.choice(range(len(augmented_record)))
                tp = augmented_record[idx]
                augmented_value = action.augment(tp[1])
                if isinstance(augmented_value, list):
                    augmented_value = augmented_value[0]
                augmented_tp = tp[0], augmented_value
                augmented_record[idx] = augmented_tp
            except:
                ...

        return augmented_record


if __name__ == "__main__":
    augmenter = Augmenter(probability=1)
    record = [
        ("content", "vldb conference papers 2020-01-01"),
        ("year", "2020"),
    ]
    for i in range(10):
        print(repr(augmenter(record)))
