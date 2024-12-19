import pandas as pd
import matplotlib.pyplot as plt


def plot_latency_and_complexity():
    latency_nodes_metrics = []
    msg_complexity_metrics = []
    for i in range (10, 20, 2):
        average_time = []
        msg_complexity = []
        for j in range(0, 10):
            file_name = (
                "output/rco_" + str(i) + "/node-" + str(j) + "-msg_summary.csv"
            )
            try:
                df = pd.read_csv(file_name)
                average_time.append(df.iloc[:, 3].mean())
                msg_complexity.append(df.iloc[:,6].sum())
                # print(f'Average time for file {file_name}: {average_time}')
            except FileNotFoundError:
                print(f"File {file_name} not found.")
        # get the average for each number of nodes
        latency_nodes_metrics.append(average_time)
        msg_complexity_metrics.append(msg_complexity)

    plt.plot(range(10, 20, 2), latency_nodes_metrics,color='blue', label="Average Latency")
    plt.xlabel("Number of nodes")
    plt.ylabel("Average Latency time (ms)")
    plt.title("Average Latency time with msg complexity vs. Number of nodes")

    num_nodes = range(10, 20, 2)
    
    for i, latency in enumerate(latency_nodes_metrics):
        plt.annotate(f"{latency}",
                     (num_nodes[i], latency_nodes_metrics[i]),
                     textcoords="offset points", xytext=(0, 5), ha='center', color="blue", fontsize=9)
    
    for i, msg_complexity in enumerate(msg_complexity_metrics):
        plt.annotate(f"{msg_complexity}",
                     (num_nodes[i], msg_complexity_metrics[i]),
                     textcoords="offset points", xytext=(0, 5), ha='center', color="red", fontsize=9)
 

    if len(num_nodes) == len(latency_nodes_metrics):
        plt.scatter(num_nodes, latency_nodes_metrics, color='red', marker='x', s=50, label="Latency", zorder=5)
    else:
        print("Error: num_nodes and latency_nodes_metrics must be the same size")
        
    if len(num_nodes) == len(msg_complexity_metrics):
        plt.scatter(num_nodes, msg_complexity_metrics, color='red', marker='x', s=50, label="Latency", zorder=5)
    else:
        print("Error: num_nodes and msg_complexity_metrics must be the same size")
    
    plt.legend()
    plt.tight_layout()
    plt.show()

plot_latency_and_complexity()
