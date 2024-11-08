
NUM_NODES=2
# python -m cs4545.system.util compose $NUM_NODES topologies/echo.yaml echo
python -m in4150.system.util cfg cfg/echo.test.yaml

# Exit if the above command fails
if [ $? -ne 0 ]; then
    exit 1
fi

docker compose build
docker compose up