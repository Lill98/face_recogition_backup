import sys

sys.path.append("..")
from config import DEFAULT_TABLE
from logs import LOGGER
from operations.load import format_data

def do_upload(table_name, img_path, model, milvus_client, mysql_cli, name_folder):
    try:
        pass
        if not table_name:
            table_name = DEFAULT_TABLE
        # feat = model.resnet50_extract_feat(img_path)
        embedding_result, name_folders, img_list = model.infer([img_path])
        feat = embedding_result.cpu().detach().tolist()
        ids = milvus_client.insert_entity(table_name, feat)
        milvus_client.create_index(table_name)
        mysql_cli.create_mysql_table(table_name)
        mysql_cli.load_data_to_mysql(table_name, format_data(ids, [img_path], [name_folder], feat))
        return ids[0]
    except Exception as e:
        LOGGER.error(f"Error with upload : {e}")
        sys.exit(1)