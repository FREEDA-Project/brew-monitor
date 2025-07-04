
set of int: CompFlavs = 1..sum(c in Comps)(length(Flav[c]));

function int: Idx(Comps: c, Flavs: f) =
    sum (i in 1..c-1)(length(Flav[Comps[i]])) + arg_max([f = i | i in Flav[c]]);

enum Res = C(CRes) ++ N(NRes);

array[CompFlavs] of set of Res: Req_cf = [
    {r | r in Res where comReq[cf, r] != worstBounds[r]} | cf in CompFlavs
];

array[Comps, Flavs, Comps] of set of Res: Req_cfc = array3d(Comps, Flavs, Comps,
    [{r | r in Res where depReq[c1, i, c2, r] != worstBounds[r]}
    | c1 in Comps, i in Flavs, c2 in Comps
]);

set of int: Nodes0 = {0} union Nodes;

array[Nodes] of set of Res: Req_n = [
    {r | r in Res where nodeCap[n, r] != worstBounds[r]} | n in Nodes
];

constraint assert(forall(r in Res)(nodeCap[0,r] = bestBounds[r]),
    "Assertion nodeCap[0,r] = bestBounds[r] failed.", true);

constraint assert (forall(n in Nodes, r in Res)(
    linkCap[n,0,r] = bestBounds[r] /\ linkCap[0, n, r] = bestBounds[r]),
    "Assertion linkCap[n,0,r] = linkCap[0,n,r] = bestBounds[r] failed.", true);

constraint assert (forall(r in Res)(cost[0,r] = 0),
    "Assertion cost[0,r] = 0 failed.", true);

array [{0} union CompFlavs, Nodes0] of var 0..1: D;

array [Comps] of var Nodes0: node = [
    sum(i in Flav[c], j in Nodes)(j * D[Idx(c, i), j]) | c in Comps
];

var int: totCost = sum(c in Comps, i in Flav[c], r in Req_cf[Idx(c, i)])(
    comReq[Idx(c, i), r] * cost[node[c], r] * D[Idx(c, i), node[c]]
);

var int: totCarb = sum(cs in Comps, is in Flav[cs], js in Nodes)(
  D[Idx(cs, is), js] * (
    energy[Idx(cs, is)] * carb[js] + sum(
      cd in Comps,
      id in Flav[cd] where mayUse[cd, Idx(cs, is)] = 1 /\ energy_dependency[cs, is, cd] > 0,
      jd in Nodes
    )(
      D[Idx(cd, id), jd] * energy_dependency[cs, is, cd] * round((carb[js] + carb[jd]) / 2)
    )
  )
);

constraint forall(j in Nodes0)(D[0, j] = 0);
constraint forall(i in CompFlavs)(D[i, 0] = 0);

constraint forall(c in Comps)(
    sum(i in Flav[c], j in Nodes)(D[Idx(c, i), j]) <= 1
);

constraint forall(m in mustComps)(
    sum (i in Flav[m], j in Nodes)(D[Idx(m, i), j]) > 0 /\ node[m] > 0
);

constraint forall(
    c in Comps,
    i in Flav[c],
    cu in Comps,
    iu in Flav[cu] where Uses[Idx(c, i), Idx(cu, iu)] = 1
)(
    sum(j in Nodes)(D[Idx(c, i), j]) <=
    sum(k in Flav[cu], j in Nodes where imp[cu,k] >= imp[cu,iu])(D[Idx(cu, k),j])
);

constraint forall(c in Comps diff mustComps)(
    sum(i in Flav[c], j in Nodes)(D[Idx(c, i), j]) <=
    sum(
        cs in Comps where c != cs,
        is in Flav[cs] where mayUse[c, Idx(cs, is)] = 1,
        j in Nodes
    )(D[Idx(cs, is), j])
);

constraint forall(j in Nodes, r in Req_n[j] where r in C(CRes)) (
    if worstBounds[r] = MIN_RBOUNDS then
        sum(c in Comps, i in Flav[c] where r in Req_cf[Idx(c,i)])
        (comReq[Idx(c,i), r] * D[Idx(c,i), j]) <= nodeCap[j,r]
    else
        assert(false, "·Lower bound for 'maximization' resources unsupported.")
    endif
);

