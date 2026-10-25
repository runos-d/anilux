def chat_cascade(collector, field, sub_objs, using):
    collector.collect(sub_objs, source=field.remote_field.model,
                      source_attr=field.name, nullable=False)
