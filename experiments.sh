#!/bin/bash

time_step=0.1
time_interval=1
out="experiment_results.txt"

particle_counts=(1 10 100 1000 10000 100000 1000000 10000000)
msh_filenames=("results/box.msh" "results/sphere.msh" "results/cylinder.msh" "results/cone.msh")

max_threads=$(nproc)
thread_count=1
thread_counts=()

while [ "$thread_count" -le "$max_threads" ]; do
    thread_counts+=("$thread_count")
    thread_count=$((thread_count * 2))
done

>$out

for msh_filename in "${msh_filenames[@]}"; do
    for thread_count in "${thread_counts[@]}"; do
        for particle_count in "${particle_counts[@]}"; do
            if [ "$particle_count" -le 1000000 ] && [ "$thread_count" -ge 4 ]; then
                echo "Running experiment with $particle_count particles and mesh file $msh_filename with $thread_count threads"
                (time ./main $particle_count $time_step $time_interval $msh_filename $thread_count) 2>&1 | grep real | awk '{print $2}' >>$out
            fi
            if [ "$max_threads" -eq 16 ] && [ "$thread_count" -le 16 ]; then
                echo "Running experiment with $particle_count particles and mesh file $msh_filename with $thread_count threads"
                (time ./main $particle_count $time_step $time_interval $msh_filename $thread_count) 2>&1 | grep real | awk '{print $2}' >>$out
            fi
        done
    done
done
