"""读取本机发布口令；口令文件位于仓库外，不打印或写入发布产物。"""
from __future__ import annotations

import os
from pathlib import Path
import stat

DEFAULT_ENV = 'ABS_DASHBOARD_PASSWORD'


def password_path() -> Path:
    return Path.home() / '.config' / 'abs-toolbox' / 'dashboard-password'


def load_password(env_name: str = DEFAULT_ENV) -> str:
    value = os.environ.get(env_name)
    if value:
        return value
    if env_name != DEFAULT_ENV:
        raise RuntimeError(f'未设置密码环境变量 {env_name}')
    path = password_path()
    try:
        with path.open('rb') as handle:
            info = os.fstat(handle.fileno())
            if (path.is_symlink() or not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
                raise RuntimeError('本机发布口令文件必须由当前用户所有、非符号链接且权限为600')
            value = handle.read().decode('utf-8').rstrip('\r\n')
    except FileNotFoundError:
        raise RuntimeError('未配置本机发布口令或ABS_DASHBOARD_PASSWORD') from None
    if not value:
        raise RuntimeError('本机发布口令为空')
    return value
