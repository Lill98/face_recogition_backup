import sys

sys.path.append("..")
from config import DEFAULT_TABLE
from logs import LOGGER


def do_search(table_name, img_path, top_k, model, milvus_client, mysql_cli):
    try:
        # print("do search--------------------")
        if not table_name:
            table_name = DEFAULT_TABLE
        # feat = model.resnet50_extract_feat(img_path)
        embedding_result, name_folders, img_list = model.infer([img_path])
        if embedding_result is not None:
            feat = embedding_result.cpu().detach().tolist()[0]
            # print("feat:", feat)

            # search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
            vectors = milvus_client.search_vectors(table_name, [feat], top_k)
            print("vectors", vectors)
            # vectors=milvus_client.search([feat],  
            #     param=search_params, 
            #     anns_field="embedding",
            #     limit=top_k, 
            #     expr=None,
            #     consistency_level="Strong")
            vids = [str(x.id) for x in vectors[0]]
            paths, name_folder = mysql_cli.search_by_milvus_ids(vids, table_name)
            distances = [x.distance for x in vectors[0]]
        else:
            name_folder, paths, distances = None, None, None
        # print(":paths", paths)
        return name_folder, paths, distances
    except Exception as e:
        LOGGER.error(f"Error with search : {e}")
        sys.exit(1)
