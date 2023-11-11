# ROBOT
## Installation in conda virtual env
```
conda create -n newenv python=3.7 
conda install -n newenv python-graphviz graphviz

cd {user-directory}/anaconda3/envs/newenv/Scripts/

pip install imgaug opencv-python opencv-contrib-python numpy requests tqdm PyYAML pandas seaborn playsound psutil pyserial sklearn

pip install torch==1.7.1+cpu torchvision==0.8.2+cpu torchaudio===0.7.2 -f https://download.pytorch.org/whl/torch_stable.html
```

Set virtual env in code https://code.visualstudio.com/docs/python/environments