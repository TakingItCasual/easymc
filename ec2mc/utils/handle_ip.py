import os.path
import importlib.util

from ec2mc import consts

# TODO: Offer JSON validation for handler JSON files.
def main(handler_script, aws_region, instance_name, instance_id, new_ip):
    """pass along instance info to handler under config's ip_handlers"""
    if consts.USE_HANDLER is False:
        return

    handler_path = f"{consts.IP_HANDLER_DIR}{handler_script}"
    if os.path.isfile(handler_path):
        handler = load_script(handler_path)
        handler.main(aws_region, instance_name, instance_id, new_ip)
    else:
        print(f"  {handler_script} not found from config's ip_handlers.")


def load_script(script_path):
    """load python script"""
    spec = importlib.util.spec_from_file_location("handler", script_path)
    handler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(handler)
    return handler
