from logManager import logger

from constants import YD_ENDPOINT, YD_TOKEN, YD_PATH, YD_PATH_TOKEN
from datetime import datetime, date

import ydb
import ydb.iam


class DbHandler:
    """Класс для взаимодействия с БД"""

    def __init__(self):
        """Конструктор"""
        logger.debug("start init ydb")
        driver_config = ydb.DriverConfig(
            endpoint=YD_ENDPOINT,
            database=YD_PATH,
            #credentials=ydb.iam.MetadataUrlCredentials(),
             credentials=ydb.AccessTokenCredentials(YD_TOKEN)
            # credentials=ydb.iam.ServiceAccountCredentials.from_file(YD_PATH_TOKEN
        )

        self.driver = ydb.Driver(driver_config)
        try:
            self.driver.wait(timeout=5)
            logger.debug("end init ydb")
        except TimeoutError:
            print("Connect failed to YDB")
            print("Last reported errors by discovery:")
            print(self.driver.discovery_debug_details())
            logger.debug("end init ydb (error)")
            exit(1)

    def get_room_list(self):
        session = self.driver.table_client.session().create()
        result = session.transaction(ydb.SerializableReadWrite()).execute(
            """
            SELECT * FROM room_list;
            """,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2),
        )
        return result[0]

    def get_user_rating(self):
        session = self.driver.table_client.session().create()
        result = session.transaction(ydb.SerializableReadWrite()).execute(
            """
            SELECT * FROM user_rating;
            """,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2),
        )
        return result[0]

    def get_current_user(self, idUser: int):
        session = self.driver.table_client.session().create()
        result = session.transaction(ydb.SerializableReadWrite()).execute(
            f"""
            SELECT * FROM user_rating WHERE id_user = {idUser};
            """,
            commit_tx=True,
            settings=ydb.BaseRequestSettings().with_timeout(3).with_operation_timeout(2),
        )
        return result[0]

    def upsert_user_rating(self, id_user, last_check_datetime, current_points, fullname,  maximum_points,
                           username):
        session = self.driver.table_client.session().create()

        try:
            id_user = int(id_user)
            current_points = int(current_points) if current_points is not None else 0
            maximum_points = int(maximum_points) if maximum_points is not None else 0

            # Преобразование параметров даты и времени
            if isinstance(last_check_datetime, str):
                check_datetime_str = f"Datetime('{datetime.strptime(last_check_datetime, '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%SZ')}')"
            else:
                check_datetime_str = "Datetime('1970-01-01T00:00:00Z')"  # Значение по умолчанию

            # Формирование и выполнение запроса
            query = f"""
            UPSERT INTO user_rating (id_user, last_check_datetime, current_points, fullname, maximum_points, username) VALUES 
            ({id_user}, {check_datetime_str}, {current_points}, '{fullname}', {maximum_points}, '{username}');
            """

            session.transaction().execute(
                query,
                commit_tx=True
            )

        except Exception as e:
            logger.error(f"An error occurred: {e}")
