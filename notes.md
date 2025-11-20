


Set up environment (windows)
```python -m venv .venv```

Activate Environment using 
```./.venv/Scripts/Activate.ps1```

Upgrade pip
```python -m pip install --upgrade pip ```

Install predefined packages
```python -m pip install -r requirements.txt```

Initialize ngrok (public host)
```./scripts_offline/misc/ngrok.exe http https://agent.dev.bridgeo.ai --domain cheetah-well-serval.ngrok-free.app```

Intialize API application
```python -m uvicorn run:app --host 0.0.0.0 --port 8501 --reload```

"c:/Users/krenova/OneDrive - Krenova/eh_codes/whatsapp_agent/webhook_test.py"

streamlit run main.py   

wsl -d

sudo docker ps   


python 

# Install postgresql

https://www.docker.com/blog/how-to-use-the-postgres-docker-official-image/



sudo apt install docker-compose-plugin
docker compose version
sudo docker compose up -d #d for detached

# Pull latest PostgreSQL image
docker pull postgres:15

# Running PostgreSQL container (standalone)
```
docker run -d \
  --name postgres-db \
  -e POSTGRES_USER=${POSTGRES_USER} \
  -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
  -e POSTGRES_DB=${POSTGRES_DB} \
  -p ${POSTGRES_PORT}:5432 \
  -v postgres_data:/var/lib/postgresql/data \
  postgres:17
```




## Primary docker commands
Start docker daemon
```sudo service docker start```

Check if container is running
```docker ps```

Stop container (when needed)
```docker stop postgres-db```

List all containers, including stopped
```docker ps -a```

Remove container (when needed)
```docker rm <container name or id>```

Delete unwanted docker image
```docker rmi <image_id_or_tag>```

Force delete unwanted docker image - even with existing stopped container
```docker rmi -f <image_id_or_tag>```

Remove docker volume
```docker volume rm <volume-name>```

Force remove docker volume
```docker volume rm -f <volume-name>```

Build Dockerfile image
```sudo docker build --no-cache -t <assign image name> .```

Build image
```docker compose build```

Build image without cache
```docker compose build --no-cache```

start container in detached mode
```docker compose up -d```

Build and start container in detached mode
```docker compose up --build -d```


## Cleaning up
Stop and remove container.
```sudo docker compose down```

Stop, remove container and volume
```sudo docker compose down -v```

Remove unused data, including build cache, stopped containers, networks, and dangling images. (WARNING: deletes everything)
```sudo docker system prune -a --volumes```

Remove the build cache without affecting your images
```sudo docker builder prune```

Remove unused containers, networks, and dangling images, but keep existing images and volumes.
```sudo docker system prune```


## Troubleshooting and Debugging
Note that if you are mapping the container's directory to host, and container is has `read/write activities` on the host, take note to ensure the following permissions are given.
```
sudo chown -R 999:999 .dbData/postgresql
sudo chmod -R 700 .dbData/postgresql
```

Inspect logs of container
```docker logs <container_name_or_id>```

Enter bash of container
```sudo docker exec -it <container_name/id> /bin/bash```

Enter bash of container as root
```sudo docker exec -u 0 -it whatsapp_pg /bin/bash```


# Postgresql
```psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}```