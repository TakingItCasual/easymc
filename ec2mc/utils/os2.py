"""more specialized functions to interact with files and directories"""

import os
from pathlib import Path
from typing import Dict, List, Union
import shutil
import json
import jsonschema
from jsonschema.exceptions import ValidationError
from ruamel import yaml

from ec2mc import consts
from ec2mc.utils import halt

def dir_files(target_dir: Path, *, ext: str="") -> List[str]:
    """return names of files in directory"""
    return [f.name for f in target_dir.iterdir()
        if (target_dir / f).is_file() and str(f).endswith(ext)]


def recursive_dir_files(target_dir: Path) -> List[Path]:
    """return paths of files under target_dir, with prefix removed"""
    prefix_len = len(target_dir.parts)
    return [Path(*(Path(path) / f).parts[prefix_len:])
        for path, _, files in os.walk(target_dir)
        for f in files]


def dir_dirs(target_dir: Path) -> List[str]:
    """return names of directories in directory"""
    return [d.name for d in target_dir.iterdir() if (target_dir / d).is_dir()]


def get_json_schema(schema_name: str) -> Dict:
    """return schema from ec2mc.validate.jsonschemas as dictionary"""
    return parse_json(consts.DIST_DIR / "validate" /  # type: ignore
        "jsonschemas" / f"{schema_name}_schema.json")


def validate_dict(
    input_dict: Union[Dict, List], schema_dict: Dict, input_dict_src: str
) -> None:
    """validate dictionary using jsonschema schema dictionary"""
    try:
        jsonschema.validate(input_dict, schema_dict)
    except ValidationError as e:
        halt.err(f"{input_dict_src} incorrectly formatted:", e.message)


def parse_json(file_path: Path) -> Union[Dict, List]:
    """validate JSON file exists and contains valid JSON"""
    if not file_path.is_file():
        halt.err(f"{file_path} not found.")
    file_contents = file_path.read_text(encoding="utf-8")
    try:
        return json.loads(file_contents)
    except ValueError:
        halt.err(f"{file_path} is not a valid JSON file.")


def save_json(input_dict: Union[Dict, List], file_path: Path) -> None:
    """modify/create JSON file from dictionary"""
    with file_path.open("w", encoding="utf-8") as out_file:
        json.dump(input_dict, out_file, ensure_ascii=False, indent=4)
    file_path.chmod(consts.CONFIG_PERMS)


def parse_yaml(file_path: Path) -> Union[Dict, List]:
    """validate YAML file exists and contains valid YAML"""
    if not file_path.is_file():
        halt.err(f"{file_path} not found.")
    file_contents = file_path.read_text(encoding="utf-8")
    try:
        return yaml.safe_load(file_contents)
    except Exception:  # Multiple exceptions possible. Idk what they all are.
        halt.err(f"{file_path} is not a valid YAML file.")


def create_configuration_zip(
    user_name: str, new_key: Dict[str, str], give_ssh_key: bool
) -> None:
    """create zipped config folder containing new IAM user access key"""
    temp_dir = consts.CONFIG_DIR / ".ec2mc"
    if temp_dir.is_dir():
        shutil.rmtree(temp_dir, onerror=del_readonly)
    temp_dir.mkdir()

    new_config_dict = {
        'access_key': new_key,
        'region_whitelist': consts.REGIONS
    }
    shutil.copytree(consts.AWS_SETUP_DIR, temp_dir / "aws_setup")
    save_json(new_config_dict, temp_dir / "config.json")

    if give_ssh_key is True:
        if consts.RSA_KEY_PEM.is_file():
            pem_base = consts.RSA_KEY_PEM.name
            shutil.copy(consts.RSA_KEY_PEM, temp_dir / pem_base)
        if consts.RSA_KEY_PPK.is_file():
            ppk_base = consts.RSA_KEY_PPK.name
            shutil.copy(consts.RSA_KEY_PPK, temp_dir / ppk_base)

    out_zip = consts.CONFIG_DIR / f"{user_name}_config"
    shutil.make_archive(out_zip, "zip", consts.CONFIG_DIR, ".ec2mc")
    shutil.rmtree(temp_dir, onerror=del_readonly)


def del_readonly(action, name, exc):
    """handle deletion of readonly files for shutil.rmtree"""
    Path(name).chmod(0o777)
    action(name)
