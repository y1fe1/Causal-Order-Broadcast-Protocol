#import "@preview/modern-technique-report:0.1.0": *

#show: modern-technique-report.with(
  title: [Assignment 3 Lab Report:\ Reliable broadcast : Bracha's Protocols and Optimizations],
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
        The purpose of this lab assignment is to implement a causal-order Byzantine broadcast Algorithm that is desgined to work in a complete netwrok with up to $f$ faulty node.
        
        The Report also examines possible Malicisous Action a Byzantine Node can perform and its impact on the whole network.
      ]
  ]
)

#pagebreak()

= Expeirmental Setup 
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
  "10",
  "Graph Connectivity",
  "6",
  "Number of Failure Nodes",
  "0-2",
  "Number of Broad Casters",
  "3",
  "Number of Distinct Messages",
  "5",
)

#set align(left)


#pagebreak()


= Result 
\
== Latency and message complexity for one RCO-Broadcast Operation \

In this metric, the experiment was conducted on a 6-connected graph, with 10 nodes, and 5 distinct messages broadcasting across the network. The results show a overall decreasing trend in average latency and Message Complexity with the Echo amplification enabled


#pagebreak()

== Byzantine Behaviour and Its Impact \

*There is several ways that a Byzantine Node can disrupt the RCO Protocols in Several ways, Such as *:
\
\

  1. *Message Dropping*: \
    A faulty node can selectively drop a message that is delivered to it
    - Impact : 
      - Breaks causal chains, potentially leading to incorrect delivery order at correct processes.
      - Can cause indefinite waiting in correct processes expecting causally related messages.


  2. *Manipulate Incorrect Vector Clock (Artificial Boosting Attack)*: \
    Byzantine Node $p_k$ Manipulate all values in the vector clock VC[rank($p_j$)] $forall $ correct node $p_j$.When the Byzantine node send this manipulated vector clock to a correct process, the correct process recieve this false vector clock and propogate it throughout the system.

    - Impact : 
      - True Causal Order is disrupted as false dependencies created beween messages
      - True node may faulty deliver a Message even though causal dependencies are not satisfied 
      - legitimate message may be never delivered as causal dependencies will never be satisfied

  3. *Message Delayed* :\
    Byzantine process delivered a message from another process. But instead of immediately forwarding or processing the messsage, it can hold the message for an arbitary amount of time until it is broadcasted to others but much later then expected.
    - Impact:
        - Disruption of Causal Order that may lead to incorrect delivery order at any correct process
        - Increased Latency across all network as Message delivery time is manipulated.
        - A correct node have no way to differentiate bettwen such a Byzantine $p_i$ is delaying the message or a correct $p_j$ that is experiencing very slow communcation
 

#pagebreak()

= Conclusion

#box(
  inset: 1cm,
  [
    #text(14pt)[
        In conclusion......
      ]
  ]
)
