





if "__main__" == __name__:

    from confluent_kafka.admin import AdminClient
    adminConfluent = AdminClient({'bootstrap.servers': ",".join(["localhost:9092"])})
    groups = adminConfluent.list_groups(group=None)
    print(groups)