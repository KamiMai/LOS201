set terminal pngcairo size 1400,1000 font 'DejaVu Sans,12'
set output 'logs/latency_histogram.png'
set multiplot layout 2,1 title 'Host wake-up latency - 4 SCHED_FIFO threads, 60 s per run'
set grid
set xlabel 'Latency (microseconds)'
set ylabel 'Samples across four threads'
set logscale y
set yrange [0.8:*]
set key top right
set xrange [0:100]
set title 'Main distribution'
plot 'logs/hist_standard.txt' using 1:(($2+$3+$4+$5)>0?($2+$3+$4+$5):1/0) with lines lw 2 title 'No injected stress', \
     'logs/hist_loaded.txt' using 1:(($2+$3+$4+$5)>0?($2+$3+$4+$5):1/0) with lines lw 2 title 'CPU + I/O + memory stress'
set xrange [0:4000]
set title 'Tail including the observed maximum'
plot 'logs/hist_standard.txt' using 1:(($2+$3+$4+$5)>0?($2+$3+$4+$5):1/0) with points pt 7 ps 0.35 title 'No injected stress', \
     'logs/hist_loaded.txt' using 1:(($2+$3+$4+$5)>0?($2+$3+$4+$5):1/0) with points pt 7 ps 0.35 title 'CPU + I/O + memory stress'
unset multiplot
