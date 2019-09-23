export CWD=`pwd`
export PYTHONPATH="$CWD/src:$PYTHONPATH"
export MYPYPATH="$PYTHONPATH"
alias ipython="sh $CWD/ipython.sh"

runjupyter() {
  jupyter-notebook --ip 0.0.0.0 --port 8888 \
    --NotebookApp.token='' --NotebookApp.password='' "$@" --no-browser
}
alias jupyter=runjupyter
