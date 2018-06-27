import sys
import os
import tljh.systemd as systemd
import tljh.conda as conda
from tljh import user

INSTALL_PREFIX = os.environ.get('TLJH_INSTALL_PREFIX', '/opt/tljh')
HUB_ENV_PREFIX = os.path.join(INSTALL_PREFIX, 'hub')
USER_ENV_PREFIX = os.path.join(INSTALL_PREFIX, 'user')

HERE = os.path.abspath(os.path.dirname(__file__))


def ensure_jupyterhub_service(prefix):
    with open(os.path.join(HERE, 'systemd-units', 'jupyterhub.service')) as f:
        unit_template = f.read()

    unit = unit_template.format(
        python_interpreter_path=sys.executable,
        jupyterhub_config_path=os.path.join(HERE, 'jupyterhub_config.py'),
        install_prefix=INSTALL_PREFIX
    )
    systemd.install_unit('jupyterhub.service', unit)


def ensure_jupyterhub_package(prefix):
    """
    Install JupyterHub into our conda environment if needed.

    Conda constructor does not play well with conda-forge, so we can ship this
    with constructor
    """
    # FIXME: Use fully deterministic package lists here
    conda.ensure_conda_packages(prefix, ['jupyterhub==0.9.0'])
    conda.ensure_pip_packages(prefix, [
        'jupyterhub-dummyauthenticator==0.3.1',
        'jupyterhub-systemdspawner==0.9.12',
    ])


ensure_jupyterhub_package(HUB_ENV_PREFIX)
ensure_jupyterhub_service(HUB_ENV_PREFIX)

user.ensure_group('jupyterhub-admins')
user.ensure_group('jupyterhub-users')

with open('/etc/sudoers.d/jupyterhub-admins', 'w') as f:
    f.write('%jupyterhub-admins ALL = (ALL) NOPASSWD: ALL')

conda.ensure_conda_env(USER_ENV_PREFIX)
conda.ensure_conda_packages(USER_ENV_PREFIX, [
    'jupyterhub==0.9.0',
    'notebook==5.5.0'
])
systemd.reload_daemon()
systemd.start_service('jupyterhub')