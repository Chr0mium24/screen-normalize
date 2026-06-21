# FPANet CUDA 部署记录

FPANet 用于本项目第二阶段的视频去摩尔纹实验。它和当前第一阶段的屏幕几何归一化是两个独立模块：

```text
拍屏幕视频 -> 透视矫正和裁切 -> FPANet 视频去摩尔纹 -> 正常屏幕视频
```

## 当前本机状态

当前工作机是 macOS ARM，未检测到 `nvidia-smi` 和 `nvcc`。因此这里可以准备代码和配置，但不能真正编译 DCNv2，也不能跑 CUDA 推理或训练。

真正运行 FPANet 需要 NVIDIA GPU 的 Linux 环境，并且要有 CUDA toolkit。只装显卡驱动不够，因为 DCNv2 需要用 `nvcc` 编译 CUDA 扩展。

## 代码位置

FPANet 官方仓库放在：

```text
third_party/fpanet/
```

这是第三方源码目录，已加入 `.gitignore`，不直接提交到本项目。需要重新拉取时运行：

```bash
uv run scripts/setup_fpanet_cuda.py clone
```

## CUDA 环境

官方环境接近：

- Python 3.7
- PyTorch 1.11
- CUDA 11.3
- DCNv2

为了用 `uv` 管理环境，本项目提供了：

```text
requirements/fpanet-cu113.txt
scripts/setup_fpanet_cuda.py
```

在 CUDA Linux 机器上执行：

```bash
uv run scripts/setup_fpanet_cuda.py all
```

这会做四件事：

1. 拉取 `kuai-lab/nn24_FPANet` 到 `third_party/fpanet/`。
2. 生成本地 option 文件到 `third_party/fpanet/option/local/`。
3. 创建 `third_party/.venvs/fpanet-cu113/`。
4. 安装 PyTorch CUDA 11.3 依赖并编译 DCNv2。

如果 CUDA 不在默认路径，显式传入：

```bash
uv run scripts/setup_fpanet_cuda.py all --cuda-home /usr/local/cuda-11.3
```

如果显卡架构需要调整：

```bash
uv run scripts/setup_fpanet_cuda.py all --cuda-arch-list "8.6"
```

## 检查环境

```bash
uv run scripts/setup_fpanet_cuda.py check
```

成功的 CUDA 机器上应该能看到：

- `nvidia-smi` 存在；
- `nvcc` 存在；
- `torch.cuda.is_available()` 为 `True`；
- `torch.version.cuda` 接近 `11.3`。

## 数据集

FPANet 使用 VDMoire 数据集。默认目录是：

```text
third_party/fpanet/datasets/
```

期望结构：

```text
third_party/fpanet/datasets/
├── tcl/
│   ├── train/source/
│   ├── train/target/
│   ├── test/source/
│   └── test/target/
└── iphone/
    ├── train/source/
    ├── train/target/
    ├── test/source/
    └── test/target/
```

生成本地配置：

```bash
uv run scripts/setup_fpanet_cuda.py write-options
```

如果数据集在别的位置：

```bash
uv run scripts/setup_fpanet_cuda.py write-options --dataset-root /data/VDMoire
```

## 权重

当前未在官方 FPANet 仓库中看到明确发布的预训练 checkpoint。若后续拿到 checkpoint，可以生成带权重路径的本地测试配置：

```bash
uv run scripts/setup_fpanet_cuda.py write-options --checkpoint /path/to/fpanet.pth
```

如果没有 checkpoint，就需要先训练：

```bash
cd third_party/fpanet
../.venvs/fpanet-cu113/bin/python -m torch.distributed.launch \
  --nproc_per_node=1 \
  --master_port=4321 \
  ./train.py \
  -opt option/local/train_tcl_local.yml
```

## 测试

编译完成后先跑 smoke test：

```bash
uv run scripts/setup_fpanet_cuda.py smoke
```

再跑官方测试入口：

```bash
cd third_party/fpanet
../.venvs/fpanet-cu113/bin/python -m torch.distributed.launch \
  --nproc_per_node=1 \
  --master_port=4321 \
  ./test.py \
  -opt option/local/test_tcl_local.yml
```

测试结果会写到 FPANet 自己的 `results/` 目录。本项目最终需要把可复现实验结果整理回 `runs/`。

## 风险点

- DCNv2 使用旧 PyTorch/THC 接口，不建议直接升级到 PyTorch 2.x。
- macOS/Apple Silicon 不能跑这个 CUDA 版本。
- FPANet 是视频去摩尔纹模型，适合作为第二阶段主候选，但没有官方 checkpoint 时需要训练成本。
- 后续还需要把第一阶段输出的视频切帧，整理成 FPANet 可读取的连续帧输入。
