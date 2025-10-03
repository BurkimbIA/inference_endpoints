# Speech Synthesis Service

This service will provide text-to-speech capabilities.

## Models (To be added)

- Coqui TTS models
- XTTS for voice cloning
- Custom Mooré TTS models
- Multi-speaker voice synthesis

## Building the Docker Image

```bash
cd speech/
docker build --build-arg HF_TOKEN=$HF_TOKEN -t burkimbia/speech-service .
```

## Running the Service

```bash
docker run -p 8000:8000 -e HF_TOKEN=$HF_TOKEN burkimbia/speech-service
```

## TODO

- [ ] Add TTS model integration
- [ ] Add support for Mooré language speech synthesis
- [ ] Implement voice cloning capabilities
- [ ] Add audio quality optimization
- [ ] Support multiple output formats (WAV, MP3, etc.)