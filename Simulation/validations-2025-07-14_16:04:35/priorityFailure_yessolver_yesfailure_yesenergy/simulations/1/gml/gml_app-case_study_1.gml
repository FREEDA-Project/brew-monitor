graph [
  directed 1
  node [
    id 0
    label "gateway_tiny"
    cpu 1
    ram 2
    storage 0
    availability 98
    subnet "_networkx_list_start"
    subnet "public"
    security "firewall"
    security "ssl"
    energy 598
    group "CLOUD"
    processing_time 0
  ]
  node [
    id 1
    label "data_gather_olbia_tiny"
    cpu 1
    ram 1
    storage 0
    availability 97
    subnet "_networkx_list_start"
    subnet "private"
    security "_networkx_list_start"
    security "ssl"
    energy 598
    group "CLOUD"
    processing_time 0
  ]
  node [
    id 2
    label "data_gather_torino_tiny"
    cpu 1
    ram 1
    storage 0
    availability 97
    subnet "_networkx_list_start"
    subnet "private"
    security "_networkx_list_start"
    security "ssl"
    energy 598
    group "CLOUD"
    processing_time 0
  ]
  node [
    id 3
    label "aggregator_tiny"
    cpu 1
    ram 4.0
    storage 0
    availability 99
    subnet "_networkx_list_start"
    subnet "private"
    security "_networkx_list_start"
    security "ssl"
    energy 598
    group "CLOUD"
    processing_time 0
  ]
  edge [
    source 0
    target 3
    latency 25
    energy 5
  ]
  edge [
    source 3
    target 1
    latency 25
    energy 5
  ]
  edge [
    source 3
    target 2
    latency 25
    energy 5
  ]
]
