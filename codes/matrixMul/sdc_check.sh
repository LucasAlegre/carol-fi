# Remove GDB specific outputs from gold and inj output
CLEAN_GOLD=/tmp/clean_carol_fi_gold.txt
CLEAN_INJ_OUTPUT=/tmp/clean_carol_fi_inj.txt
TMP=/tmp/carol_buff.txt

cat ${GOLD_OUTPUT_PATH} > ${CLEAN_GOLD}

for i in '/Breakpoint/,+2d' '/\[New Thread/d' '/\[Thread/d' '/\[Switching/d' '/\[Inferior/d';
do
    for j in ${INJ_OUTPUT_PATH} ${CLEAN_GOLD};
    do
        sed -e $i $j > ${TMP}
        cat ${TMP} > $j
    done
done

# SDC checking diff
# Must compare all things here
# Copied from SASSIFI
# APP, GOLD_OUTPUT_PATH and INJ_OUTPUT_PATH are set on python script
cat ${INJ_OUTPUT_PATH} > ${CLEAN_INJ_OUTPUT}

diff -B ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} > ${DIFF_LOG}

rm -f ${CLEAN_GOLD} ${CLEAN_INJ_OUTPUT} ${TMP}