docker build -t joshweir/sense2vec-rest:latest .
docker push joshweir/sense2vec-rest:latest

docker build -t joshweir/sense2vec-rest:dev --build-arg CACHEBUST=$(date +%s) -f Dockerfile.dev .
docker push joshweir/sense2vec-rest:dev

# run server: 
# docker run -it --rm -p "127.0.0.1:9188:80" -v $S2V_MODEL_PATH:/sense2vec-model -v $GOOG_NGRAMS_PATH:/google-ngrams.pkl joshweir/sense2vec-rest
# or dev:
# docker run -it --rm -p "127.0.0.1:9188:80" -v $S2V_MODEL_PATH:/sense2vec-model -v $GOOG_NGRAMS_PATH:/google-ngrams.pkl joshweir/sense2vec-rest:dev

# calling:
# curl -H "Content-Type:text/plain" --data-binary "[[\"plastic|NOUN\"]]" 'http://localhost:9188?min-scorez=0.76&nz=6&match-input-sensez=1&reduce-multi-wordformz=1&reduce-multicasez=1&min-word-len=2&reduce-compound-nouns=1'
