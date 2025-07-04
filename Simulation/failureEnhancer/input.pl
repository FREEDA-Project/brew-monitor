% Deployment
deployedTo(api, large, private1).
deployedTo(database, large, private5).
deployedTo(etcd, large, private3).
deployedTo(frontend, large, public1).
deployedTo(identity_provider, large, private1).
deployedTo(load_balancer, large, public1).
deployedTo(redis, large, private3).

% Components failures
unreachable(frontend, 126).
unreachable(frontend, 127).
unreachable(frontend, 128).
unreachable(frontend, 129).
unreachable(frontend, 130).
unreachable(frontend, 131).
unreachable(frontend, 132).
unreachable(frontend, 133).
unreachable(frontend, 134).
unreachable(frontend, 135).
unreachable(frontend, 136).
unreachable(frontend, 137).
unreachable(frontend, 138).
unreachable(frontend, 139).
unreachable(frontend, 140).
unreachable(frontend, 141).
unreachable(frontend, 142).
unreachable(frontend, 143).
unreachable(load_balancer, 126).
unreachable(load_balancer, 127).
unreachable(load_balancer, 128).
unreachable(load_balancer, 129).
unreachable(load_balancer, 130).
unreachable(load_balancer, 131).
unreachable(load_balancer, 132).
unreachable(load_balancer, 133).
unreachable(load_balancer, 134).
unreachable(load_balancer, 135).
unreachable(load_balancer, 136).
unreachable(load_balancer, 137).
unreachable(load_balancer, 138).
unreachable(load_balancer, 139).
unreachable(load_balancer, 140).
unreachable(load_balancer, 141).
unreachable(load_balancer, 142).
unreachable(load_balancer, 143).
internal(load_balancer, 143).

%  highUsage(S, FS, R, TI, TF),
highUsage(frontend, large, cpu, 126, 143).

%  highUsage(S, FS, R, TI, TF),
highUsage(frontend, large, ram, 126, 143).

% Nodes failures
overload(public1, cpu, 126, 143).
overload(public1, ram, 126, 143).
disconnection(public1, 126, 143).