constraint forall(
  c in Comps,
  i in Flav[c],
  r in Req_cf[Idx(c,i)] where r in N(NRes)
)(
    if worstBounds[r] = MIN_RBOUNDS then
        comReq[Idx(c,i), r] * D[Idx(c,i), node[c]] <= nodeCap[node[c], r]
    else
        comReq[Idx(c,i), r] >= nodeCap[node[c], r] * D[Idx(c,i), node[c]]
    endif
);

constraint forall(
    cs in Comps,
    is in Flav[cs],
    cd in Comps where mayUse[cd, Idx(cs, is)] = 1,
    r in Req_cfc[cs, is, cd] where r in N(NRes),
)(
    if worstBounds[r] = MIN_RBOUNDS then
        depReq[cs, is, cd, r] * sum(j in Nodes)(D[Idx(cs, is), j]) <=
        linkCap[node[cs], node[cd], r]
    else
        depReq[cs, is, cd, r] >= sum(j in Nodes)(D[Idx(cs, is), j]) *
        linkCap[node[cs], node[cd], r]
    endif
);

constraint totCost <= costBudget;
constraint totCarb <= carbBudget;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Input data for case_study_1 in master %%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
enum Comps = {gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history};
set of Comps: mustComps = {gateway};
enum Flavs = {tiny, large, medium};
array[Comps] of set of Flavs: Flav = [{tiny, large}, {tiny, large}, {tiny, large}, {tiny, large}, {medium}, {medium}, {large}, {medium}];
array[Comps, Flavs] of int: imp = array2d(Comps, Flavs, [
	%tiny, large, medium
	1, 2, 0, % gateway
	1, 2, 0, % data_gather_olbia
	1, 2, 0, % data_gather_torino
	1, 2, 0, % aggregator
	0, 0, 1, % mongodb_batch_olbia
	0, 0, 1, % mongodb_batch_torino
	0, 1, 0, % analyzer
	0, 0, 1, % mongodb_history
]);
array[CompFlavs] of int: energy = [598, 598, 598, 598, 598, 598, 598, 598, 598, 598, 598, 598];
array[Comps, Flavs, Comps] of int: energy_dependency = array3d(Comps, Flavs, Comps, [

	% gateway
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 0, 0, 5, 0, 0, 0, 0, % tiny
	0, 0, 0, 5, 0, 0, 5, 0, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

	% data_gather_olbia
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 0, 0, 0, 0, 0, 0, 0, % tiny
	0, 0, 0, 0, 5, 0, 0, 0, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

	% data_gather_torino
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 0, 0, 0, 0, 0, 0, 0, % tiny
	0, 0, 0, 0, 0, 5, 0, 0, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

	% aggregator
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 5, 5, 0, 0, 0, 0, 0, % tiny
	0, 5, 5, 0, 0, 0, 0, 5, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

	% mongodb_batch_olbia
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 0, 0, 0, 0, 0, 0, 0, % tiny
	0, 0, 0, 0, 0, 0, 0, 0, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

	% mongodb_batch_torino
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 0, 0, 0, 0, 0, 0, 0, % tiny
	0, 0, 0, 0, 0, 0, 0, 0, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

	% analyzer
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 0, 0, 0, 0, 0, 0, 0, % tiny
	0, 0, 0, 0, 0, 0, 0, 5, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

	% mongodb_history
	%gateway, data_gather_olbia, data_gather_torino, aggregator, mongodb_batch_olbia, mongodb_batch_torino, analyzer, mongodb_history
	0, 0, 0, 0, 0, 0, 0, 0, % tiny
	0, 0, 0, 0, 0, 0, 0, 0, % large
	0, 0, 0, 0, 0, 0, 0, 0, % medium

]);
array[CompFlavs, CompFlavs] of 0..1: Uses = array2d(CompFlavs, CompFlavs, [
	%gateway_tiny, gateway_large, data_gather_olbia_tiny, data_gather_olbia_large, data_gather_torino_tiny, data_gather_torino_large, aggregator_tiny, aggregator_large, mongodb_batch_olbia_medium, mongodb_batch_torino_medium, analyzer_large, mongodb_history_medium
	0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, % gateway_tiny
	0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, % gateway_large
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % data_gather_olbia_tiny
	0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, % data_gather_olbia_large
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % data_gather_torino_tiny
	0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, % data_gather_torino_large
	0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, % aggregator_tiny
	0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 1, % aggregator_large
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % mongodb_batch_olbia_medium
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % mongodb_batch_torino_medium
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, % analyzer_large
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % mongodb_history_medium
]);
array[Comps, CompFlavs] of 0..1: mayUse = array2d(Comps, CompFlavs, [
	%gateway_tiny, gateway_large, data_gather_olbia_tiny, data_gather_olbia_large, data_gather_torino_tiny, data_gather_torino_large, aggregator_tiny, aggregator_large, mongodb_batch_olbia_medium, mongodb_batch_torino_medium, analyzer_large, mongodb_history_medium
	0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % gateway
	0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, % data_gather_olbia
	0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, % data_gather_torino
	1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % aggregator
	0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, % mongodb_batch_olbia
	0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, % mongodb_batch_torino
	0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, % analyzer
	0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, % mongodb_history
]);
enum CRes = {cpu, ram, storage};
enum NRes = {availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public};
int: MAX_RBOUNDS = 1024;
int: MIN_RBOUNDS = 0;
array[Res] of MIN_RBOUNDS..MAX_RBOUNDS: worstBounds = [
	MIN_RBOUNDS, % cpu
	MIN_RBOUNDS, % ram
	MIN_RBOUNDS, % storage
	MIN_RBOUNDS, % availability
	MAX_RBOUNDS, % latency
	MIN_RBOUNDS, % security_encrypted_storage
	MIN_RBOUNDS, % security_firewall
	MIN_RBOUNDS, % security_ssl
	MIN_RBOUNDS, % subnet_private
	MIN_RBOUNDS, % subnet_public
];
array[Res] of MIN_RBOUNDS..MAX_RBOUNDS: bestBounds = [
	MAX_RBOUNDS, % cpu
	MAX_RBOUNDS, % ram
	MAX_RBOUNDS, % storage
	MAX_RBOUNDS, % availability
	MIN_RBOUNDS, % latency
	MAX_RBOUNDS, % security_encrypted_storage
	MAX_RBOUNDS, % security_firewall
	MAX_RBOUNDS, % security_ssl
	MAX_RBOUNDS, % subnet_private
	MAX_RBOUNDS, % subnet_public
];

