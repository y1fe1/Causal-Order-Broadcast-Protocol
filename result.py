import pandas as pd
import matplotlib.pyplot as plt
import glob

# file_paths = 'output/Bracha_Test_20241212_1715/node-*msg_summary.csv'
# csv_files = glob.glob(file_paths)
# df_list = [pd.read_csv(file) for file in csv_files]

baseline_path = 'output/Baseline/node-*msg_summary.csv'
optim1_path = 'output/Optim1/node-*msg_summary.csv'
optim2_path = 'output/Optim2/node-*msg_summary.csv'
optim3_path = 'output/Optim3/node-*msg_summary.csv'

baseline_files = glob.glob(baseline_path)
optim1_files = glob.glob(optim1_path)
optim2_files = glob.glob(optim2_path)
optim3_files = glob.glob(optim3_path)

baseline_df_list = [pd.read_csv(file) for file in baseline_files]
optim1_df_list = [pd.read_csv(file) for file in optim1_files]
optim2_df_list = [pd.read_csv(file) for file in optim2_files]
optim3_df_list = [pd.read_csv(file) for file in optim3_files]

# Concatenate DataFrames for each optimization with baseline
optim1_df = pd.concat([pd.concat(baseline_df_list), pd.concat(optim1_df_list)])
optim2_df = pd.concat([pd.concat(baseline_df_list), pd.concat(optim2_df_list)])
optim3_df = pd.concat([pd.concat(baseline_df_list), pd.concat(optim3_df_list)])

# Group by 'msg_id' and calculate mean latency and sum of bytes_sent for each group
optim1_grouped_latency = optim1_df.groupby('msg_id').agg({'latency': 'mean'}).reset_index()
optim1_grouped_byte_sent = optim1_df.groupby('msg_id').agg({'byte_sent': 'mean'}).reset_index()

optim2_grouped_latency = optim2_df.groupby('msg_id').agg({'latency': 'mean'}).reset_index()
optim2_grouped_byte_sent = optim2_df.groupby('msg_id').agg({'byte_sent': 'mean'}).reset_index()

optim3_grouped_latency = optim3_df.groupby('msg_id').agg({'latency': 'mean'}).reset_index()
optim3_grouped_byte_sent = optim3_df.groupby('msg_id').agg({'byte_sent': 'mean'}).reset_index()


# print(optim2_grouped_byte_sent)

def plot_figure_latency(optimal_grouped_latency, metics_kind, optim_num):
    # Merge baseline and optim1 latency data on 'msg_id'
    baseline_latency = pd.concat(baseline_df_list).groupby('msg_id').agg({'latency': 'mean'}).reset_index()
    merged_latency = pd.merge(baseline_latency, optimal_grouped_latency, on='msg_id', suffixes=('_baseline', f'_optim{optim_num}'))

    # Plot the comparison as bar chart
    plt.figure(figsize=(12, 8))
    bar_width = 0.35
    index = merged_latency['msg_id']

    plt.bar(index, merged_latency['latency_baseline'], bar_width, label='Baseline Latency')
    plt.bar(index + bar_width, merged_latency[f'latency_optim{optim_num}'], bar_width, label=f'Optim{optim_num} Latency')

    plt.xlabel('Message ID')
    plt.ylabel('Latency')
    plt.title(f'Comparison of {metics_kind}: Baseline vs Optim{optim_num}')
    plt.xticks(index + bar_width / 2, merged_latency['msg_id'])
    plt.legend()
    plt.grid(True)
    plt.show()
    
def plot_figure_msg(optimal_grouped_msg, metics_kind, optim_num):
    # Merge baseline and optim1 latency data on 'msg_id'
    baseline_msg = pd.concat(baseline_df_list).groupby('msg_id').agg({'byte_sent': 'mean'}).reset_index()
    merged_msg = pd.merge(baseline_msg, optimal_grouped_msg, on='msg_id', suffixes=('_baseline', f'_optim{optim_num}'))

    # Plot the comparison as bar chart
    plt.figure(figsize=(12, 8))
    bar_width = 0.35
    index = merged_msg['msg_id']

    plt.bar(index, merged_msg['byte_sent_baseline'], bar_width, label='Baseline Message Complexity')
    plt.bar(index + bar_width, merged_msg[f'byte_sent_optim{optim_num}'], bar_width, label=f'Optim{optim_num} Message Complexity')

    plt.xlabel('Message ID')
    plt.ylabel('Message Complexity')
    plt.title(f'Comparison of {metics_kind}: Baseline vs Optim{optim_num}')
    plt.xticks(index + bar_width / 2, merged_msg['msg_id'])
    plt.legend()
    plt.grid(True)
    plt.show()
    
plot_figure_latency(optim1_grouped_latency, 'Latency', '1')
plot_figure_latency(optim2_grouped_latency, 'Latency', '2')
plot_figure_latency(optim3_grouped_latency, 'Latency', '3')
plot_figure_msg(optim1_grouped_byte_sent, 'Bytes Sent', '1')
plot_figure_msg(optim2_grouped_byte_sent, 'Bytes Sent', '2')
plot_figure_msg(optim3_grouped_byte_sent, 'Bytes Sent', '3')
