docker build --platform linux/amd64 -t joshweir/sense2vec-rest:latest .
docker push joshweir/sense2vec-rest:latest

docker build --platform linux/amd64 -t 767398015747.dkr.ecr.us-east-1.amazonaws.com/s2v:latest .

docker push 767398015747.dkr.ecr.us-east-1.amazonaws.com/s2v:latest

docker build --platform linux/amd64 -t joshweir/sense2vec-rest:dev --build-arg CACHEBUST=$(date +%s) -f Dockerfile.dev .
docker push joshweir/sense2vec-rest:dev

# run server (aws image):
# docker run -it --rm -p "127.0.0.1:9188:80" 767398015747.dkr.ecr.us-east-1.amazonaws.com/s2v:latest

# run server: 
# docker run -it --rm -p "127.0.0.1:9188:80" -v $S2V_MODEL_PATH:/sense2vec-model joshweir/sense2vec-rest
# or dev:
# docker run -it --rm -p "127.0.0.1:9188:80" -v $S2V_MODEL_PATH_DEV:/sense2vec-model joshweir/sense2vec-rest:dev

# calling:
# curl -H "Content-Type:text/plain" --data-binary "[[\"plastic|NOUN\"]]" 'http://localhost:9188?min-scorez=0.76&nz=6&match-input-sensez=1&reduce-multi-wordformz=1&reduce-multicasez=1&min-word-len=2&reduce-compound-nouns=1'
