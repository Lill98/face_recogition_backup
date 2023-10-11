from logs import LOGGER
from config import DEFAULT_TABLE
import sys
import time
import torch

sys.path.append("..")


def do_upload(table_name, img_path, model, milvus_client, mysql_cli, name_folder):
    try:
        if not table_name:
            table_name = DEFAULT_TABLE
        start_load = time.time()

        embedding_result, name_folders, img_list = model.infer([img_path])
        torch.cuda.synchronize()
        end_infer_time = time.time() - start_load
        LOGGER.info(f"infer time: {end_infer_time}")

        # print("embedding_result", embedding_result)
        if embedding_result is not None:
            feat = embedding_result.cpu().detach().tolist()
            ids = milvus_client.insert_entity(table_name, feat)
            end_insert_time = time.time() - start_load - end_infer_time
            LOGGER.info(f"insert time: {end_insert_time}")
            milvus_client.create_index(table_name)
            end_create_index_time = time.time() - start_load - \
                end_infer_time - end_insert_time
            LOGGER.info(f"create index time: {end_create_index_time}")
            return ids, img_path, name_folder, feat
        else:
            return None, img_path, name_folder, None

    except Exception as e:
        LOGGER.error(f"Error with upload : {e}")
        return None, img_path, name_folder, None
        sys.exit(1)
