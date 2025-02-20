'''
Dan Zhang  migrate DL2 to DL3 multi format entity to send multiple commands at once
'''

import sqlalchemy
from dripline.implementations.postgres_sensor_logger import PostgresSensorLogger 

import logging
logger = logging.getLogger(__name__)

__all__ = ['ADMXSensorLogger']



class ADMXSensorLogger(PostgresSensorLogger):
    '''In standard SCPI, you should be able to send a bunch of requests separated by colons
       This spime does this and returns a json structure organized by label'''
    def __init__(self,
                 sensor_type_map_table="",
                 sensor_type_match_column="sensor_name",
                 sensor_type_column_name="epics_data_type",
                 data_tables_dict={},
                 **kwargs):
        '''
        sensor_type_map_table (str): name of the child endpoint of this instance which provides access to the endpoint_id_map, which stores the sensor type
        sensor_type_column_name (str):  name of the column to use for the return type (matched against keys in the data_tables_dict argument here)
        sensor_type_match_column (str): column against which to check for matches to the sensor name
        data_tables_dict (dict):  dictionary mapping types (in the sensor_type_map_table) to child endpoints of this instance which provide access to the data_table for that type
        '''
        PostgresSensorLogger.__init__(self, **kwargs)
        self._sensor_type_map_table=sensor_type_map_table
        self._sensor_type_match_column = sensor_type_match_column
        self._sensor_type_column_name = sensor_type_column_name
        self._data_tables_dict = data_tables_dict
   
    def process_payload(self, a_payload, a_routing_key_data, a_message_timestamp):
        
        try:
            sensor_name = a_routing_key_data["sensor_name"]
            this_type = None
            this_table = self.sync_children[self._sensor_type_map_table]
            where_eq_dict_local ={self._sensor_type_match_column: sensor_name}
            column_name = self._sensor_type_column_name
            this_type = this_table.do_select(return_cols=[column_name], where_eq_dict=where_eq_dict_local)
            if not this_type[1]:
                logger.critical('endpoint with name "{}" was not found in database hence failed to log its value; might need to add it to the db'.format(sensor_name))
                return
            else:
                sensor_type = this_type[1][0][0]
                if not sensor_type in self._data_tables_dict:
                    logger.critical(f'endpoint with name "{sensor_name}" is not configured with a recognized type in the sensors_list table')
                    logger.critical(f'sensor type is {sensor_type}')
                    logger.critical(f'data tables: {self._data_tables_dict}')
                    return
                else:
                    this_data_table = self.sync_children[self._data_tables_dict[sensor_type]]

                    # combine data sources
                    insert_data = {'timestamp': a_message_timestamp}
                    insert_data.update(a_routing_key_data)
                    insert_data.update(a_payload.to_python())
                    logger.info(f"Inserting from endpoint {self._data_tables_dict[sensor_type]}; data are:\n{insert_data}")
                    # do the insert
                    insert_return = this_data_table.do_insert(**insert_data)
                    logger.debug(f"Return from insertion: {insert_return}")
                    logger.info("finished processing data")
        except sqlalchemy.exc.SQLAlchemyError as err:
            logger.critical(f'Received SQL error while doing insert: {err}')
        except Exception as err:
            logger.critical(f'An exception was raised while processing a payload to insert: {err}')
