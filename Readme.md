# FACE RECOGNITION

## 1. Requirements
- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
At the manager node run this command to open the port:
```
sudo ufw allow 22/tcp
sudo ufw allow 2376/tcp
sudo ufw allow 2377/tcp
sudo ufw allow 7946/tcp
sudo ufw allow 7946/udp
sudo ufw allow 4789/udp
sudo firewall-cmd --reload
```
At the woker node run this command to open the port:
```
sudo ufw allow 22/tcp

sudo ufw allow 2376/tcp

sudo ufw allow 7946/tcp

sudo ufw allow 7946/udp

sudo ufw allow 4789/udp

sudo firewall-cmd --reload
```

## 2. Set up
Clone code and put code at your directory. I call this is YOUR_DIRECTORY. Create new data directory. Structure as below:
```bash
YOUR_DIRECTORY
├── config
├── data
├── model
├── operations
├── pics
├── weights
├── .dockerignore
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── encode.py
├── infer.py
├── logs.py
├── main.py
├── requirements.txt
├── test_model.bash
├── test_model.py
├── milvus_helpers.py # Connect to Milvus server and insert/drop/query vectors in Milvus.
├── mysql_helpers.py # Connect to MySQL server, and add/delete/query IDs and object information.
```

- Use pretrain model:   
Download the [weight](https://drive.google.com/file/d/1ZUA02NPt_nElbFlsTpJofCTxgE1gdYhP/view?usp=sharing) and push it under weights folder  
Replace checkpoint path at [here](https://github.com/Lill98/face_recognition/blob/de10d6e72fd769b7972750405c22dd0047ea38d8/main.py#L41) to "weights/adaface_ir101_webface12m.ckpt"
- Use Retrain model:  
Download the [weight](https://drive.google.com/file/d/1BDBwt-ZNydUavfnFfNO9HQEXR6SC1kLP/view?usp=sharing) and push it under weights folder  
Replace checkpoint path at [here](https://github.com/Lill98/face_recognition/blob/de10d6e72fd769b7972750405c22dd0047ea38d8/main.py#L41) to "weights/Retrain_101.ckpt"


## 3. Deploy
### 3.1 pre-requisite
#### Install the share volume
Install gluster at all machine joined the swarm: 
For example we have ip manager node(docker-master) and ip woker node(docker-node1) is: IP1, IP2 respectively 
```
sudo apt-get update
sudo apt-get upgrade -y
sudo nano /etc/hosts
```
add the bellow line to the hosts file:  
```
IP1 docker-master
IP2 docker-node1
```
after that we will install gluster:
```
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:gluster/glusterfs-3.12
sudo apt-get update
sudo apt install glusterfs-server -y
sudo systemctl start glusterd
sudo systemctl enable glusterd
```
from the manager node run (this command run only on manager node):
```
gluster peer probe docker-node1;

```
create folder to save volume
```
sudo mkdir -p /gluster/volume1
sudo mkdir /fr_test
sudo chmod 777 /fr_test
sudo gluster volume create face_recognition replica 2 transport tcp IP1:/gluster/volume1 IP2:/gluster/volume2 force

```
from the manager node run (this command run only on manager node):
```
sudo gluster volume create face_recognition replica 2 transport tcp IP1:/gluster/volume1 IP2:/gluster/volume2 force
```

mount client folder to volume:
```
mount -t glusterfs localhost:face_recognition /fr_test
```

#### Install the nvidia docker swarm

please read [here](https://gist.github.com/coltonbh/374c415517dbeb4a6aa92f462b9eb287).

### 3.1. Deploy service


cd to milvus_compose folder and run:
```
docker-compose build
docker-compose push
docker-compose up -d
```
cd back to YOUR_DIRECTORY and run:
```
docker stack deploy --compose-file docker-compose.yml face_recognition
```
Open `IP1:5001/docs` or `IP2:5001/docs` in your browser to view all the APIs.

To close the container run:
```
docker stack rm face_recognition

```

cd to milvus_compose and run :
```
docker compose down -d
```
The API as below:

![fastapi](pics/api.png)

### 3.2. Deploy backup restore
Create environment with python 3.8  
Install package:  
```
pip install -r requirements_backup.txt
```
run the api:
```
python main_backup_restore.py
```

## 4. How to use service api

### 4.1 Load image to database 
- Put your image folder under **data directory**. For example name of folder is **company1** (you can put all staff_name_1 under data directory). Structure as bellow:

```bash
YOUR_DIRECTORY
├── config
├── data
    ├── company1
        ├── staff_name_1
                    ├── image1.jpg
                    ├── image2.jpg
                    ...
        ├── staff_name_2
        ...
...
```
Navigate to load api and work as below:
<!-- 
![fastapi](pics/API4.png)
Path to image folder in this example is **/data/company1** -->
Table: Name of table  
Check_exists: True if you wan to check pat, otherwise False
File: Path to folder 
![fastapi](pics/api5.png)

Wait until receive message as below:

![fastapi](pics/API6.png)

### 4.2 Searching
Navigate to search api and work as below:  
The name of table is the same as load image 
![fastapi](pics/API7.png)

Name: name of folder  
distance: minimum distance  
path: path to the same image
![fastapi](pics/API8.png)

### 4.3 Upload image
Navigate to upload api and work as below      
url: path to folder where you want to save upload image. you need to put a list here  
images: list of image respective to url  
Example: I want to upload image to staff_name_1 folder, path to folder in this example is **/data/company1/staff_name_1**  
The name of image doesn't included in folder
![fastapi](pics/API10.png)

Wait until receive message as below:
![fastapi](pics/API12.png)

### 4.4 Delete database (OPTIONAL)
- Run this if you want to delete database
Navigate to drop api and work as below:

![fastapi](pics/API2.png)

![fastapi](pics/API3.png)

### 4.5 Delete entity (OPTIONAL)
Navigate to drop_entity api and work as below  
table_name: Name of table include the entity   
folder_name: folder's name want to delete

![fastapi](pics/API11.png)

Wait until receive message as below:
![fastapi](pics/API13.png)

## 4. How to use backup api
Open `127.0.0.1:5002/docs` in your browser to view all the APIs.

- Navigate to backup_data to backup dataset
- Navigate to get_backup_data to get name version data in backup folder
- Navigate to restore_data to restore dataset.
  + name_version: Name of version that you want to backup  