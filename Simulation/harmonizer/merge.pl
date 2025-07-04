affinity(identity_provider,large,redis,large).
affinity(api,large,database,large,0.006).
avoid(api,large,private3,0.91).
avoid(database,large,private3,1.0).
