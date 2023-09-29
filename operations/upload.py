from logs import LOGGER
from config import DEFAULT_TABLE
import sys

sys.path.append("..")


def do_upload(table_name, img_path, model, milvus_client, mysql_cli, name_folder):
    try:
        if not table_name:
            table_name = DEFAULT_TABLE
        embedding_result, name_folders, img_list = model.infer([img_path])
        # print("embedding_result", embedding_result)
        if embedding_result is not None:
            feat = embedding_result.cpu().detach().tolist()
            ids = milvus_client.insert_entity(table_name, feat)
            milvus_client.create_index(table_name)
            return ids, img_path, name_folder, feat
        else:
            return None, img_path, name_folder, None

    except Exception as e:
        LOGGER.error(f"Error with upload : {e}")
        return None, img_path, name_folder, None
        sys.exit(1)