array[CompFlavs, Res] of int: comReq = array2d(CompFlavs, Res, [
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	1, 2, MIN_RBOUNDS, 98, MAX_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, 1, % gateway_tiny
	2, 4, MIN_RBOUNDS, 99, MAX_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, 1, % gateway_large
	1, 1, MIN_RBOUNDS, 97, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, % data_gather_olbia_tiny
	1, 2, MIN_RBOUNDS, 99, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, % data_gather_olbia_large
	1, 1, MIN_RBOUNDS, 97, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, % data_gather_torino_tiny
	1, 2, MIN_RBOUNDS, 99, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, % data_gather_torino_large
	1, 2, MIN_RBOUNDS, 99, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, % aggregator_tiny
	2, 4, MIN_RBOUNDS, 99, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, % aggregator_large
	1, 2, 50, 99, MAX_RBOUNDS, 1, MIN_RBOUNDS, MIN_RBOUNDS, 1, MIN_RBOUNDS, % mongodb_batch_olbia_medium
	1, 2, 50, 99, MAX_RBOUNDS, 1, MIN_RBOUNDS, MIN_RBOUNDS, 1, MIN_RBOUNDS, % mongodb_batch_torino_medium
	2, 2, MIN_RBOUNDS, 99, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 1, 1, MIN_RBOUNDS, % analyzer_large
	2, 4, 100, 99, MAX_RBOUNDS, 1, MIN_RBOUNDS, MIN_RBOUNDS, 1, MIN_RBOUNDS, % mongodb_history_medium
]);
enum Nodes = {m2, main, worker1, worker2};

