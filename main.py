import uvicorn
import os
from diskcache import Cache
from fastapi import FastAPI, File, UploadFile, Query
from fastapi.param_functions import Form
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import FileResponse
from encode import Resnet50
from milvus_helpers import MilvusHelper
from mysql_helpers import MySQLHelper
from config import TOP_K, UPLOAD_PATH
from operations.load import do_load
from operations.upload import do_upload
from operations.search import do_search
from operations.count import do_count
from operations.drop import do_drop
from operations.delete_entity import do_drop_entity

from logs import LOGGER
from pydantic import BaseModel
from typing import Optional
from urllib.request import urlretrieve
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from infer_ada import *
from typing import List
from threading import Thread
from operations.backup_restore import backup, restore
from operations.load import format_data

# from
app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

MODEL = Inference(
    check_point="weights/Retrain_101.ckpt", device="cuda")

MYSQL_CLI = MySQLHelper()
MILVUS_CLI = MilvusHelper()

# Mkdir '/tmp/search-images'
if not os.path.exists(UPLOAD_PATH):
    os.makedirs(UPLOAD_PATH)
    LOGGER.info(f"mkdir the path:{UPLOAD_PATH}")


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs={}, Verbose=None):
        Thread.__init__(self, group, target, name, args, kwargs)
        self._return = None

    def run(self):
        print(type(self._target))
        if self._target is not None:
            self._return = self._target(*self._args,
                                        **self._kwargs)

    def join(self, *args):
        Thread.join(self, *args)
        return self._return


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse({'detail': str(exc)}, status_code=400)


class Item(BaseModel):
    Table: Optional[str] = None
    Check_exists: bool = False
    File: str


@app.post('/img/load')
async def load_images(item: Item):
    # Insert all the image under the file path to Milvus/MySQL
    try:
        if item.Check_exists:
            list_check_image = MYSQL_CLI.search_image_path_by_table_name(
                item.Table)
        else:
            list_check_image = None
        total_num = do_load(item.Table, item.File, MODEL,
                            MILVUS_CLI, MYSQL_CLI, list_check_image)
        LOGGER.info(f"Successfully loaded data, total count: {total_num}")
        return "Successfully loaded data!"
    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400


def make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def upload_data(url, img_path, table_name):  # async
    # Insert the upload image to Milvus/MySQL
    try:

        name_folder = url.split("/")[-1]
        ids, img_path, name_folder, feat = do_upload(table_name, img_path, MODEL,
                                                     MILVUS_CLI, MYSQL_CLI, name_folder)
        return ids, img_path, name_folder, feat

    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': str(e)}


@app.post('/img/upload')
async def upload_images(images: List[UploadFile] = File(None), urls: List[str] = Query(...), table_name: str = None):
    list_thread = []
    list_image = []
    list_fail_detect = []
    list_ids = []
    list_img_path = []
    list_name_folder = []
    list_feat = []
    result = {'status': True, 'msg': ""}
    for image, url in zip(images, urls):
        split_path = [i for i in url.split("/") if len(i) > 0]
        for i in range(1, len(split_path)+1):
            make_dir("/" + "/".join(split_path[:i]))
        # Save the upload image to server.
        if image is not None and url is not None:
            content = await image.read()  # await
            print('read pic succ')
            img_path = os.path.join(url, image.filename)
            list_image.append(image.filename)
            with open(img_path, "wb+") as f:
                f.write(content)

        else:
            return {'status': False, 'msg': 'Image and url are required'}, 400

        thread = ThreadWithReturnValue(
            target=upload_data, args=(url, img_path, table_name))
        thread.start()
        list_thread.append(thread)

    for thread in list_thread:
        ids, img_path, name_folder, feat = thread.join()
        if ids:
            list_ids.append(ids[0])
            list_img_path.append(img_path)
            list_name_folder.append(name_folder)
            list_feat.append(feat[0])
        else:
            list_fail_detect.append(img_path.split("/")[-1])
    if list_ids:
        MYSQL_CLI.create_mysql_table(table_name)
        MYSQL_CLI.load_data_to_mysql(table_name, format_data(
            list_ids, list_img_path, list_name_folder, list_feat))

    if list_fail_detect:
        return {'status': False, 'msg': f'Can not detect face at image {list_fail_detect}. Please replace other image'}, 400

    if result["status"]:
        result["msg"] = "Successfully uploaded data"
        return result
    else:
        return result, 400


@app.post('/img/search_topk')
async def search_images(image: UploadFile = File(...), topk: int = Form(TOP_K), table_name: str = None):
    # Search the upload image in Milvus/MySQL
    try:
        # Save the upload image to server.
        content = await image.read()
        # print('read pic succ')
        img_path = os.path.join(UPLOAD_PATH, image.filename)
        # print("img_path", img_path)
        with open(img_path, "wb+") as f:
            f.write(content)
        name_folder, paths, distances = do_search(
            table_name, img_path, topk, MODEL, MILVUS_CLI, MYSQL_CLI)
        res = dict(zip(paths, distances))
        # print("---res", res)
        res = sorted(res.items(), key=lambda item: item[1], reverse=True)
        LOGGER.info("Successfully searched similar images!")
        return res
    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400


@app.post('/img/search')
async def search_images_real(image: UploadFile = File(...), topk: int = Form(TOP_K), table_name: str = None):
    # Search the upload image in Milvus/MySQL
    try:
        # Save the upload image to server.
        content = await image.read()
        # print('read pic succ')
        img_path = os.path.join(UPLOAD_PATH, image.filename)
        # print("img_path", img_path)
        with open(img_path, "wb+") as f:
            f.write(content)
        name_folder, paths, distances = do_search(
            table_name, img_path, topk, MODEL, MILVUS_CLI, MYSQL_CLI)
        res = dict(zip(paths, zip(name_folder, distances)))
        # print("--res", res)
        res = sorted(res.items(), key=lambda item: item[1][-1], reverse=True)
        # print("sort", res)
        if len(res) > 2:
            res = res[:3]
        list_name_folder = [values[-1][0] for values in res]
        num_init = 1
        value_init = res[0]
        for idx, name in enumerate(list_name_folder):
            num_ap = list_name_folder.count(name)
            if num_ap > num_init:
                value_init = res[idx]
                if idx == 0:
                    break

        LOGGER.info("Successfully searched similar images!")
        return {"name": value_init[-1][0], "cosine similarity": value_init[-1][1], "path": value_init[0]}
    except Exception as e:
        LOGGER.error(e)
        return {' ': False, 'msg': e}, 400


@app.post('/img/count')
async def count_images(table_name: str = None):
    # Returns the total number of images in the system
    try:
        num = do_count(table_name, MILVUS_CLI)
        LOGGER.info("Successfully count the number of images!")
        return num
    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400


@app.post('/img/drop')
async def drop_tables(table_name: str = None):
    # Delete the collection of Milvus and MySQL
    try:
        status = do_drop(table_name, MILVUS_CLI, MYSQL_CLI)
        LOGGER.info("Successfully drop tables in Milvus and MySQL!")
        return status
    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400


@app.post('/img/drop_entity')
async def drop_entity(table_name: str = None, folder_name: str = None):
    # Delete the collection of Milvus and MySQL
    try:
        status = do_drop_entity(table_name, MILVUS_CLI, MYSQL_CLI, folder_name)
        LOGGER.info("Successfully drop tables in Milvus and MySQL!")
        return status
    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400


@app.post('/img/get_name_table')
async def get_name_table():
    # Delete the collection of Milvus and MySQL
    try:
        return MYSQL_CLI.get_name_table()
    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400

# print("a")
if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=5001)
