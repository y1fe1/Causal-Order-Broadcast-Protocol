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
        The purpose of this lab assignment is to implement Bracha's Reliable Broadcast Algorithm and three optimizations that improve the performance of the algorithm. Bracha's algorithm is based on the fully-connected network model, however in practice, the network is not fully connected in most cases. 

        The goal is to implement the Bracha's algorithm based on Dolev's algorithm, which guarantees a (virtual) fully connected network. The algorithm is Byzantine fault-tolerant.
        
        The optimizations are designed to improve the performance of the Bracha's algorithm in terms of message complexity and latency.
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
== Latency and message complexity without or with the 'Echo amplifications' optimization. \

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
        In conclusion, the experiments demonstrate distinct trends based on the varying metrics of the Bracha's protocol. With the three optimizations, the performance of the network all shows increasing trend in term of better Latency and Message Complexity. We see that Optimziation 3 has the most significant effect in reducing message communcation across the network. And optimization 1 and 2 has a slightly  less performance as the network is relatively small,  which wrong-order asynchronous message delivered are not that common as the nodes recieved SEND Message in time.

        In conclusion, Bracha's Reliable broadcast algorithm can make sure the message be delivered correctly, and resist Byzantine behaviours.
      ]
  ]
)
