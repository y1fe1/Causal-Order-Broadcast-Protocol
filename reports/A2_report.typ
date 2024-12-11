#import "@preview/modern-technique-report:0.1.0": *

#show: modern-technique-report.with(
  title: [Assignment 2 Lab Report:\ Reliable broadcast : Bracha's Protocols and Optimizations],
  subtitle: [
    
  ],
  series: [],
  author: grid(
    align: left + horizon,
    columns: 3,
    inset: 7pt,
    [*Member*], [Haoran Tang], [6195326],
    [], [Huan Li],             [6311032],
    [], [Yifei Qi],            [6299008],
    [],[],[],
    [*Professor*], [J.E.A.P. Decouchant], [J.Decouchant\@tudelft.nl],
  ),
  date: ("2024-2025 Q2"),
  theme-color: rgb(21, 74, 135),
  font: "New Computer Modern",
  title-font: "Noto Sans",
  background: "",
)

= Purpose
#box(
  inset: 1cm,
  [
    #text(14pt)[
        The purpose of this lab assignment is to implement Bracha's Reliable Broadcast Algorithm and three optimizations that improve the performance of the algorithm. Bracha's algorithm is based on the fully-connected network model, however in practice, the network is not fully connected in most cases. 

        The goal is to implement the Bracha's algorithm based on Dolev's algorithm, which guarantees a (virtual) fully connected network. The algorithm is Byzantine fault-tolerant.
        
        The optimizations are designed to improve the performance of the Bracha's algorithm in terms of message complexity and latency.
      ]
  ]
)

#pagebreak()

= Expiermental Setup 
\
\
\

#set align(center)
  #table(
  columns: (auto, auto),
  inset: 20pt,
  table.header(
    [Paramete Name],
    [Values]
  ),
  "Number of Nodes",
  "15",
  "Graph Connectivity",
  "10",
  "Number of Failure Nodes",
  "0-2",
  "Number of Broad Casters",
  "4",
  "Number of Distinct Messages",
  "2",
)

#set align(left)


#pagebreak()


= Result 
\
== Latency and message complexity without or with the 'Echo amplifications' optimization. \

In this metric, the experiment was conducted on a 6-connected graph, with the number of nodes incrementally increasing from 6 to 20. The results clearly show an upward trend in both average latency and message complexity as the number of nodes increases.

// #image("latency_nodes_assignment1.png")

#pagebreak()

== Latency and message complexity without or with the 'Single-hop Send messages' and the 'Echo amplifications' optimizations. \


In this metric, the experiment was conducted on a graph with 20 nodes, with the connectivity incrementally increasing from 6 to 19. The results clearly show a downward decreasing trend in average latency as the number of nodes increases.

// #image("conn_nodes_assignment1.png")

#pagebreak()
== Latency and message complexity without or with optimization MBD.11. \

In this metric, the experiment was conducted on a 19-connected graph with 20 nodes, with the number of Byzantine nodes incrementally increased from 0 to 6. The results clearly show an upward trend in average latency. For message complexity, due to the extremely high message complexity of malicious messages created by Byzantine nodes, the message flow in the network is significantly influenced.
// #image("byzantine_nodes_assignment1.png")

#pagebreak()

= Conclusion

#box(
  inset: 1cm,
  [
    #text(14pt)[
        In conclusion, the experiments demonstrate distinct trends based on the varying metrics of the Bracha's protocol. With the three optimizations, the performance has different trends of increasing. The 'Echo amplifications' optimization xxx. The 'Single-hop Send messages' and the 'Echo amplifications' optimizations xxx. The optimization MBD.11 xxx.

        In conclusion, Bracha's Reliable broadcast algorithm can make sure the message be delivered correctly, and resist Byzantine behaviours.
      ]
  ]
)
