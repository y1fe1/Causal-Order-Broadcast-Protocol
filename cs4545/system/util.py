import copy
from pathlib import Path
from typing import Optional

import click
import yaml


@click.group()
def cli():
    pass


@cli.command('compose')
@click.argument('num_nodes', type=int)
@click.argument('topology_file', type=str, default='topologies/echo.yaml')
@click.argument('algorithm', type=str, default='echo')
@click.option('--template_file', type=str, default='docker-compose.template.yml')
def compose(num_nodes, topology_file, algorithm, template_file):
    prepare_compose_file(num_nodes, topology_file, algorithm, template_file)


def prepare_compose_file(num_nodes, topology_file, algorithm, template_file, location='cs4545'):
    with open(template_file, 'r') as f:
        content = yaml.safe_load(f)

        node = content['services']['node0']
        content['x-common-variables']['TOPOLOGY'] = topology_file

        nodes = {}
        baseport = 9090
        connections = {}

        network_name = list(content['networks'].keys())[0]
        subnet = content['networks'][network_name]['ipam']['config'][0]['subnet'].split('/')[0]
        network_base = '.'.join(subnet.split('/')[0].split('.')[:-1])

        # Create a ring topology
        for i in range(num_nodes):
            n = copy.deepcopy(node)
            n['ports'] = [f'{baseport + i}:{baseport + i}']
            n['networks'][network_name]['ipv4_address'] = f'{network_base}.{10 + i}'
            n['environment']['PID'] = i
            n['environment']['TOPOLOGY'] = topology_file
            n['environment']['ALGORITHM'] = algorithm
            n['environment']['LOCATION'] = location
            nodes[f'node{i}'] = n

            connections[i] = [(i + 1) % num_nodes, (i - 1) % num_nodes]

        content['services'] = nodes

        with open('docker-compose.yml', 'w') as f2:
            yaml.safe_dump(content, f2)
            print(f'Output written to docker-compose.yml')

        with open(topology_file, 'w') as f3:
            yaml.safe_dump(connections, f3)
            print(f'Output written to {topology_file}')


@cli.command('cfg')
@click.argument('cfg_file', type=str)
def prepare_from_cfg(cfg_file: str):
    with open(cfg_file, 'r') as f:
        cfg = yaml.safe_load(f)
        # print(cfg)
        if 'template' not in cfg:
            cfg['template'] = 'docker-compose.template.yml'
        if 'location' not in cfg:
            cfg['location'] = 'cs4545'
        prepare_compose_file(cfg['num_nodes'], cfg['topology'], cfg['algorithm'], cfg['template'], cfg['location'])


@cli.command()
@click.argument('cfg_file', type=str)
@click.argument('output_dir', type=str)
@click.option('--verbose', type=bool, default=True)
@click.option('--append_file', type=str)
@click.option('--name', type=str)
def eval(cfg_file: str, output_dir: str, verbose: bool = True, append_file: Optional[str] = None,
         name: Optional[str] = None):
    if verbose:
        print('Evaluating output')
    with open(cfg_file, 'r') as f:
        cfg = yaml.safe_load(f)

    out_dir = Path(output_dir)
    out_files = {}
    for f in [x for x in out_dir.iterdir() if x.suffix == '.out']:
        with open(f, 'r') as f2:
            # Load the txt in the file
            out_files[f.stem] = [x.rstrip() for x in f2.readlines()]
    valid = 0
    invalid = 0

    node_stats = [yaml.safe_load(open(x)) for x in out_dir.iterdir() if x.suffix == '.yml']

    # Aggregate the node stats where the structure is a list of dictionaries with the same keys
    agg_stats = {}
    for key in node_stats[0].keys():
        agg_stats[key] = [x[key] for x in node_stats]
        try:
            agg_stats[key] = sum(agg_stats[key])
        except Exception:
            pass
    agg_stats['num_nodes'] = len(node_stats)
    agg_stats['algorithm'] = cfg['algorithm']

    if 'expected_output' not in cfg:
        print('No expected output found in cfg')
    else:
        for node_name in cfg['expected_output']:
            node_output = iter(out_files[node_name])
            eval_output = cfg['expected_output'][node_name]

            for expected_val in eval_output:
                try:
                    node_val = next(node_output)
                    if expected_val != node_val:
                        if verbose:
                            print(f'Output mismatch for {node_name} at {expected_val} != {node_val}')
                        invalid += 1
                    else:
                        valid += 1
                except StopIteration:
                    if verbose:
                        print('Output mismatch: Expected more output')
                    invalid += 1

    if valid + invalid == 0:
        score = 0.0
    else:
        score = (valid / float(valid + invalid)) * 100.0
    if verbose:
        print(f'Valid: {valid} Invalid: {invalid}, Score: {score:.2f}%')

        print(agg_stats)
    if append_file and name:
        print(f'Appending to {append_file} for {name}')
        csv_line = ','.join([name, str(valid), str(invalid), f'{score:.2f}'])
        with open(append_file, 'a') as f:
            f.write(csv_line)
            f.write('\n')


@cli.command()
@click.argument('topology_file', type=str)
def draw_topology(topology_file: str):
    with open(topology_file, 'r') as f:
        edges = yaml.safe_load(f)
        import networkx as nx
        import matplotlib.pyplot as plt
        G = nx.DiGraph()
        for node, connections in edges.items():
            for conn in connections:
                G.add_edge(f'{node}', f'{conn}')
        pos = nx.spring_layout(G)
        nx.draw(G, with_labels=True, pos=pos)
        plt.show()


if __name__ == '__main__':
    cli()
