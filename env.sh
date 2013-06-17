case "$BASH_SOURCE" in
    /*)
    ENV_BASE_FILE="$BASH_SOURCE"
    ;;
    *)
    ENV_BASE_FILE="`pwd`/$BASH_SOURCE"
esac
ENV_BASE_DIR=`dirname $ENV_BASE_FILE`

export PYTHONPATH=$ENV_BASE_DIR:$PYTHONPATH

unset BASE_FILE
unset ENV_BASE_DIR
