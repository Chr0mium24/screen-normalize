#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# ///

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


FPANET_URL = "https://github.com/kuai-lab/nn24_FPANet.git"
PYTORCH_CU113_INDEX = "https://download.pytorch.org/whl/cu113"


def project_root() -> Path:
    script_path = Path(__file__).resolve()
    for path in (script_path.parent, *script_path.parents):
        if (path / ".git").exists():
            return path
    return Path.cwd()


ROOT = project_root()
FPANET_DIR = ROOT / "third_party" / "fpanet"
VENV_DIR = ROOT / "third_party" / ".venvs" / "fpanet-cu113"
REQUIREMENTS = ROOT / "requirements" / "fpanet-cu113.txt"


def run(command: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=cwd, env=env, check=True)


def python_bin(venv_dir: Path) -> Path:
    if platform.system() == "Windows":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def default_cuda_home() -> Path:
    env_value = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
    if env_value:
        return Path(env_value)
    for candidate in (Path("/usr/local/cuda-11.3"), Path("/usr/local/cuda")):
        if candidate.exists():
            return candidate
    return Path("/usr/local/cuda")


def cuda_env(cuda_home: Path, arch_list: str) -> dict[str, str]:
    env = os.environ.copy()
    env["CUDA_HOME"] = str(cuda_home)
    env["CUDA_PATH"] = str(cuda_home)
    env["TORCH_CUDA_ARCH_LIST"] = arch_list
    env["PATH"] = f"{cuda_home / 'bin'}{os.pathsep}{env.get('PATH', '')}"
    ld_paths = [str(cuda_home / "lib64")]
    if env.get("LD_LIBRARY_PATH"):
        ld_paths.append(env["LD_LIBRARY_PATH"])
    env["LD_LIBRARY_PATH"] = os.pathsep.join(ld_paths)
    return env


def nvcc_path(cuda_home: Path) -> Path | None:
    found = shutil.which("nvcc")
    if found:
        return Path(found)
    candidate = cuda_home / "bin" / "nvcc"
    if candidate.exists():
        return candidate
    return None


def cuda_build_problems(cuda_home: Path) -> list[str]:
    problems: list[str] = []
    if platform.system() != "Linux":
        problems.append("FPANet/DCNv2 CUDA build is expected to run on Linux.")
    if nvcc_path(cuda_home) is None:
        problems.append("nvcc was not found; install the CUDA toolkit, not only the driver.")
    if shutil.which("nvidia-smi") is None:
        problems.append("nvidia-smi was not found; CUDA runtime/GPU access is not visible.")
    return problems


def check_environment(cuda_home: Path) -> None:
    print(f"project root: {ROOT}")
    print(f"FPANet dir:   {FPANET_DIR}")
    print(f"venv dir:     {VENV_DIR}")
    print(f"system:       {platform.system()} {platform.machine()}")
    print(f"CUDA_HOME:    {cuda_home}")
    print(f"nvidia-smi:   {shutil.which('nvidia-smi') or 'not found'}")
    print(f"nvcc:         {nvcc_path(cuda_home) or 'not found'}")

    py = python_bin(VENV_DIR)
    if py.exists():
        run(
            [
                str(py),
                "-c",
                "import torch; "
                "print('torch:', torch.__version__); "
                "print('torch cuda:', torch.version.cuda); "
                "print('cuda available:', torch.cuda.is_available()); "
                "print('device count:', torch.cuda.device_count())",
            ]
        )
    else:
        print("venv python:  not created")


def require_cuda_build_host(cuda_home: Path, force: bool) -> None:
    problems = cuda_build_problems(cuda_home)
    if problems and not force:
        for problem in problems:
            print(f"error: {problem}", file=sys.stderr)
        print("Use --force only if you know this host can still build/run CUDA.", file=sys.stderr)
        raise SystemExit(2)


def clone_fpanet() -> None:
    FPANET_DIR.parent.mkdir(parents=True, exist_ok=True)
    if (FPANET_DIR / "README.md").exists():
        print(f"FPANet already exists at {FPANET_DIR}")
        return
    run(["git", "clone", "--depth", "1", FPANET_URL, str(FPANET_DIR)])


def create_venv(python_version: str) -> None:
    VENV_DIR.parent.mkdir(parents=True, exist_ok=True)
    run(["uv", "venv", "--python", python_version, str(VENV_DIR)])


def install_dependencies() -> None:
    py = python_bin(VENV_DIR)
    if not py.exists():
        raise SystemExit(f"venv python not found: {py}")
    run(
        [
            "uv",
            "pip",
            "install",
            "--python",
            str(py),
            "--extra-index-url",
            PYTORCH_CU113_INDEX,
            "-r",
            str(REQUIREMENTS),
        ]
    )


def build_dcn(cuda_home: Path, arch_list: str) -> None:
    py = python_bin(VENV_DIR)
    dcn_dir = FPANET_DIR / "network" / "DCNv2"
    if not (dcn_dir / "setup.py").exists():
        raise SystemExit(f"DCNv2 setup.py not found: {dcn_dir}")

    env = cuda_env(cuda_home, arch_list)
    run([str(py), "setup.py", "build_ext", "--inplace"], cwd=dcn_dir, env=env)
    run(["uv", "pip", "install", "--python", str(py), "-e", str(dcn_dir)], env=env)


