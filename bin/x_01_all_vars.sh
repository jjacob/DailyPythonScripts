#!/bin/bash
mkdir logs
python src/cross_section_measurement/01_get_fit_results.py &> logs/met_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -v HT &> logs/ht_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -v ST &> logs/st_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -v MT &> logs/mt_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -v WPT &> logs/wpt_fit.log &
# 7 TeV
python src/cross_section_measurement/01_get_fit_results.py -c 7&> logs/met_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -c 7 -v HT &> logs/ht_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -c 7 -v ST &> logs/st_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -c 7 -v MT &> logs/mt_fit.log &
python src/cross_section_measurement/01_get_fit_results.py -c 7 -v WPT &> logs/wpt_fit.log &
