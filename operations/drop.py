import sys

sys.path.append("..")
from config import DEFAULT_TABLE
from logs import LOGGER
import shutil

def do_drop(table_name, milvus_cli, mysql_cli):
    if not table_name:
        table_name = DEFAULT_TABLE
    try:
        if not milvus_cli.has_collection(table_name):
            return f"Milvus doesn't have a collection named {table_name}"
        status = milvus_cli.delete_collection(table_name)
        images_path = mysql_cli.search_image_path_by_table_name(table_name)
        # print("images_path", images_path)
        shutil.rmtree("/".join(images_path[0].split("/")[:-2]))
        mysql_cli.delete_table(table_name)
        return status
    except Exception as e:
        LOGGER.error(f"Error with drop table: {e}")
        sys.exit(1)