array[Nodes0, Res] of int: nodeCap = array2d(Nodes0, Res,
	[bestBounds[r] | r in Res] ++ [ % No node
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	2, 3, 512, 98, 0, 0, 1, 1, 0, 1, % m2
	4, 16, 1024, 99, 0, 0, 1, 1, 0, 1, % main
	8, 16, 1024, 99, 0, 0, 1, 1, 1, 0, % worker1
	8, 16, 1024, 99, 0, 1, 1, 1, 1, 0, % worker2
]);
array[Comps, Flavs, Comps, Res] of int: depReq = array4d(Comps, Flavs, Comps, Res, [

	% gateway

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


	% data_gather_olbia

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


	% data_gather_torino

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


	% aggregator

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


	% mongodb_batch_olbia

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


	% mongodb_batch_torino

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


	% analyzer

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 97, 25, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


	% mongodb_history

	% tiny
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% large
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history

	% medium
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % gateway
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % data_gather_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % aggregator
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_olbia
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_batch_torino
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % analyzer
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % mongodb_history


]);
array[Nodes0, Nodes0, Res] of int: linkCap = array3d(Nodes0, Nodes0, Res, [

	% 0
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % 0
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % m2
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % main
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % worker1
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % worker2

	% m2
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % 0
	2, 3, 512, 98, 0, 0, 1, 1, 0, 1, % m2
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % main
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % worker1
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % worker2

	% main
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % 0
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % m2
	4, 16, 1024, 99, 0, 0, 1, 1, 0, 1, % main
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % worker1
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % worker2

	% worker1
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % 0
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % m2
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % main
	8, 16, 1024, 99, 0, 0, 1, 1, 1, 0, % worker1
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % worker2

	% worker2
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MIN_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, MAX_RBOUNDS, % 0
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % m2
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % main
	MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, 99, 10, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, MIN_RBOUNDS, % worker1
	8, 16, 1024, 99, 0, 1, 1, 1, 1, 0, % worker2

]);
array[Nodes0, Res] of int: cost = array2d(Nodes0, Res, [0 | r in Res] ++ [ % No node
	%cpu, ram, storage, availability, latency, security_encrypted_storage, security_firewall, security_ssl, subnet_private, subnet_public
	4, 0, 0, 0, 0, 0, 0, 0, 0, 0, % m2
	9, 0, 0, 0, 0, 0, 0, 0, 0, 0, % main
	7, 0, 0, 0, 0, 0, 0, 0, 0, 0, % worker1
	7, 0, 0, 0, 0, 0, 0, 0, 0, 0, % worker2
]);
array[Nodes0] of int: carb = array1d(Nodes0, [0] ++ [ % No node
	200, 402, 340, 360
]);
int: costBudget = 2000000;
int: carbBudget = 2000000;
var int: obj = sum(
	c in Comps,
	i in Flav[c],
	j in Nodes where D_old[Idx(c, i), j] = 1
)(
	D[Idx(c, i), j]
);

solve maximize obj;

var int: app_quality = sum(c in Comps, i in Flav[c])(
    imp[c,i] * sum([D[Idx(c,i),j] | j in Nodes])
);
output [
    if fix(node[c]) > 0 then
        "Component \(c) deployed in flavour \([Flavs[i] | i in Flav[c] where D[Idx(c, i), node[c]] > 0][1]) on node \(Nodes[node[c]]).\n"
    else
        "Component \(c) not deployed.\n"
    endif
    | c in Comps
] ++ [
    "Objective value: \(obj)\n\tApp quality: \(app_quality)\n\tTotal cost: \(totCost)\n\tTotal carb: \(totCarb)"
];

array[CompFlavs, Nodes] of 0..1: D_old = array2d(CompFlavs, Nodes, [
	%m2, main, worker1, worker2
	0, 0, 0, 0, % gateway_tiny
	0, 1, 0, 0, % gateway_large
	0, 0, 0, 0, % data_gather_olbia_tiny
	0, 0, 1, 0, % data_gather_olbia_large
	0, 0, 0, 0, % data_gather_torino_tiny
	0, 0, 1, 0, % data_gather_torino_large
	0, 0, 0, 0, % aggregator_tiny
	0, 0, 1, 0, % aggregator_large
	0, 0, 0, 1, % mongodb_batch_olbia_medium
	0, 0, 0, 1, % mongodb_batch_torino_medium
	0, 0, 1, 0, % analyzer_large
	0, 0, 0, 1, % mongodb_history_medium
]);
