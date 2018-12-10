# R and ggplot must be installed. For ubuntu users: sudo apt install r-base-core r-cran-ggplot2
all: sa ga

mxm: process_mxm.py parseUtils.py createErrLimitsTableforPlot.R lineGraph.R 
	./process_mxm.py
	./createErrLimitsTableforPlot.R mxm_logs_parsed.csv MxM errLimit_mxm.csv
	./lineGraph.R errLimit_mxm.csv errLimit_mxm.pdf

hotspot: process_hotspot.py parseUtils.py createErrLimitsTableforPlot.R lineGraph.R 
	./process_hotspot.py
	./createErrLimitsTableforPlot.R hotspot_logs_parsed.csv HotSpot errLimit_hotspot.csv
	./lineGraph.R errLimit_hotspot.csv errLimit_hotspot.pdf

ga: process_ga.py parseUtils.py createErrLimitsTableforPlot.R lineGraph.R
	./process_ga.py
	./createErrLimitsTableforPlot.R ga_logs_parsed.csv ga errLimit_ga.csv
	./lineGraph.R errLimit_ga.csv errLimit_ga.pdf

sa: process_sa.py parseUtils.py createErrLimitsTableforPlot.R lineGraph.R
	./process_sa.py
	./createErrLimitsTableforPlot.R sa_logs_parsed.csv sa errLimit_sa.csv
	./lineGraph.R errLimit_sa.csv errLimit_sa.pdf

clean:
	rm -f mxm_logs_parsed.csv errLimit_mxm.csv errLimit_mxm.pdf hotspot_logs_parsed.csv errLimit_hotspot.csv errLimit_hotspot.pdf parseUtils.pyc
