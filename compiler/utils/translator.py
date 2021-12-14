import logging
from ruamel.yaml import YAML
from io import StringIO


def translate(deployment_format: str = None, topologody_metadata: dict = None, log: logging = None) -> str:
    if deployment_format is not None:
        log.info(f'Translating a {deployment_format} deployment')
    if deployment_format == 'kubernetes':
        adt = _translate('kubernetes', topologody_metadata, log)
        return _build_adt(adt, log)
    elif deployment_format == 'docker':
        adt = _translate('docker', topologody_metadata, log)
        return _build_adt(adt, log)
    else:
        log.warning(f'Topology format is undefined')
        topologody_type = _check_type(topologody_metadata, log)
        if topologody_type == 'kubernetes':
            adt = _translate('kubernetes', topologody_metadata, log)
            return _build_adt(adt, log)
        elif topologody_type == 'docker':
            adt = _translate('docker', topologody_metadata, log)
            return _build_adt(adt, log)
        else:
            log.debug("Wrong deploymentFormat! Please, specify \"docker\" or \"kubernetes\"!")
            raise Exception("Wrong deploymentFormat! Please, specify \"docker\" or \"kubernetes\"!")


def _build_adt(adt_in: dict,  log: logging = None) -> str:
    log.debug('Building the ADT')
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 800
    dt_stream = StringIO()
    yaml.dump(adt_in, dt_stream)
    adt_str = dt_stream.getvalue()
    adt = ''
    for line in adt_str.splitlines():
        adt = adt + '  ' + line + '\n'
    adt = adt[:adt.rfind('\n')]
    log.info('Translation completed successfully')
    return adt


def _check_type(topologody_metadata: dict = None, log: logging = None) -> str:
    log.warning(f'Trying to specify topology format')
    topology_type = None
    artifacts = list(topologody_metadata)
    if 'apiVersion' in artifacts:
        topology_type = "kubernetes"
    elif 'version' in artifacts:
        topology_type = "docker"
    return topology_type


def _translate(deployment_format: str, topologody_metadata: dict, log: logging = None) -> dict:
    adt = {"node_templates": {}}
    if deployment_format == 'kubernetes':
        try:
            log.debug(f'Translating a kubernetes manifest')
            name = topologody_metadata["metadata"]["name"].lower()
            kind = topologody_metadata["kind"].lower()
            name_kind = f'{name}-{kind}'
            if kind in ['deployment', 'pod', 'statefulset', 'daemonset']:
                topologody_metadata['metadata'].pop('annotations', None)
                topologody_metadata['metadata'].pop('creationTimestamp', None)
                topologody_metadata.pop('status', None)
                adt['node_templates'][name_kind] = {"type": "tosca.nodes.MiCADO.Kubernetes",
                                                    "interfaces": {"Kubernetes":
                                                                       {"create":
                                                                            {"inputs": topologody_metadata}}}, }
        except KeyError as e:
            log.debug("Wrong kubernetes manifest format!")
            raise e
    if deployment_format == 'docker':
        try:
            log.debug(f'Translating a docker compose')
            for service, values in topologody_metadata["services"].items():
                adt['node_templates'][service] = {'type': 'tosca.nodes.MiCADO.Container.Application.Docker.Deployment',
                                                  'properties': values}
            for volume, values in topologody_metadata.get("volumes",dict()).items():
                adt['node_templates'][volume] = {'type': 'tosca.nodes.MiCADO.Container.Volume', 'properties': values}
        except KeyError as e:
            log.debug("Wrong docker compose format!")
            raise e
    return adt
