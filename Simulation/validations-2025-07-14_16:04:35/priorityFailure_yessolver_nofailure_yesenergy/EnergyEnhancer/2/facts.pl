serviceConnection(gateway, aggregator, 0.005, 5.0).
serviceConnection(data_gather_olbia, mongodb_batch_olbia, 0.005, 5.0).
serviceConnection(data_gather_torino, mongodb_batch_torino, 0.005, 5.0).
serviceConnection(aggregator, data_gather_olbia, 0.005, 5.0).
serviceConnection(aggregator, data_gather_torino, 0.005, 5.0).
service(gateway, 0.598, 598.0).
service(data_gather_olbia, 0.598, 598.0).
service(data_gather_torino, 0.598, 598.0).
service(aggregator, 0.598, 598.0).
service(mongodb_batch_olbia, 0.598, 598.0).
service(mongodb_batch_torino, 0.598, 598.0).
node(m2, 200).
node(main, 402).
node(worker1, 340).
node(worker2, 360).
node(worker3, 360).
deployedTo(gateway,tiny,m2).
deployedTo(data_gather_olbia,large,worker1).
deployedTo(data_gather_torino,large,worker1).
deployedTo(aggregator,tiny,worker1).
deployedTo(mongodb_batch_olbia,medium,worker2).
deployedTo(mongodb_batch_torino,medium,worker2).
highConsumptionService(gateway,large,main,1.000).
highConsumptionService(data_gather_olbia,large,worker2,0.896).
highConsumptionService(data_gather_olbia,large,worker3,0.896).
highConsumptionService(data_gather_torino,large,worker2,0.896).
highConsumptionService(data_gather_torino,large,worker3,0.896).
highConsumptionService(aggregator,large,worker2,0.896).
highConsumptionService(aggregator,large,worker3,0.896).
highConsumptionService(mongodb_batch_olbia,medium,worker3,0.896).
highConsumptionService(mongodb_batch_torino,medium,worker3,0.896).
highConsumptionService(analyzer,large,worker2,0.896).
highConsumptionService(analyzer,large,worker3,0.896).
highConsumptionService(mongodb_history,medium,worker3,0.896).
highConsumptionService(gateway,tiny,main,1.000).
highConsumptionService(aggregator,tiny,worker2,0.896).
highConsumptionService(aggregator,tiny,worker3,0.896).
