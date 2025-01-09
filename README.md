# Distributed Lab

This repository contains the implementation of the Causal-Order Broadcast Protocol with Byzantine Fault Tolerance, developed during our project at TU Delft.

## Overview of the Algorithm

The algorithm is structured into three layers, each building upon the guarantees of the previous one to achieve Reliable Causal Order Broadcast. Below are the details of each layer:

### 1. Reliable Communication: Dolev Algorithm
This layer ensures the following properties:

- **RC-Validity:** If a correct process `p` broadcasts a message `m`, then every correct process eventually RC-delivers `m`.
- **RC-No Duplication:** No correct process RC-delivers a message `m` more than once.
- **RC-Integrity:** If a correct process RC-delivers a message `m` with sender `p_i`, then `m` was previously broadcast by `p_i`.

### 2. Reliable Broadcast: Bracha Protocol
This layer builds on Reliable Communication to provide:

- **BRB-Validity:** If a correct process `p` broadcasts a message `m`, then every correct process eventually BRB-delivers `m`.
- **BRB-No Duplication:** No correct process BRB-delivers a message `m` more than once.
- **BRB-Integrity:** If a correct process BRB-delivers a message `m` with sender `p_i`, then `m` was previously broadcast by `p_i`.
- **BRB-Agreement:** If some correct process BRB-delivers a message `m`, then every correct process eventually BRB-delivers `m`.

### 3. Reliable Causal Order Broadcast
This top layer ensures:

- **RCO-Validity:** If a correct process `p` broadcasts a message `m`, then every correct process eventually RCO-delivers `m`.
- **RCO-No Duplication:** No correct process RCO-delivers a message `m` more than once.
- **RCO-Integrity:** If a correct process RCO-delivers a message `m` with sender `p_i`, then `m` was previously broadcast by `p_i`.
- **RCO-Agreement:** If some correct process RCO-delivers a message `m`, then every correct process eventually RCO-delivers `m`.
- **RCO-Causal Order:** No correct process `p_i` RCO-delivers a message `m_2` unless it has already delivered every message `m_1` such that `m_1 → m_2`.
- 
## Contributors
- [halantown](https://github.com/halantown)
- [for9interesting](https://github.com/for9interesting)

## References
The implementation and design are based on the following seminal works in distributed systems and Byzantine Fault Tolerance:

- C. Cachin, R. Guerraoui, and L. E. T. Rodrigues, *Introduction to Reliable and Secure Distributed Programming*, 2011.
- G. Bracha, “An asynchronous [(n-1)/3]-resilient consensus protocol,” in PODC, 1984.
- G. Bracha and S. Toueg, “Asynchronous consensus and broadcast protocols,” J. ACM, vol. 32, no. 4, pp. 824–840, 1985.
- G. Bracha, “Asynchronous Byzantine agreement protocols,” Inf. Comput., vol. 75, no. 2, pp. 130–143, 1987.
- M. Raynal, *Fault-tolerant message-passing distributed systems: an algorithmic approach*, 2018.
- S. Bonomi, J. Decouchant, G. Farina, V. Rahli, and S. Tixeuil, “Practical Byzantine reliable broadcast on partially connected networks,” in *2021 IEEE 41st International Conference on Distributed Computing Systems (ICDCS)*, pp. 506–516, IEEE, 2021.
- D. Dolev, “Unanimity in an unknown and unreliable environment,” in FOCS, IEEE, 1981.
- S. Bonomi, G. Farina, and S. Tixeuil, “Multi-hop Byzantine reliable broadcast with honest dealer made practical,” *Journal of the Brazilian Computer Society*, vol. 25, pp. 1–23, 2019.
