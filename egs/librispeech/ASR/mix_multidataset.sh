#!/usr/bin/env bash

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

set -eou pipefail

nj=16
stage=1
stop_stage=100

num_splits=0

giga_Level=S

dl_dir=$PWD/download

. shared/parse_options.sh || exit 1

# vocab size for sentence piece models.
# It will generate data/lang_bpe_xxx,
# data/lang_bpe_yyy if the array contains xxx, yyy
vocab_sizes=(
  # 5000
  # 2000
  # 1000
  500
)

# multidataset list.
# LibriSpeech and musan are required.
# The others are optional.
multidataset=(
  "gigaspeech",
  "commonvoice",
)

# All files generated by this script are saved in "data".
# You can safely remove "data" and rerun this script to regenerate it.
mkdir -p data

log() {
  # This function is from espnet
  local fname=${BASH_SOURCE[1]##*/}
  echo -e "$(date '+%Y-%m-%d %H:%M:%S') (${fname}:${BASH_LINENO[0]}:${FUNCNAME[1]}) $*"
}

log "dl_dir: $dl_dir"

if [ $stage -le 1 ] && [ $stop_stage -ge 1 ]; then
  log "Stage 1: Prepare the other datasets"
  # GigaSpeech
  if [[ "${multidataset[@]}" =~ "gigaspeech" ]]; then
    log "Dataset: GigaSpeech"
    if [ ! -f data/.giga_dataset.done ]; then
      ln -svf ../../gigaspeech/ASR/data/manifests/gigaspeech_* data/manifests/.
      ln -svf ../../gigaspeech/ASR/data/fbank/cuts_* data/fbank/.
      ln -svf ../../gigaspeech/ASR/data/fbank/feats_* data/fbank/.
      ln -svf ../../gigaspeech/ASR/data/fbank/gigaspeech_* data/fbank/.
      ln -svf ../../gigaspeech/ASR/data/fbank/${giga_Level}_split data/fbank/.
      mkdir -p  data/fbank/multidataset_split_${num_splits}
      ln -svf ../../gigaspeech/ASR/data/fbank/${giga_Level}_split/cuts_${giga_Level}.*.jsonl.gz data/fbank/multidataset_split_${num_splits}/.
      touch data/.giga_dataset.done
    fi
  fi

  # CommonVoice
  if [[ "${multidataset[@]}" =~ "commonvoice" ]]; then
    if [ ! -f data/.cv_dataset.done ]; then
      log "Dataset: CommonVoice"
      ln -s ../../commonvoice/ASR/data/en data/en
      touch data/.cv_dataset.done
    fi
  fi
fi

if [ $stage -le 2 ] && [ $stop_stage -ge 2 ]; then
  log "Stage 2 Create multidataset"
  split_dir=data/fbank/multidataset_split_${num_splits}
  if [ ! -f $split_dir/.multidataset.done ]; then
    mkdir -p $split_dir/multidataset
    log "Split LibriSpeech"
    if [ ! -f $split_dir/.librispeech_split.done ]; then
      lhotse split $num_splits ./data/fbank/librispeech_cuts_train-all-shuf.jsonl.gz $split_dir
      touch $split_dir/.librispeech_split.done
    fi

    if [[ "${multidataset[@]}" =~ "commonvoice" ]]; then
      log "Split CommonVoice"
      if [ ! -f $split_dir/.cv-en_train_split.done ]; then
        lhotse split $num_splits ./data/en/fbank/cv-en_cuts_train.jsonl.gz $split_dir
        touch $split_dir/.cv-en_train_split.done
      fi
    fi

    if [ ! -f $split_dir/.multidataset_mix.done ]; then
      log "Mix multidataset"
      for ((seq=0; seq<${nums_plits}; seq++)); do
        fseq=$(printf "%02d" $seq)
        gunzip -c $split_dir/*.*${fseq}.jsonl.gz | \
        shuf | gzip -c > $split_dir/multidataset/multidataset_cuts_train.${fseq}.jsonl.gz
      done
      touch $split_dir/.multidataset_mix.done
    fi

    touch $split_dir/.multidataset.done
  fi
fi
