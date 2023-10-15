import shutil
from logs import LOGGER
from config import DEFAULT_TABLE
import sys
import os
sys.path.append("..")


def do_drop(table_name, milvus_cli, mysql_cli):
    if not table_name:
        table_name = DEFAULT_TABLE
    try:
        images_path = mysql_cli.search_image_path_by_table_name(table_name)

        mysql_cli.delete_table(table_name)

        print("images_path", images_path)
        if len(images_path):
            path_root_folder = "/".join(images_path[0].split("/")[:-2])
            if os.path.exists(path_root_folder):
                shutil.rmtree(path_root_folder)

        if not milvus_cli.has_collection(table_name):
            return f"Milvus doesn't have a collection named {table_name}"
        status = milvus_cli.delete_collection(table_name)

        return status
    except Exception as e:
        LOGGER.error(f"Error with drop table: {e}")
        sys.exit(1)
