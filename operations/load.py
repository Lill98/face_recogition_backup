from logs import LOGGER
from config import DEFAULT_TABLE
import sys
import os
from diskcache import Cache
import torch

sys.path.append("..")


# Get the path to the image
def get_imgs(path_root, list_image_check=None):
    pics = []
    name_folder = []
    print("list_image_check", list_image_check)
    list_paths = list(os.walk(path_root))
    for paths in list_paths:
        if not paths[1]:
            # print("paths", paths)
            folder = paths[0].split("/")[-1]
            path_folder = paths[0]
            for f in os.listdir(path_folder):
                if ((f.endswith(extension) for extension in
                        ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG', ".bmp"]) and not f.startswith('.DS_Store')):
                    print("os.path.join(path_folder, f)",
                          os.path.join(path_folder, f))
                    if list_image_check:
                        if os.path.join(path_folder, f) in list_image_check:
                            # print("--------path exists", os.path.join(path_folder, f))
                            continue
                    pics.append(os.path.join(path_folder, f))
                    name_folder.append(folder)
    # print("pics", pics)
    return pics, name_folder


# Get the vector of images
def extract_features(img_dir, model, list_check_image=None):
    try:
        cache = Cache('./tmp')
        feats = []
        path_images = []
        list_folder_names = []
        # if os.path.isdir(img_dir):
        img_list, name_folders = get_imgs(img_dir, list_check_image)
        # elif type(img_dir) is list:

        # total = len(img_list)
        # cache['total'] = total
        # print("img_list", img_list)
        if len(img_list):
            embedding_result, name_folders, img_list = model.infer(img_list)
            # resut_distance = torch.cdist(embedding_result.cpu(), embedding_result.cpu(), 2)
            # print("resut_distance", resut_distance)

            # print("embedding_result.cpu()", embedding_result.cpu().size())
            feats = (1*embedding_result.cpu()).detach().tolist()

            # print("img_path--", img_list)
            # names.append(img_path.encode() for img_path in img_list)
            # print("img_path--encode", names)

            for img_path, name_folder in zip(img_list, name_folders):
                path_images.append(img_path.encode())
                list_folder_names.append(name_folder.encode())
                # try:
                #     # norm_feat = model.resnet50_extract_feat(img_path)
                #     norm_feat = model.resnet50_extract_feat(img_path)
                #     print("norm_feat", type(norm_feat))
                #     feats.append(norm_feat)
                #     names.append(img_path.encode())
                #     cache['current'] = i + 1
                #     print(f"Extracting feature from image No. {i + 1} , {total} images in total")
                # except Exception as e:
                #     LOGGER.error(f"Error with extracting feature from image {e}")
                #     continue
            return feats, path_images, list_folder_names
        else:
            return None, None, None

    except Exception as e:
        LOGGER.error(f"Error with extracting feature from image {e}")
        sys.exit(1)

# Get the vector of images
# def extract_features(img_dir, model):
#     try:
#         cache = Cache('./tmp')
#         feats = []
#         names = []
#         img_list = get_imgs(img_dir)
#         total = len(img_list)
#         cache['total'] = total
#         for i, img_path in enumerate(img_list):
#             try:
#                 # norm_feat = model.resnet50_extract_feat(img_path)
#                 norm_feat = model.resnet50_extract_feat(img_path)
#                 print("norm_feat", type(norm_feat))
#                 feats.append(norm_feat)
#                 names.append(img_path.encode())
#                 cache['current'] = i + 1
#                 print(f"Extracting feature from image No. {i + 1} , {total} images in total")
#             except Exception as e:
#                 LOGGER.error(f"Error with extracting feature from image {e}")
#                 continue
#         return feats, names
#     except Exception as e:
#         LOGGER.error(f"Error with extracting feature from image {e}")
#         sys.exit(1)


# Combine the id of the vector and the name of the image into a list
def format_data(ids, names, list_folder_names, vectors):
    data = []
    for i in range(len(ids)):
        value = (str(ids[i]), names[i], list_folder_names[i], str(vectors[i]))
        data.append(value)
    return data


# Import vectors to Milvus and data to Mysql respectively
def do_load(table_name, image_dir, model, milvus_client, mysql_cli, list_check_image=None):
    # print("loading image-----------------")
    if not table_name:
        table_name = DEFAULT_TABLE
    vectors, path_images, list_folder_names = extract_features(
        image_dir, model, list_check_image)
    # print("vectors",vectors)
    # vectors = -1*vectors
    # print("------------extract feature done")
    # print(len(vectors))
    # status = milvus_client.delete_collection(table_name)
    # mysql_cli.delete_table(table_name)
    if vectors:
        ids = milvus_client.insert(table_name, vectors)
        # print("done insert")
        milvus_client.create_index(table_name)
        # print("done index")
        mysql_cli.create_mysql_table(table_name)
        # print("done create_mysql_table")
        mysql_cli.load_data_to_mysql(table_name, format_data(
            ids, path_images, list_folder_names, vectors))
        len_ids = len(ids)
        # print("done load_data_to_mysql")
    else:
        len_ids = 0

    return len_ids

# # Import vectors to Milvus and data to Mysql respectively
# def do_load_check_exists(table_name, image_dir, model, milvus_client, mysql_cli):
#     # print("loading image-----------------")
#     if not table_name:
#         table_name = DEFAULT_TABLE
#     vectors, path_images, list_folder_names = extract_features(image_dir, model)
#     # print("vectors",vectors)
#     # vectors = -1*vectors
#     # print("------------extract feature done")
#     # print(len(vectors))
#     # status = milvus_client.delete_collection(table_name)
#     # mysql_cli.delete_table(table_name)
#     ids = milvus_client.insert(table_name, vectors)
#     # print("done insert")
#     milvus_client.create_index(table_name)
#     # print("done index")
#     mysql_cli.create_mysql_table(table_name)
#     # print("done create_mysql_table")
#     mysql_cli.load_data_to_mysql(table_name, format_data(ids, path_images, list_folder_names, vectors))
#     # print("done load_data_to_mysql")

#     return len(ids)