def rewrite_option_template(
    source: Path,
    destination: Path,
    dataset_root: Path,
    checkpoint: Path | None,
    num_gpu: int,
) -> None:
    text = source.read_text()
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith("num_gpu:"):
            lines.append(f"{indent}num_gpu: {num_gpu}")
        elif stripped.startswith("dataroot_gt:"):
            suffix = stripped.split(":", 1)[1].strip().replace("./datasets/", "")
            lines.append(f"{indent}dataroot_gt: {dataset_root / suffix}")
        elif stripped.startswith("dataroot_lq:"):
            suffix = stripped.split(":", 1)[1].strip().replace("./datasets/", "")
            lines.append(f"{indent}dataroot_lq: {dataset_root / suffix}")
        elif stripped.startswith("root:"):
            lines.append(f"{indent}root: {FPANET_DIR}")
        elif stripped.startswith("pretrain_network_g:"):
            value = str(checkpoint) if checkpoint else "~"
            lines.append(f"{indent}pretrain_network_g: {value}")
        else:
            lines.append(line)

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n")
    print(f"wrote {destination}")


def write_local_options(dataset_root: Path, checkpoint: Path | None, num_gpu: int) -> None:
    option_dir = FPANET_DIR / "option" / "local"
    templates = [
        FPANET_DIR / "option" / "test" / "test_tcl.yml",
        FPANET_DIR / "option" / "test" / "test_iphone.yml",
        FPANET_DIR / "option" / "train" / "train_tcl.yml",
        FPANET_DIR / "option" / "train" / "train_iphone.yml",
    ]
    for template in templates:
        rewrite_option_template(
            template,
            option_dir / template.name.replace(".yml", "_local.yml"),
            dataset_root.resolve(),
            checkpoint.resolve() if checkpoint else None,
            num_gpu,
        )


def smoke_test(cuda_home: Path, arch_list: str) -> None:
    py = python_bin(VENV_DIR)
    env = cuda_env(cuda_home, arch_list)
    code = f"""
import pathlib
import sys
import torch

repo = pathlib.Path({str(FPANET_DIR)!r})
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / 'network' / 'DCNv2'))

print('torch:', torch.__version__)
print('torch cuda:', torch.version.cuda)
print('cuda available:', torch.cuda.is_available())
assert torch.cuda.is_available(), 'CUDA is not available to PyTorch'

from network.FPANet import FPANet

net = FPANet(width=8, enc_blk_nums=[1, 1, 1], middle_blk_num=1, dec_blk_nums=[1, 1, 1]).cuda().eval()
x = torch.randn(1, 3, 64, 64, device='cuda')
with torch.no_grad():
    out = net([x, x, x])
print('smoke output:', [tuple(t.shape) for t in out])
"""
    run([str(py), "-c", code], cwd=FPANET_DIR, env=env)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare the external FPANet repository for CUDA training/evaluation."
    )
    parser.add_argument(
        "command",
        choices=("check", "clone", "write-options", "install", "build-dcn", "smoke", "all"),
        nargs="?",
        default="check",
    )
    parser.add_argument("--python", default="3.9", help="Python version for the FPANet uv venv.")
    parser.add_argument("--cuda-home", type=Path, default=default_cuda_home())
    parser.add_argument(
        "--cuda-arch-list",
        default="7.5;8.0;8.6;8.9",
        help="TORCH_CUDA_ARCH_LIST used while compiling DCNv2.",
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=FPANET_DIR / "datasets",
        help="VDMoire dataset root used in generated local option files.",
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=None,
        help="Optional FPANet checkpoint path for generated test option files.",
    )
    parser.add_argument("--num-gpu", type=int, default=1)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass Linux/nvcc/nvidia-smi guardrails for install/build commands.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.command in {"check", "all"}:
        check_environment(args.cuda_home)

    if args.command in {"clone", "write-options", "install", "build-dcn", "smoke", "all"}:
        clone_fpanet()

    if args.command in {"write-options", "all"}:
        write_local_options(args.dataset_root, args.checkpoint, args.num_gpu)

    if args.command in {"install", "build-dcn", "smoke"}:
        require_cuda_build_host(args.cuda_home, args.force)

    if args.command == "all":
        problems = cuda_build_problems(args.cuda_home)
        if problems and not args.force:
            for problem in problems:
                print(f"warning: {problem}")
            print("CUDA install/build skipped on this host after cloning and writing options.")
            return

    if args.command in {"install", "all"}:
        create_venv(args.python)
        install_dependencies()

    if args.command in {"build-dcn", "all"}:
        build_dcn(args.cuda_home, args.cuda_arch_list)

    if args.command in {"smoke", "all"}:
        smoke_test(args.cuda_home, args.cuda_arch_list)


if __name__ == "__main__":
    main()
