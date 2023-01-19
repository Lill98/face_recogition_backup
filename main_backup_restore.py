import uvicorn
import os
from fastapi import FastAPI
from operations.backup_restore import backup, restore, get_newest_database
from logs import LOGGER
from starlette.middleware.cors import CORSMiddleware
from typing import List
from fastapi import FastAPI, File, UploadFile, Query
from pydantic import BaseModel
from typing import Optional
import requests

app = FastAPI()
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

class Item(BaseModel):
    Table: Optional[str] = None
    File: str

@app.post('/img/backup_data')
async def backup_data():
    try:
        os.system("docker-compose -p face_recognition down")
        backup()
        os.system("docker-compose -p face_recognition up -d")
        return "Successfully loaded data!"

    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400

@app.get('/img/get_backup_data')
async def get_backup_data():
    try:
        list_file = os.listdir("backup")
        return list_file
    except Exception as e:
        LOGGER.error(e)
        return {'status': False, 'msg': e}, 400

@app.post('/img/restore_data')
async def restore_data(name_version: str = None):
    # Delete the collection of Milvus and MySQL
    try:
        os.system("docker-compose -p face_recognition down")
        restore(name_backup=name_version)
        os.system("docker-compose -p face_recognition up -d")

        return "Successfully loaded data!"
    except:
        try:
            os.system("docker-compose -p face_recognition down")
            name_version = get_newest_database()
            restore(name_backup=name_version)
            os.system("docker-compose -p face_recognition up -d")

        except Exception as e:
            LOGGER.error(e)
            return {'status': False, 'msg': e}, 400

# @app.post('/img/upload_dataset')
# async def upload_dataset(item: Item):
#     # print("----")
#     # Insert all the image under the file path to Milvus/MySQL
#     url = 'http://192.168.192.243:5001/img/get_path_image'
#     params = {"table_name":"test1"}
    
#     response = requests.post(url, params=params)
#     all_path = response.text


# print("a")
if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=5002)
