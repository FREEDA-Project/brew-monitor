graph [
  directed 1
  node [
    id 0
    label "main"
    cpu 4.0
    ram 16.0
    storage 1024
    availability 99
    subnet "_networkx_list_start"
    subnet "public"
    security "ssl"
    security "firewall"
    energy 0.0
    gpu 0
    group "CLOUD"
    processing_time 0
    cost 9
    carbon 402
  ]
  node [
    id 1
    label "m2"
    cpu 2
    ram 3
    storage 512
    availability 98
    subnet "_networkx_list_start"
    subnet "public"
    security "ssl"
    security "firewall"
    energy 0.0
    gpu 0
    group "CLOUD"
    processing_time 0
    cost 4
    carbon 200
  ]
  node [
    id 2
    label "worker1"
    cpu 8
    ram 16
    storage 1024
    availability 99
    subnet "_networkx_list_start"
    subnet "private"
    security "ssl"
    security "firewall"
    energy 0.0
    gpu 0
    group "CLOUD"
    processing_time 0
    cost 7
    carbon 340
  ]
  node [
    id 3
    label "worker2"
    cpu 8
    ram 16
    storage 1024
    availability 99
    subnet "_networkx_list_start"
    subnet "private"
    security "ssl"
    security "firewall"
    security "encrypted_storage"
    energy 0.0
    gpu 0
    group "CLOUD"
    processing_time 0
    cost 7
    carbon 360
  ]
  edge [
    source 0
    target 2
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 0
    target 3
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 1
    target 2
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 1
    target 3
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 2
    target 0
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 2
    target 1
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 2
    target 3
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 3
    target 0
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 3
    target 1
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
  edge [
    source 3
    target 2
    latency 10
    energy 0.0
    bandwidth +INF
    availability 99
  ]
]
