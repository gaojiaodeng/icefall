# Copyright      2023  Xiaomi Corp.        (authors: Zengrui Jin)
#
# See ../../../../LICENSE for clarification regarding multiple authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import logging
from functools import lru_cache
from pathlib import Path
from typing import Dict

from lhotse import CutSet, load_manifest_lazy


class MultiDataset:
    def __init__(self, args: argparse.Namespace):
        """
        Args:
          manifest_dir:
            It is expected to contain the following files:
            - aishell2_cuts_train.jsonl.gz
        """
        self.fbank_dir = Path(args.manifest_dir)
        self.use_librispeech = args.use_librispeech
        self.use_gigaspeech = args.use_gigaspeech
        self.use_commonvoice = args.use_commonvoice

    def train_cuts(self) -> CutSet:
        logging.info("About to get multidataset train cuts")

        # GigaSpeech
        if self.use_gigaspeech:
            logging.info("Loading GigaSpeech in lazy mode")
            gigaspeech_cuts = load_manifest_lazy(
                self.fbank_dir / "cuts_XS.jsonl.gz"
            )

        # CommonVoice
        if self.use_commonvoice:
            logging.info("Loading CommonVoice in lazy mode")
            commonvoice_cuts = load_manifest_lazy(
                self.fbank_dir / "cv-en_cuts_train.jsonl.gz"
            )

        # LibriSpeech
        if self.use_librispeech:
            logging.info("Loading LibriSpeech in lazy mode")
            train_clean_100_cuts = self.train_clean_100_cuts()
            train_clean_360_cuts = self.train_clean_360_cuts()
            train_other_500_cuts = self.train_other_500_cuts()

        if self.use_gigaspeech and self.use_librispeech and self.use_commonvoice:
            return CutSet.mux(
                gigaspeech_cuts,
                train_clean_100_cuts,
                train_clean_360_cuts,
                train_other_500_cuts,
                commonvoice_cuts,
                weights=[
                    len(gigaspeech_cuts),
                    len(train_clean_100_cuts),
                    len(train_clean_360_cuts),
                    len(train_other_500_cuts),
                    len(commonvoice_cuts),
                ],
            )
        else:
            raise NotImplementedError(
                f"""Not implemented for 
                use_gigaspeech: {self.use_gigaspeech}
                use_librispeech: {self.use_librispeech}
                use_commonvoice: {self.use_commonvoice}"""
            )

    def dev_cuts(self) -> CutSet:
        logging.info("About to get multidataset dev cuts")

        # GigaSpeech
        logging.info("Loading GigaSpeech DEV set in lazy mode")
        gigaspeech_dev_cuts = load_manifest_lazy(
            self.fbank_dir / "cuts_DEV.jsonl.gz"
        )

        # LibriSpeech
        dev_clean_cuts = self.dev_clean_cuts()
        dev_other_cuts = self.dev_other_cuts()

        logging.info("Loading CommonVoice set in lazy mode")
        commonvoice_dev_cuts = load_manifest_lazy(
            self.fbank_dir / "cv-en_cuts_dev.jsonl.gz"
        )

        return CutSet.mux(
            gigaspeech_dev_cuts,
            dev_clean_cuts,
            dev_other_cuts,
            commonvoice_dev_cuts,
            weights=[
                len(gigaspeech_dev_cuts),
                len(dev_clean_cuts),
                len(dev_other_cuts),
                len(commonvoice_dev_cuts),
            ],
        )

    def test_cuts(self) -> Dict[str, CutSet]:
        logging.info("About to get multidataset test cuts")

        # GigaSpeech
        logging.info("Loading GigaSpeech test set in lazy mode")
        gigaspeech_test_cuts = load_manifest_lazy(
            self.fbank_dir / "cuts_TEST.jsonl.gz"
        )

        # LibriSpeech
        test_clean_cuts = self.test_clean_cuts()
        test_other_cuts = self.test_other_cuts()

        logging.info("Loading CommonVoice set in lazy mode")
        commonvoice_test_cuts = load_manifest_lazy(
            self.fbank_dir / "cv-en_cuts_test.jsonl.gz"
        )

        test_cuts = {
            "librispeech_test_clean": test_clean_cuts,
            "librispeech_test_other": test_other_cuts,
            "gigaspeech_test": gigaspeech_test_cuts,
            "commonvoice_test": commonvoice_test_cuts,
        }

        return test_cuts

    @lru_cache()
    def train_clean_100_cuts(self) -> CutSet:
        logging.info("About to get train-clean-100 cuts")
        return load_manifest_lazy(
            self.fbank_dir / "librispeech_cuts_train-clean-100.jsonl.gz"
        )

    @lru_cache()
    def train_clean_360_cuts(self) -> CutSet:
        logging.info("About to get train-clean-360 cuts")
        return load_manifest_lazy(
            self.fbank_dir / "librispeech_cuts_train-clean-360.jsonl.gz"
        )

    @lru_cache()
    def train_other_500_cuts(self) -> CutSet:
        logging.info("About to get train-other-500 cuts")
        return load_manifest_lazy(
            self.fbank_dir / "librispeech_cuts_train-other-500.jsonl.gz"
        )

    @lru_cache()
    def dev_clean_cuts(self) -> CutSet:
        logging.info("About to get dev-clean cuts")
        return load_manifest_lazy(
            self.fbank_dir / "librispeech_cuts_dev-clean.jsonl.gz"
        )

    @lru_cache()
    def dev_other_cuts(self) -> CutSet:
        logging.info("About to get dev-other cuts")
        return load_manifest_lazy(
            self.fbank_dir / "librispeech_cuts_dev-other.jsonl.gz"
        )

    @lru_cache()
    def test_clean_cuts(self) -> CutSet:
        logging.info("About to get test-clean cuts")
        return load_manifest_lazy(
            self.fbank_dir / "librispeech_cuts_test-clean.jsonl.gz"
        )

    @lru_cache()
    def test_other_cuts(self) -> CutSet:
        logging.info("About to get test-other cuts")
        return load_manifest_lazy(
            self.fbank_dir / "librispeech_cuts_test-other.jsonl.gz"
        )
