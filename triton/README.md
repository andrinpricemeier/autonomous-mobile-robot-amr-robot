# Triton Inference Server

# How to install

1. Visit https://github.com/triton-inference-server/server/releases and download the trition server jetpack tgz file
2. Follow the instructions in the release notes to install the server. Note: Do not install numpy again because the Jetson Nano requires v16 which is installed when installing tensorflow (mentioned here: https://docs.nvidia.com/deeplearning/frameworks/install-tf-jetson-platform/index.html).
3. Copy over the models and plugins folder into the installed triton server
4. Start the server using start_server.sh

No config.pbtext is required because the triton server creates one on the fly by using the --strict-model-config=false flag.