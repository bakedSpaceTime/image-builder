# image-builder

For building images using GCP Cloud Build

Inspiration taken from [How to Save $17,000 a Month by Self-Hosting DeepSeek R1 on Google Cloud Run GPU][1] by Ve Sharma and [Run your AI inference applications on Cloud Run with NVIDIA GPUs][2] by Sagar Randive and Wenlei (Frank) He.

## Installation

```bash
git clone https://github.com/bakedSpaceTime/image-builder.git
cd image-builder

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Prerequisites

Setup the `gcloud` commandline tool for GCP
Instructions found here [Install the gcloud CLI][3]

## Usage

The `main` function defined in `main.py` can take the script paremeters either through CLI options or by writing the arguments directly in the Python file.

### CLI Arguments

Example

```bash
python -m main --models qwq --submit
```

```text
usage: main.py [-h] --models MODELS [--build-dir BUILD_DIR] [--submit] [--no-build-scripts]

Generate Dockerfile and cloudbuild.yaml templates for Ollama models

options:
  -h, --help               show this help message and exit
  --models MODELS          Comma-separated list of model names
  --build-dir BUILD_DIR    Directory where build files will be created
  --submit                 Submit builds to Google Cloud
  --no-build-scripts       Don't generate build scripts
```

### Arguments in Python

Advantage of this method is that all arguments can be predefined without requiring an additional script (Bash or PowerShell) file to define CLI options.

Modify the `main.py`

```python
if __name__ == "__main__":
    options = {
        "models_str": "qwen2.5-coder:32b,qwen2.5:32b",
        "build_dir": "./build",
        "submit": True,
        "no_build_scripts": False,
    }
    main(**options)
```

Run the build script

`python -m main`

[1]: https://medium.com/@vesharma.dev/how-to-save-17-000-a-month-by-self-hosting-deepseek-r1-on-google-cloud-run-gpu-6a186cc976b9
[2]: https://cloud.google.com/blog/products/application-development/run-your-ai-inference-applications-on-cloud-run-with-nvidia-gpus/
[3]: https://cloud.google.com/sdk/docs/install
