
NUM_NODES=4
python src/util.py $NUM_NODES topologies/election.yaml election
docker compose build
docker compose up