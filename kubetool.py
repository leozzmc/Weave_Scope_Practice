"""
Pre-requision:
⚠ pip3 install kubernetes
"""
from operator import ge
from re import A
from kubernetes import  client,config
from kubernetes.stream import stream
import yaml

# Load Config Files
config_file = r"~/.kube/config"
config.kube_config.load_kube_config(config_file=config_file)
Api_Instance = client.CoreV1Api()
Api_Batch = client.BatchV1Api()

class KubeTool:
    def __init__(self):
        pass
    
    # List All Nodes
    def list_node(self):
        api_response = Api_Instance.list_node()
        data = {}
        for i in api_response.items:
            data[i.metadata.name] = {
            "name": i.metadata.name,
            "status": i.status.conditions[-1].type if i.status.conditions[-1].status == "True" else "NotReady",
            "ip": i.status.addresses[0].address,
            "kubelet_version": i.status.node_info.kubelet_version,
            "os_image": i.status.node_info.os_image,
            }
        return data

    # List All Namespaces
    def get_namespace_list(self):
        namespace_list = []
        for ns in Api_Instance.list_namespace().items:
            # print(ns.metadata.name)
            namespace_list.append(ns.metadata.name)
        return namespace_list

    # List All pods
    def get_pods(self):
        pod_list = []
        for i in Api_Instance.list_pod_for_all_namespaces().items:
            #print(f"[{i.status.pod_ip}] [{i.metadata.namespace}]: {i.metadata.name}")
            pod_list.append(i.metadata.name)
        return pod_list

    # List All Services
    def get_services(self):
        service_list=[]
        for i in Api_Instance.list_service_for_all_namespaces().items:
            print(f"[{i.metadata.namespace}] [{i.metadata.name}] {i.spec.cluster_ip} <{i.spec.ports[0].name}> {i.spec.ports[0].port} ---> {i.spec.ports[0].target_port}")

    # Output the pod log for given namespace
    def read_pod_log(slef, given_namespace:str, given_pod:str):
        pod_log = Api_Instance.read_namespaced_pod_log(name=given_pod,namespace=given_namespace)
        print(pod_log)


        
kubeInstance = KubeTool()
print(kubeInstance.read_pod_log("kube-system","etcd-minikube"))