export STREETS_ROOT=`pwd`
export PYTHONPATH="$STREETS_ROOT/src:$PYTHONPATH"
export MYPYPATH="$PYTHONPATH"
alias ipython="sh $STREETS_ROOT/ipython.sh"

runjupyter() {
  jupyter-notebook --ip 0.0.0.0 --port 8888 \
    --NotebookApp.token='' --NotebookApp.password='' "$@" --no-browser
}
alias jupyter=runjupyter
