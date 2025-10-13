# Example input
## regex:
(1|2)*33*  

## eps-nfa:
Q = {i, q, f};  
A = {0, 1};  
I = i;  
F = {f};  
(i, 1) -> {q, f};  
(q, 0) -> {f};  
(q,'') -> {f};  
(f, 0) -> {f};  