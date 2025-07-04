graph [
  directed 1
  node [
    id 0
    label "gateway_large"
    cpu 2
    ram 4
    storage 0
    availability 99
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
    label "data_gather_olbia_large"
    cpu 1
    ram 2
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
  node [
    id 2
    label "data_gather_torino_large"
    cpu 1
    ram 2
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
  node [
    id 3
    label "aggregator_large"
    cpu 2
    ram 4
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
  node [
    id 4
    label "mongodb_batch_olbia_medium"
    cpu 1
    ram 2
    storage 50
    availability 99
    subnet "_networkx_list_start"
    subnet "private"
    security "_networkx_list_start"
    security "encrypted_storage"
    energy 598
    group "CLOUD"
    processing_time 0
  ]
  node [
    id 5
    label "mongodb_batch_torino_medium"
    cpu 1
    ram 2
    storage 50
    availability 99
    subnet "_networkx_list_start"
    subnet "private"
    security "_networkx_list_start"
    security "encrypted_storage"
    energy 598
    group "CLOUD"
    processing_time 0
  ]
  node [
    id 6
    label "analyzer_large"
    cpu 2
    ram 2
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
  node [
    id 7
    label "mongodb_history_medium"
    cpu 2
    ram 4
    storage 100
    availability 99
    subnet "_networkx_list_start"
    subnet "private"
    security "_networkx_list_start"
    security "encrypted_storage"
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
    source 0
    target 6
    latency 25
    energy 5
  ]
  edge [
    source 1
    target 4
    latency 25
    energy 5
  ]
  edge [
    source 2
    target 5
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
  edge [
    source 3
    target 7
    latency 25
    energy 5
  ]
  edge [
    source 6
    target 7
    latency 25
    energy 5
  ]
]
