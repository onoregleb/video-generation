This tutorial primarily introduces how to use Gradio to set up a simple web server.

## Running Guide

### Installation Guide for Linux

```shell
# Begin by cloning the repository:
git clone https://github.com/SkyworkAI/SkyReels-V1

# We recommend Python 3.10 and CUDA version 12.2 for the manual installation.
# Install the relevant Python dependency packages.
pip install -r requirements.txt
pip install gradio

```

### Starting the Web Server

```shell
# task_type:The task type is designated to support both t2v and i2v. For the execution of an i2v task, please set 'i2v'.
# gpu_num: Number of GPUs used, If using multi-GPU parallel inference, set `gpu_num` to the number of GPUs you are running.
cd scripts && python3 gradio_web.py --task_type t2v --gpu_num 1
```