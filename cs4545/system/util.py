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
@click.option('--topology', type=str, default='fully')
@click.option('--connectivity', type=int, default=-1)
@click.option('--template_file', type=str,  default='docker-compose.template.yml')
@click.option('--overwrite_topology',is_flag=True, help='Overwrite the topology file. Useful for topologies that can be adjusted dynamically such as rings. Do not use this option if you have a static topology file that you want the preserve!')
def compose(num_nodes, topology_file, algorithm, topology, connectivity, template_file, overwrite_topology):
    prepare_compose_file(num_nodes, topology_file, algorithm, topology, connectivity, template_file, overwrite_topology=overwrite_topology)


def prepare_compose_file(num_nodes, topology_file, algorithm, topology, connectivity, template_file, location='cs4545', overwrite_topology = False):
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

        for i in range(num_nodes):
            n = copy.deepcopy(node)
            n['ports'] = [f'{baseport + i}:{baseport + i}']
            n['networks'][network_name]['ipv4_address'] = f'{network_base}.{10 + i}'
            n['environment']['PID'] = i
            n['environment']['TOPOLOGY'] = topology_file
            n['environment']['ALGORITHM'] = algorithm
            n['environment']['LOCATION'] = location
            nodes[f'node{i}'] = n

            # Create topology
            # It will only be used when the overwrite_topology is set to True
            if topology == 'ring':
                connections[i] = [(i + 1) % num_nodes, (i - 1) % num_nodes]
            elif topology == 'fully':
                if connectivity <= 0:
                    connections[i] = [j for j in range(num_nodes) if j != i]
                else:
                    connectivity = min(connectivity, num_nodes - 1)
                    connections[i] = []
                    for j in range(1, (connectivity // 2) + 1):
                        before = (i + j) % num_nodes
                        after = (i - j) % num_nodes
                        connections[i].extend([before, after])
                    if connectivity % 2 == 1:
                        connections[i].append((i + (connectivity // 2) + 1) % num_nodes)
                    connections[i].sort()

        content['services'] = nodes

        with open('docker-compose.yml', 'w') as f2:
            yaml.safe_dump(content, f2)
            print(f'Output written to docker-compose.yml')

        if overwrite_topology:
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
