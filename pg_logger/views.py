import logging

from EXPERIMENTS.pg_logger.models import PgLog, PgLogLVL, PgLogLVL_map

logger = logging.getLogger(__name__)


class PgLogger(object):

    def __init__(self, *args, **kwargs):
        return

    def debug(self, *args, **kwargs): self.log_action(level=PgLogLVL.debug.name, *args, **kwargs)

    def info(self, *args, **kwargs): self.log_action(level=PgLogLVL.info.name, *args, **kwargs)

    def warning(self, *args, **kwargs): self.log_action(level=PgLogLVL.warning.name, *args, **kwargs)

    def error(self, *args, **kwargs): self.log_action(level=PgLogLVL.error.name, *args, **kwargs)

    def critical(self, *args, **kwargs): self.log_action(level=PgLogLVL.critical.name, *args, **kwargs)

    def log_action(self, level, object_model, object_id: int, text: str, user=None, company_user=None, *args, **kwargs):
        if not user and company_user:
            user = company_user.user

        log_level = getattr(logger, level)
        model_name = object_model._meta.concrete_model.__name__
        log_level(
            f"{text} | model_name={model_name} (model_id={object_id}) | user={user} | company_user={company_user} ")

        PgLog.objects.create(
            level=PgLogLVL_map[level],
            user=user,
            company_user=company_user,
            model_name=model_name,
            model_id=object_id,
            message=text,
            params={"args": args, "kwargs": kwargs}
        )



from logging import Handler


class DBHandler(Handler,object):
    # def __init__(self):
    #     super(DBHandler, self).__init__()

    def emit(self,record):
        # model = record.model
        # log_entry = PgLog(level=record.levelname, message=record.msg)
        print('record =', record)
        print('dir record =', dir(record))
        # log_entry = PgLog(
        #     level=record.levelname,
        #     # level=PgLogLVL_map[level],
        #     message=record.msg,
        #     user=record.user,
        #     company_user=record.company_user,
        #     content_type=record.content_type,
        #     object_id=record.object_id,
        #     params={"args": record.args, "kwargs": record.kwargs}
        #
        # )
        # log_entry.save()


import logging

from django_db_logger.config import DJANGO_DB_LOGGER_ENABLE_FORMATTER

db_default_formatter = logging.Formatter()


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        # from .models import StatusLog

        trace = None

        if record.exc_info:
            trace = db_default_formatter.formatException(record.exc_info)

        if DJANGO_DB_LOGGER_ENABLE_FORMATTER:
            msg = self.format(record)
        else:
            msg = record.getMessage()

        kwargs = {
            'logger_name': record.name,
            'level': record.levelno,
            'msg': msg,
            'trace': trace
        }

        # StatusLog.objects.create(**kwargs)

    def format(self, record):
        print('asdasd')
        if self.formatter:
            fmt = self.formatter
        else:
            fmt = db_default_formatter

        if type(fmt) == logging.Formatter:
            record.message = record.getMessage()

            if fmt.usesTime():
                record.asctime = fmt.formatTime(record, fmt.datefmt)

            # ignore exception traceback and stack info

            return fmt.formatMessage(record)
        else:
            return fmt.format(record)

