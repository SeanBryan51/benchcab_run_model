import yaml
import subprocess
import string
import tempfile
import time
import os
import contextlib
import hpcpy
import hpcpy.exceptions

CONFIG_FILE_NAME = "config.yaml"
TEMPDIR_PREFIX = "benchcab_run_model_"


@contextlib.contextmanager
def working_dir(newdir):
    prevdir = os.getcwd()
    os.chdir(newdir)
    try:
        yield
    finally:
        os.chdir(prevdir)


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


def get_env(export=None, set=None):
    # TODO(Sean): add append_path, prepend_path, unset, remove_path
    env = dict()
    if export:
        if export == "all":
            env = os.environ.copy()
        else:
            env = {k: os.environ[k] for k in export}
    if set:
        env = {**env, **set}
    return env


def benchcab_run_model():

    with open(CONFIG_FILE_NAME) as file:
        config = yaml.safe_load(file)

    for model_config in config["model_configs"]:
        template_mapping = dict()

        model_config_root_path = tempfile.mkdtemp(prefix=TEMPDIR_PREFIX)
        template_mapping["MODEL_CONFIG_ROOT"] = model_config_root_path
        if "fetch_from" in model_config:
            fetch_repo(model_config["fetch_from"], model_config_root_path)

        run_script_path = interpolate_string(
            model_config["run_script"], template_mapping
        )
        env = dict()
        if "env" in model_config:
            env = get_env(**model_config["env"])
        try:
            client = hpcpy.get_client()
            client.submit(
                run_script_path,
                variables=env,
            )
        except hpcpy.exceptions.NoClientException:
            try:
                with working_dir(model_config_root_path):
                    subprocess.run(run_script_path, shell=True, check=True, env=env)
            except subprocess.CalledProcessError as exc:
                raise exc from None


if __name__ == "__main__":
    benchcab_run_model()
