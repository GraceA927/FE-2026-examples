#!/bin/bash


#SBATCH --partition=demo









#SBATCH --time=2:00:00





#SBATCH --requeue


#SBATCH --open-mode=append
#SBATCH --output=stdout.txt
#SBATCH --error=stderr.txt




module load /shared/emod/shared_tools/modulefiles/singularity



# Assign the values from the template
ntasks=1

# Get mpi_type
mpi_type=pmi2

# All submissions happen at the experiment level
# Check if ntasks is greater than 1 to include --mpi=$mpi_type
if [ "$ntasks" -gt 1 ]; then
    echo "Running with MPI (ntasks=$ntasks)"
    bash run_simulation.sh "$1" "$mpi_type"
else
    echo "Running without MPI (ntasks=$ntasks)"
    bash run_simulation.sh "$1" "no-mpi"
fi
wait



