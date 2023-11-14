# from clickhouse_backend.models import ClickhouseModel
# from api.models import Event
#
# from clickhouse_backend.models import ClickhouseModel
#
#
# def get_subclasses(class_):
#     classes = class_.__subclasses__()
#
#     index = 0
#     while index < len(classes):
#         classes.extend(classes[index].__subclasses__())
#         index += 1
#
#     return list(set(classes))
#
#
# class ClickHouseRouter:
#     def __init__(self):
#         self.route_model_names = set()
#         for model in get_subclasses(ClickhouseModel):
#             if model._meta.abstract:
#                 continue
#             self.route_model_names.add(model._meta.label_lower)
#
#     def db_for_read(self, model, **hints):
#         if (model._meta.label_lower in self.route_model_names
#                 or hints.get("clickhouse")):
#             return "clickhouse"
#         return None
#
#     def db_for_write(self, model, **hints):
#         if (model._meta.label_lower in self.route_model_names
#                 or hints.get("clickhouse")):
#             return "clickhouse"
#         return None
#
#     def allow_migrate(self, db, app_label, model_name=None, **hints):
#         if (f"{app_label}.{model_name}" in self.route_model_names
#                 or hints.get("clickhouse")):
#             return db == "clickhouse"
#         elif db == "clickhouse":
#             return False
#         return None
#
# # class ClickHouseRouter:
# #
# #     def __init__(self):
# #         self.route_model_names = set()
# #         print('??? ')
# #         print('get_subclasses(ClickhouseModel) =', get_subclasses(ClickhouseModel))
# #         for model in get_subclasses(ClickhouseModel):
# #             if model._meta.abstract:
# #                 continue
# #             print('label_lower =', model._meta.label_lower)
# #             self.route_model_names.add(model._meta.label_lower)
# #
# #     def db_for_read(self, model, **hints):
# #         print('>>> db_for_read')
# #         print('model =', model)
# #         # if model._meta.label_lower in self.route_model_names
# #         #         or hints.get('clickhouse')):
# #         if model == Event:
# #             return 'analytic'
# #         return None
# #
# #     def db_for_write(self, model, **hints):
# #         print('>>> db_for_write')
# #         print('model =', model)
# #         # if (model._meta.label_lower in self.route_model_names
# #         #         or hints.get('clickhouse')):
# #         if model == Event:
# #             return 'analytic'
# #         return None
# #
# #     def allow_migrate(self, db, app_label, model_name=None, **hints):
# #         # print('??? =', f'{app_label}.{model_name}')
# #         # raise Exception('wtf')
# #
# #         if f'{app_label}.{model_name}' == 'api.event':
# #             return db == 'analytic'
# #         elif db == 'analytic':
# #             return False
# #         return None
