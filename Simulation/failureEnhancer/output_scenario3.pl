% Deployment
deployedTo(api, large, private1).
deployedTo(database, large, private5).
deployedTo(etcd, large, private4).
deployedTo(frontend, large, public1).
deployedTo(identity_provider, large, private2).
deployedTo(load_balancer, large, public1).
deployedTo(redis, large, private1).

% Components failures
unreachable(api, 48).
unreachable(api, 49).
unreachable(api, 50).
unreachable(api, 51).
unreachable(api, 52).
unreachable(api, 53).
unreachable(api, 54).
unreachable(api, 55).
unreachable(api, 56).
unreachable(api, 57).
unreachable(api, 58).
unreachable(api, 59).
unreachable(api, 60).
unreachable(api, 61).
unreachable(api, 62).
unreachable(api, 63).
unreachable(api, 64).
unreachable(api, 65).
unreachable(api, 66).
unreachable(api, 67).
unreachable(api, 68).
unreachable(api, 69).
unreachable(api, 70).
unreachable(api, 71).
unreachable(api, 72).
unreachable(api, 73).
unreachable(api, 74).
unreachable(api, 75).
unreachable(api, 76).
unreachable(api, 77).
unreachable(api, 78).
unreachable(api, 79).
unreachable(api, 80).
unreachable(api, 81).
unreachable(api, 82).
unreachable(api, 83).
unreachable(api, 84).
unreachable(api, 85).
unreachable(api, 86).
unreachable(api, 87).
unreachable(api, 88).
unreachable(api, 89).
unreachable(api, 90).
unreachable(api, 91).
unreachable(api, 92).
unreachable(api, 93).
unreachable(api, 94).
unreachable(api, 95).
unreachable(api, 96).
unreachable(api, 97).
unreachable(api, 98).
unreachable(redis, 48).
unreachable(redis, 49).
unreachable(redis, 50).
unreachable(redis, 51).
unreachable(redis, 52).
unreachable(redis, 53).
unreachable(redis, 54).
unreachable(redis, 55).
unreachable(redis, 56).
unreachable(redis, 57).
unreachable(redis, 58).
unreachable(redis, 59).
unreachable(redis, 60).
unreachable(redis, 61).
unreachable(redis, 62).
unreachable(redis, 63).
unreachable(redis, 64).
unreachable(redis, 65).
unreachable(redis, 66).
unreachable(redis, 67).
unreachable(redis, 68).
unreachable(redis, 69).
unreachable(redis, 70).
unreachable(redis, 71).
unreachable(redis, 72).
unreachable(redis, 73).
unreachable(redis, 74).
unreachable(redis, 75).
unreachable(redis, 76).
unreachable(redis, 77).
unreachable(redis, 78).
unreachable(redis, 79).
unreachable(redis, 80).
unreachable(redis, 81).
unreachable(redis, 82).
unreachable(redis, 83).
unreachable(redis, 84).
unreachable(redis, 85).
unreachable(redis, 86).
unreachable(redis, 87).
unreachable(redis, 88).
unreachable(redis, 89).
unreachable(redis, 90).
unreachable(redis, 91).
unreachable(redis, 92).
unreachable(redis, 93).
unreachable(redis, 94).
unreachable(redis, 95).
unreachable(redis, 96).
unreachable(redis, 97).
unreachable(redis, 98).

% Nodes failures
overload(private1, cpu, 48, 93).
overload(private1, ram, 50, 93).
