from operations.load import do_load
from infer_ada import *
from milvus_helpers import MilvusHelper
from mysql_helpers import MySQLHelper
from operations.search import do_search
from operations.drop import do_drop
import argparse


def main(args):
    MILVUS_CLI = MilvusHelper()
    MYSQL_CLI = MySQLHelper()
    with open("wrong_file.txt","a") as f:
        f.write("\n------"+args.path_model+"\n")
    if args.drop:
        do_drop(args.table_name, MILVUS_CLI, MYSQL_CLI)
    MODEL = Inference(check_point=args.path_model)
    total_num = do_load(args.table_name, args.path_folder, MODEL, MILVUS_CLI, MYSQL_CLI)
    list_result = []
    for folder in os.listdir(args.path_folder):
        path_folder = os.path.join(args.path_folder, folder)
        FLAG = True
        for image in os.listdir(path_folder)[:args.number_image]:
            path_image = os.path.join(path_folder, image)
            try:
                name_folder, paths, distances = do_search(args.table_name, path_image, 10, MODEL, MILVUS_CLI, MYSQL_CLI)
            except:
                continue
            res = dict(zip(paths, zip(name_folder, distances)))
            res = sorted(res.items(), key=lambda item: item[1][-1], reverse=True)
            res = res[1:4]
            list_name_folder = [values[-1][0] for values in res]
            num_init = 1
            value_init = res[0]
            for idx, name in enumerate(list_name_folder):
                num_ap = list_name_folder.count(name)
                if num_ap > num_init:
                    value_init = res[idx]
                    if idx == 0:
                        break

            name_folder_pre = value_init[-1][0]
            if folder != name_folder_pre:
                FLAG = False
                # break
                with open("wrong_file.txt","a") as f:
                    f.write(path_image+"\n")
        if FLAG:
            list_result.append(1)
        else:
            list_result.append(0)

    accuracy = sum(list_result)/len(list_result)
    print("accuracy: ", accuracy)
    with open("wrong_file.txt","a") as f:
        f.write(f"\naccuracy: {accuracy}")
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Infer model PyTorch Siamese Example')
    parser.add_argument('--table_name', type=str,
                        help='name of table')
    parser.add_argument('--path_folder', type=str,
                        help='Directory of image')
    parser.add_argument('--path_model', type=str,
                        help='path to checkpoint')
    parser.add_argument('--number_image', type=int,
                        help='number check image')
    parser.add_argument('--drop', action='store_true',
                        help='path to checkpoint')  
                                          
    args = parser.parse_args()
    print(args)
    main(args)