% Deployment
deployedTo(aggregator, large, worker1).
deployedTo(analyzer, large, worker1).
deployedTo(data_gather_olbia, large, worker1).
deployedTo(data_gather_torino, large, worker1).
deployedTo(gateway, large, main).
deployedTo(mongodb_batch_olbia, medium, worker2).
deployedTo(mongodb_batch_torino, medium, worker2).
deployedTo(mongodb_history, medium, worker2).

% Components failures
unreachable(gateway, 31).
unreachable(gateway, 32).
unreachable(gateway, 33).
unreachable(gateway, 34).
unreachable(gateway, 35).
unreachable(gateway, 36).
unreachable(gateway, 37).
unreachable(gateway, 38).
unreachable(gateway, 39).
unreachable(gateway, 40).
unreachable(gateway, 41).
unreachable(gateway, 42).
unreachable(gateway, 43).
unreachable(gateway, 44).
unreachable(gateway, 45).
unreachable(gateway, 46).
unreachable(gateway, 47).
unreachable(gateway, 48).
unreachable(gateway, 49).
unreachable(gateway, 50).
unreachable(gateway, 51).
unreachable(gateway, 52).
unreachable(gateway, 53).
unreachable(gateway, 54).
unreachable(gateway, 55).
unreachable(gateway, 56).
unreachable(gateway, 57).
unreachable(gateway, 58).
unreachable(gateway, 59).
unreachable(gateway, 60).
unreachable(gateway, 61).
unreachable(gateway, 62).
unreachable(gateway, 63).
unreachable(gateway, 64).
unreachable(gateway, 65).
unreachable(gateway, 66).
unreachable(gateway, 67).
unreachable(gateway, 68).
unreachable(gateway, 69).
unreachable(gateway, 70).
unreachable(gateway, 71).
unreachable(gateway, 72).
unreachable(gateway, 73).
unreachable(gateway, 74).
unreachable(gateway, 75).
unreachable(gateway, 76).
unreachable(gateway, 77).
unreachable(gateway, 78).
unreachable(gateway, 79).
unreachable(gateway, 80).
unreachable(gateway, 81).
unreachable(gateway, 82).
unreachable(gateway, 83).
unreachable(gateway, 84).
unreachable(gateway, 85).
unreachable(gateway, 86).
unreachable(gateway, 87).
unreachable(gateway, 88).
unreachable(gateway, 89).
unreachable(gateway, 90).
unreachable(gateway, 91).
unreachable(gateway, 92).
unreachable(gateway, 93).
unreachable(gateway, 94).
unreachable(gateway, 95).
unreachable(gateway, 96).
unreachable(gateway, 97).
unreachable(gateway, 98).

% Nodes failures
overload(main, cpu, 31, 98).
overload(main, ram, 31, 98).
