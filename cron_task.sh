#!/bin/env bash 

OUTPUT_PATH="$DIGEST_PATH/markdown"

FILENAME=$(date "+%d-%m-%Y.md")
ENGLISH="--english"
RUSSIAN="--russian"

source $CONDA_PATH/etc/profile.d/conda.sh
conda activate digest
cd $DIGEST_PATH

if [[ -z "${TEST_RUN}" ]]; then
    python -m digest.generate --summaries --highlights
    python -m digest.translate
else
    ENGLISH=""
    RUSSIAN=""
fi

cp $DIGEST_PATH/.last-digest-en.md $OUTPUT_PATH/en/$FILENAME
cp $DIGEST_PATH/.last-digest-ru.md $OUTPUT_PATH/ru/$FILENAME

python -m digest.telegram $ENGLISH --only-highlights --input $OUTPUT_PATH/en/$FILENAME
python -m digest.telegram $RUSSIAN --only-highlights --input $OUTPUT_PATH/ru/$FILENAME
