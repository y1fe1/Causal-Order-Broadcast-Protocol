#import "@preview/modern-technique-report:0.1.0": *

#show: modern-technique-report.with(
  title: [Assignment 1 Lab Report:\ Reliable communication : Dolev Protocols and Optimizations],
  subtitle: [
    
  ],
  series: [],
  author: grid(
    align: left + horizon,
    columns: 3,
    inset: 7pt,
    [*Member*], [Haoran Tang], [qwertyuiop\@tudelft.nl],
    [], [Huan Li], [qwertyuiop\@tudelft.nl],
    [], [Yifei Qi], [yifeiqi\@tudelft.nl],
    [],[],[],
    [*Professor*], [J.E.A.P. Decouchant], [J.Decouchant\@tudelft.nl],
  ),
  date: datetime.today().display("[year] -- [month] -- [day]"),
  theme-color: rgb(21, 74, 135),
  font: "New Computer Modern",
  title-font: "Noto Sans",
)

= Purpose
#box(
  inset: 1cm,
  [
    #text(14pt)[
      The purpose of this report is to implement the Dolev's Reliable Communication Algorithm and five modification that improve its performance. Reliable communication protocol is a fundamental component in distributed system since it is nesscary to ensure a message from a sender will eventually be delivered by its destination process with out any interferance from potential malicious or broken nodes in a network.
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
  "10",
  "Graph Connectivity",
  "3",
  "Number of Failur Nodes",
  "2",
  "Number of Broad Casters",
  "",
  "Number of Distinct Messages",
  "",
)

#set align(left)


#pagebreak()


= Result 
\
== Latency (average across all nodes, measured on the physical clock)and message complexity depending on number of nodes) \

== Latency and message complexity depending on network connectivity \

== Latency  and  message  complexity  depending  on  number  of  actual Byzantine nodes \


#pagebreak()

= Conclusion

#box(
  inset: 1cm,
  [
    #text(14pt)[
      In Conclusion ...
      ]
  ]
)
