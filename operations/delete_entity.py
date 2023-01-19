import sys

sys.path.append("..")
from config import DEFAULT_TABLE
from logs import LOGGER
import os

def do_drop_entity(table_name, milvus_cli, mysql_cli, name_folder):
    if not table_name:
        table_name = DEFAULT_TABLE
    try:
        if not milvus_cli.has_collection(table_name):
            return f"Milvus doesn't have a collection named {table_name}"
        milvus_ids, path_images = mysql_cli.search_milvus_ids_by_name_folder(table_name, name_folder)
        if milvus_ids:
            status = milvus_cli.delete_entity(table_name, milvus_ids)
            mysql_cli.delete_entity(table_name, milvus_ids)
            for path_image in path_images:
                os.remove(path_image)
            os.rmdir("/".join(path_image.split("/")[:-1]))
            return status
    except Exception as e:
        LOGGER.error(f"Error with drop table: {e}")
        sys.exit(1)
