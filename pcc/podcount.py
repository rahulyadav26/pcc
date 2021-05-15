import os
import json
import time
import argparse
import subprocess

KUBECTL_GET_STACK_INFO = "kubectl get deploy %s -n %s  -o json"

KUBECTL_GET_STACK = "kubectl get pods -n %s  -o json"

NO_PODS_AVAILABLE_MESSAGE = "No Pods Available for stack %s"

NO_PODS_AVAILABLE_TITLE = "No Pods Available"

PODS_UNAVAILABLE_MESSAGE = "%s Pods Down out of %s for stack %s"

PODS_UNAVAILABLE_TITLE = "%s Pods Down"

OSASCRIPT_SEND_NOTIFICATION = """osascript -e 'display notification "{}" with title "{}"'"""

ALL_PODS_UP_TITLE = "All Pods are Up"

ALL_PODS_UP_MESSAGE = "All Pods are Up for stack %s"


def send_notification(title, message):
    cmd = OSASCRIPT_SEND_NOTIFICATION.format(message, title)
    os.system(cmd)


def check_unavailable_pods(item, stack_with_pods_down):
    stack_name = item['metadata']['annotations']['meta.helm.sh/release-name']

    if 'unavailableReplicas' in item['status']:

        if 'availableReplicas' in item['status']:

            title = PODS_UNAVAILABLE_TITLE % item['status']['unavailableReplicas']
            message = PODS_UNAVAILABLE_MESSAGE % (item['status']['unavailableReplicas'], item['status']['replicas'], stack_name)

        else:

            title = NO_PODS_AVAILABLE_TITLE
            message = NO_PODS_AVAILABLE_MESSAGE % stack_name

        send_notification(title, message)
        return stack_name

    else:

        if stack_name in stack_with_pods_down:
            title = ALL_PODS_UP_TITLE
            message = ALL_PODS_UP_MESSAGE % stack_name
            send_notification(title, message)

            stack_with_pods_down.remove(stack_name)

        return None


def init_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stack", "-s", help="specify the stack name", default="")
    parser.add_argument("--namespace", "-n", help="specify the namespace", required=True)
    parser.add_argument("--trigger", "-t", help="specify the notification trigger timeout(in seconds)", default=30)
    return parser.parse_args()


def main():
    args = init_arg_parser()
    stack_with_pods_down = list()
    while True:
        if args.stack == "":
            output = json.loads(subprocess.check_output(["kubectl", "get", "deployments", "-n", args.namespace, "-o", "json"]))
            for item in output['items']:
                stack_name = check_unavailable_pods(item, stack_with_pods_down)
                if stack_name:
                    stack_with_pods_down.append(stack_name)

        else:
            output = json.loads(subprocess.check_output(["kubectl", "get", "deploy", args.stack, "-n", args.namespace, "-o", "json"]))
            stack_name = check_unavailable_pods(output, stack_with_pods_down)
            if stack_name:
                stack_with_pods_down.append(stack_name)
                
        time.sleep(int(args.trigger))


if __name__ == '__main__':
    main()
