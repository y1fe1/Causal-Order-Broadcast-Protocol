
NUM_NODES=2
python src/util.py $NUM_NODES topologies/echo.yaml echo
docker compose build
docker compose up