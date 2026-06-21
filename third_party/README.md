# third_party

This directory holds external repositories and local model environments.

`third_party/fpanet/` is an ignored clone of `kuai-lab/nn24_FPANet`. Recreate it with:

```bash
uv run scripts/setup_fpanet_cuda.py clone
```

Do not commit third-party source trees, model checkpoints, datasets, or CUDA virtual environments into this repository.
