docker build -t joshweir/sense2vec-rest:latest .
docker push joshweir/sense2vec-rest:latest

docker build -t joshweir/sense2vec-rest:dev --build-arg CACHEBUST=$(date +%s) -f Dockerfile.dev .
docker push joshweir/sense2vec-rest:dev

# run server: 
# docker run -it --rm -p "127.0.0.1:9188:80" joshweir/sense2vec-rest
# or dev:
# docker run -it --rm -p "127.0.0.1:9188:80" joshweir/sense2vec-rest:dev

# calling:
# curl -H "Content-Type:text/plain" --data-binary "Penguins are birds, they are great." 'http://localhost:8080' | jq
