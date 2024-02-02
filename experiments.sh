#!/bin/bash

if ! [ -f ./main ]; then
    echo -e "\e[1;31mError:\e[0m\e[1m Executable file \e[1;34m./main\e[0m\e[1m isn't available. Maybe you forgot to compile it from source code. Try again."
    exit 1
fi

time_step=0.1
time_interval=1
out="experiment_results.txt"

particle_counts=(1 10 100 1000 10000 100000 1000000 10000000)
msh_filenames=("results/box.msh" "results/sphere.msh" "results/cylinder.msh" "results/cone.msh")
available_msh_filenames=()

for msh_filename in "${msh_filenames[@]}"; do
    if [ -f msh_filename ]; then
        echo -e "\e[1;31mError:\e[1;34m ${msh_filename}:\e[0m\e[1m No such mesh file."
    else
        available_msh_filenames+=("$msh_filename") # Adding only existing files
    fi
done

# Checking if there is no any msh files
if [ -z "${available_msh_filenames[*]}" ]; then
    echo -e "\e[1;31mError: \e[0m\e[1mThere is no any mesh files. Exiting..."
    exit 1
fi

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
            if [ "$particle_count" -le 1000000 ] && [ "$thread_count" -lt 4 ]; then
                echo -e "Running experiment with \e[1;31m$particle_count\e[0m particles and mesh file \e[1;34m$msh_filename\e[0m with \e[1;32m$thread_count\e[0m\e[1m threads."
                (time ./main $particle_count $time_step $time_interval $msh_filename $thread_count) 2>&1 | grep real | awk '{print $2}' >>$out
            fi
            if [ "$thread_count" -ne 1 ] && [ "$thread_count" -ne 2 ] && [ "$max_threads" -ge 4 ]; then
                echo -e "Running experiment with \e[1;31m$particle_count\e[0m particles and mesh file \e[1;34m$msh_filename\e[0m with \e[1;32m$thread_count\e[0m\e[1m threads."
                (time ./main $particle_count $time_step $time_interval $msh_filename $thread_count) 2>&1 | grep real | awk '{print $2}' >>$out
            fi
        done
    done
done
