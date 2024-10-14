import yaml
import hpcpy
import subprocess
import string
import tempfile
import time

CONFIG_FILE_NAME = "config.yaml"
TEMPDIR_PREFIX = "benchcab_run_model_"


def interpolate_string(input, mapping):
    return string.Template(input).substitute(mapping)


def fetch_repo(spec, dest):
    if "git" in spec:
        url = spec["git"]["url"]
        subprocess.run(f"git clone {url} {dest}", shell=True, check=True)
        ref = spec["git"].get("ref")
        if ref:
            time.sleep(0.01)
            subprocess.run(f"cd {dest} && git checkout {ref}", shell=True, check=True)


def benchcab_run_model():

    with open(CONFIG_FILE_NAME) as file:
        config = yaml.safe_load(file)

    for model_config in config["model_configs"]:
        template_mapping = dict()

        model_config_root_path = tempfile.mkdtemp(prefix=TEMPDIR_PREFIX)
        template_mapping["MODEL_CONFIG_ROOT"] = model_config_root_path
        if "fetch_from" in model_config:
            fetch_repo(model_config["fetch_from"], model_config_root_path)

        if "run_script" in model_config:
            run_script_path = interpolate_string(
                model_config["run_script"], template_mapping
            )
            client = hpcpy.PBSClient()
            # TODO(hpcpy): what is the behaviour when hpcpy cannot infer the scheduler
            # on the current machine? In that case, try exectute the run script
            # directly.
            if "env" in model_config:
                # TODO: specify environment variables via hpcpy
                pass
            client.submit(run_script_path)


if __name__ == "__main__":
    benchcab_run_model()
