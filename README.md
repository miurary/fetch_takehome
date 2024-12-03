To get this code running:
1. `docker build -t <tag> .` in the directory with the Dockerfile to build the image
2. `docker images` to get the image id
3. `docker run -p 5000:5000 <image id>` to spin up the container
4. Access at 127.0.0.1:5000, send requests to 127.0.0.1:5000/receipts/process

Hope it all works, thanks for the opportunity!
