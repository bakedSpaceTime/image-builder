#!/usr/bin/env python3
"""
Script to generate Dockerfile and cloudbuild.yaml templates for multiple models
using Jinja2 templating and optionally submit builds to Google Cloud.
"""

import os
import argparse
import subprocess
from jinja2 import Template

# Ollama environment variable definitions
# https://github.com/ollama/ollama/issues/2941
# Define the Jinja2 templates
DOCKERFILE_TEMPLATE = """FROM ollama/ollama
ENV HOME /root
WORKDIR /
ENV OLLAMA_KEEP_ALIVE -1
RUN ollama serve & sleep 10 && ollama pull {{ model }}
{% if additional_models %}{% for additional_model in additional_models %}
RUN ollama serve & sleep 10 && ollama pull {{ additional_model }}{% endfor %}{% endif %}
ENTRYPOINT ["ollama","serve"]
"""

CLOUDBUILD_TEMPLATE = """steps:
 # Build step
 - name: gcr.io/cloud-builders/docker
   args:
    - build
    - "-t"
    - gcr.io/$PROJECT_ID/ollama:{{ model_id }}
    - "-f"
    - Dockerfile-{{ model_id }}
    - .
# Push step
 - name: gcr.io/cloud-builders/docker
   args:
    - push
    - gcr.io/$PROJECT_ID/ollama:{{ model_id }}
# Image outputs
images:
 - gcr.io/$PROJECT_ID/ollama:{{ model_id }}
# Build options
options:
  machineType: E2_HIGHCPU_8
  diskSizeGb: 200  # Increased disk space otherwise the model built on cloud build exceeds default space
"""

BUILD_SCRIPT_TEMPLATE = """#!/bin/bash
set -x
pushd {{ build_dir }}
gcloud builds submit --config {{ model_id }}-cloudbuild.yaml
popd
"""


def get_model_id(model_name):
    """
    Create a clean model ID from model name
    This handles models with version tags like "gemma:2b"
    """
    # Replace colons and dots with hyphens, removing any special characters
    return "".join(
        c if c.isalnum() else "-"
        for c in model_name.replace(":", "-").replace(".", "-")
    )


def generate_files(models, build_dir, generate_build_script=True):
    """
    Generate Dockerfile and cloudbuild.yaml for each model
    """
    # Create build directory if it doesn't exist
    os.makedirs(build_dir, exist_ok=True)

    # Create Jinja2 templates
    dockerfile_template = Template(DOCKERFILE_TEMPLATE)
    cloudbuild_template = Template(CLOUDBUILD_TEMPLATE)
    build_script_template = Template(BUILD_SCRIPT_TEMPLATE)

    build_scripts = []

    for model in models:
        model_id = get_model_id(model)
        print(f"Generating files for model: {model} (ID: {model_id})")

        # Render Dockerfile template
        dockerfile_content = dockerfile_template.render(
            model=model, additional_models=[]
        )

        # Render cloudbuild.yaml template
        cloudbuild_content = cloudbuild_template.render(model_id=model_id)

        # Write the files
        with open(os.path.join(build_dir, f"Dockerfile-{model_id}"), "w") as f:
            f.write(dockerfile_content)

        with open(os.path.join(build_dir, f"{model_id}-cloudbuild.yaml"), "w") as f:
            f.write(cloudbuild_content)

        # Generate build script for this model
        if generate_build_script:
            build_script_content = build_script_template.render(
                build_dir=build_dir, model_id=model_id
            )

            build_script_path = os.path.join(build_dir, f"build-{model_id}.sh")
            with open(build_script_path, "w") as f:
                f.write(build_script_content)

            # Make the build script executable
            os.chmod(build_script_path, 0o755)
            build_scripts.append(build_script_path)

    # Create a master build script that calls all individual build scripts
    if generate_build_script and build_scripts:
        with open(os.path.join(build_dir, "build-all.sh"), "w") as f:
            f.write("#!/bin/bash\nset -e\n\n")
            for script in build_scripts:
                f.write(f"{script}\n")

        os.chmod(os.path.join(build_dir, "build-all.sh"), 0o755)


def submit_builds(models, build_dir):
    """
    Submit builds to Google Cloud
    """
    for model in models:
        model_id = get_model_id(model)
        cloudbuild_file = os.path.join(build_dir, f"{model_id}-cloudbuild.yaml")

        print(f"Submitting build for model: {model} (ID: {model_id})")
        try:
            subprocess.run(
                ["gcloud", "builds", "submit", "--config", cloudbuild_file, build_dir],
                check=True,
            )
            print(f"Build submitted successfully for {model}")
        except subprocess.CalledProcessError as e:
            print(f"Error submitting build for {model}: {e}")


def main(models_str=None, build_dir="./build", submit=False, no_build_scripts=False):
    """
    Run the main function with either command-line arguments or direct parameters.

    Args:
        models_str (str): Comma-separated list of model names
        build_dir (str, optional): Directory where build files will be created
        submit (bool, optional): Whether to submit builds to Google Cloud
        no_build_scripts (bool, optional): Whether to skip generating build scripts
    """
    # If no models_str is provided, parse command-line arguments
    if models_str is None:
        parser = argparse.ArgumentParser(
            description="Generate Dockerfile and cloudbuild.yaml templates for Ollama models"
        )
        parser.add_argument(
            "--models",
            type=str,
            required=True,
            help="Comma-separated list of model names",
        )
        parser.add_argument(
            "--build-dir",
            type=str,
            default="./build",
            help="Directory where build files will be created",
        )
        parser.add_argument(
            "--submit", action="store_true", help="Submit builds to Google Cloud"
        )
        parser.add_argument(
            "--no-build-scripts",
            action="store_true",
            help="Don't generate build scripts",
        )

        args = parser.parse_args()

        # Use command-line arguments
        models_str = args.models
        build_dir = args.build_dir
        submit = args.submit
        no_build_scripts = args.no_build_scripts

    # Parse models
    models = [model.strip() for model in models_str.split(",")]

    # Generate files
    generate_files(models, build_dir, not no_build_scripts)

    if submit:
        submit_builds(models, build_dir)
    else:
        print("\nFiles generated successfully. To submit builds, run:")
        print(f"  {os.path.join(build_dir, 'build-all.sh')}")
        print("Or specify --submit when running this script")


if __name__ == "__main__":
    # Use when taking arguments from command-line options
    # main()

    # Example of calling main() directly with argments
    options = {
        "models_str": "qwen3:32b",
        "build_dir": "./build",
        "submit": True,
        "no_build_scripts": False,
    }
    main(**options)
