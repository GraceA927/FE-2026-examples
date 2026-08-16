#!/bin/bash

#SBATCH --signal=B:SIGTERM@30

# define the handler function
term_handler()
{
    # do whatever cleanup you want here
    echo "-1" > job_status.txt
    exit -1
}

# associate the function "term_handler" with the TERM signal
trap 'term_handler' TERM

echo ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} > job_id.txt

n=0
until [ "$n" -ge 1 ]
do
    echo "100" > job_status.txt
    
        
                
                    singularity exec /shared/home/grace/FE-2026-examples/containers/dtk_run_al2023.sif Assets/Eradication --config config.json --dll-path ./Assets --input-path ./Assets\;.
                
        
    
   RESULT=$?
   if [ $RESULT -eq 0 ]; then
      echo "0" > job_status.txt
      exit $RESULT
   fi
   n=$((n+1))
   sleep 15
done
echo "-1" > job_status.txt
exit $RESULT