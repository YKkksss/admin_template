"""开发期数据初始化（播种）。"""

from __future__ import annotations

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.config import Config
from app.models.dept import Dept
from app.models.dict import DictData, DictType
from app.models.menu import Menu
from app.models.role import Role
from app.models.user import User


async def _get_or_create_menu(
    *,
    name: str,
    defaults: dict,
    parent: Menu | None = None,
) -> Menu:
    menu = await Menu.get_or_none(name=name)
    if menu:
        return menu

    menu_path = defaults.get("path")
    if menu_path:
        by_path = await Menu.get_or_none(path=menu_path)
        if by_path:
            return by_path

    return await Menu.create(name=name, parent=parent, **defaults)


async def seed_system_menus_and_roles() -> None:
    """
    初始化系统菜单与默认角色授权（仅开发环境建议启用）。

    说明：
    - 以“尽量幂等”的方式播种：已存在的数据不会覆盖，只会补齐缺失的默认项；
    - 超级管理员默认拥有全部权限（不依赖 sys_role_menu 配置）；
    - 普通用户默认可访问：工作台、分析页。
    """

    # 顶级菜单：工作台
    workspace = await _get_or_create_menu(
        name="Workspace",
        defaults={
            "type": "menu",
            "path": "/workspace",
            "component": "/dashboard/workspace/index",
            "meta": {
                "icon": "carbon:workspace",
                "title": "page.dashboard.workspace",
                "order": 0,
            },
            "status": 1,
        },
    )

    # 顶级菜单：分析页
    analytics = await _get_or_create_menu(
        name="Analytics",
        defaults={
            "type": "menu",
            "path": "/analytics",
            "component": "/dashboard/analytics/index",
            "meta": {
                "icon": "lucide:area-chart",
                "title": "page.dashboard.analytics",
                "order": -1,
                "affixTab": True,
            },
            "status": 1,
        },
    )

    # 系统管理目录
    system_catalog = await _get_or_create_menu(
        name="System",
        defaults={
            "type": "catalog",
            "path": "/system",
            "meta": {"icon": "ion:settings-outline", "title": "system.title", "order": 9997},
            "status": 1,
        },
    )

    # 系统管理子目录：日志审计（放在系统管理下）
    expected_monitor_path = "/system/monitor"
    monitor_catalog = await _get_or_create_menu(
        name="Monitor",
        parent=system_catalog,
        defaults={
            "type": "catalog",
            "path": expected_monitor_path,
            "meta": {"icon": "carbon:log", "title": "monitor.title", "order": 9996},
            "status": 1,
        },
    )

    # 兼容旧数据：将历史的 /monitor 迁移到 /system/monitor，并挂载到 System 目录下
    monitor_update_fields: list[str] = []
    if monitor_catalog.parent_id != system_catalog.id:
        monitor_catalog.parent_id = system_catalog.id
        monitor_update_fields.append("parent_id")
    if monitor_catalog.path != expected_monitor_path:
        conflict = await Menu.get_or_none(path=expected_monitor_path)
        if not conflict or conflict.id == monitor_catalog.id:
            monitor_catalog.path = expected_monitor_path
            monitor_update_fields.append("path")
    if monitor_update_fields:
        await monitor_catalog.save(update_fields=monitor_update_fields)

    # 顶级目录：系统工具
    system_tools_catalog = await _get_or_create_menu(
        name="SystemTools",
        defaults={
            "type": "catalog",
            "path": "/system-tools",
            "meta": {"icon": "carbon:tools", "title": "system.tools.title", "order": 9998},
            "status": 1,
        },
    )

    # 系统工具：表单生成
    system_tools_form_generator = await _get_or_create_menu(
        name="SystemToolsFormGenerator",
        parent=system_tools_catalog,
        defaults={
            "type": "menu",
            "path": "/system-tools/form-generator",
            "component": "/system-tools/form-generator/index",
            "meta": {
                "icon": "carbon:application-web",
                "title": "system.tools.formGenerator",
                "order": 0,
            },
            "status": 1,
        },
    )

    # 系统管理子菜单：消息通知（所有用户可见）
    expected_notice_path = "/system/notice"
    notice_menu = await _get_or_create_menu(
        name="Notice",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": expected_notice_path,
            "component": "/notice/list",
            "meta": {
                "icon": "carbon:notification",
                "title": "page.notice.title",
                "order": 10,
            },
            "status": 1,
        },
    )

    # 兼容旧数据：将历史的 /notice 迁移到 /system/notice，并挂载到 System 目录下
    notice_update_fields: list[str] = []
    if notice_menu.parent_id != system_catalog.id:
        notice_menu.parent_id = system_catalog.id
        notice_update_fields.append("parent_id")
    if notice_menu.path != expected_notice_path:
        conflict = await Menu.get_or_none(path=expected_notice_path)
        if not conflict or conflict.id == notice_menu.id:
            notice_menu.path = expected_notice_path
            notice_update_fields.append("path")
    if notice_update_fields:
        await notice_menu.save(update_fields=notice_update_fields)

    # 系统管理子菜单：消息发布（仅有发送权限的用户可见）
    expected_notice_publish_path = "/system/notice/publish"
    notice_publish_menu = await _get_or_create_menu(
        name="NoticePublish",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": expected_notice_publish_path,
            "component": "/notice/publish/list",
            "meta": {
                "icon": "carbon:send-alt",
                "title": "page.notice.publish",
                "order": 11,
            },
            "status": 1,
        },
    )

    # 兼容旧数据：将历史的 /notice/publish 迁移到 /system/notice/publish，并挂载到 System 目录下
    notice_publish_update_fields: list[str] = []
    if notice_publish_menu.parent_id != system_catalog.id:
        notice_publish_menu.parent_id = system_catalog.id
        notice_publish_update_fields.append("parent_id")
    if notice_publish_menu.path != expected_notice_publish_path:
        conflict = await Menu.get_or_none(path=expected_notice_publish_path)
        if not conflict or conflict.id == notice_publish_menu.id:
            notice_publish_menu.path = expected_notice_publish_path
            notice_publish_update_fields.append("path")
    if notice_publish_update_fields:
        await notice_publish_menu.save(update_fields=notice_publish_update_fields)

    # 数据字典（合并为单菜单：点击进入“字典类型”列表；字典数据页作为隐藏路由跳转页）
    expected_dict_path = "/system/dict"
    expected_dict_component = "/system/dict/type/list"
    dict_type_list_code = "System:DictType:List"

    system_dict = await _get_or_create_menu(
        name="SystemDict",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": expected_dict_path,
            "component": expected_dict_component,
            "meta": {"icon": "carbon:catalog", "title": "system.dict.title", "order": 20},
            "status": 1,
        },
    )

    # 兼容旧数据：SystemDict 可能是 catalog，需要迁移成 menu
    dict_update_fields: list[str] = []
    if system_dict.parent_id != system_catalog.id:
        system_dict.parent_id = system_catalog.id
        dict_update_fields.append("parent_id")
    if system_dict.type != "menu":
        system_dict.type = "menu"
        dict_update_fields.append("type")
    if system_dict.path != expected_dict_path:
        conflict = await Menu.get_or_none(path=expected_dict_path)
        if not conflict or conflict.id == system_dict.id:
            system_dict.path = expected_dict_path
            dict_update_fields.append("path")
    if system_dict.component != expected_dict_component:
        system_dict.component = expected_dict_component
        dict_update_fields.append("component")

    dict_meta = dict(system_dict.meta or {})
    if dict_meta.get("icon") != "carbon:catalog":
        dict_meta["icon"] = "carbon:catalog"
    if dict_meta.get("title") != "system.dict.title":
        dict_meta["title"] = "system.dict.title"
    dict_meta.setdefault("order", 20)
    dict_meta["hideChildrenInMenu"] = True
    if dict_meta != (system_dict.meta or {}):
        system_dict.meta = dict_meta
        dict_update_fields.append("meta")

    # 迁移权限码：将 System:DictType:List 从旧的 SystemDictType 挪到 SystemDict（避免权限点漂移）
    if system_dict.auth_code != dict_type_list_code:
        can_set_auth = True
        holder = await Menu.get_or_none(auth_code=dict_type_list_code)
        if holder and holder.id != system_dict.id:
            if holder.name == "SystemDictType":
                holder.auth_code = None
                await holder.save(update_fields=["auth_code"])
            else:
                can_set_auth = False
        if can_set_auth:
            system_dict.auth_code = dict_type_list_code
            dict_update_fields.append("auth_code")

    if dict_update_fields:
        await system_dict.save(update_fields=dict_update_fields)

    # 兼容旧数据：如果还存在旧的 SystemDictType 菜单，则将其隐藏并挂载到 System 目录下。
    # 说明：保留历史路由可访问，避免老链接/书签失效。
    legacy_dict_type = await Menu.get_or_none(name="SystemDictType")
    if legacy_dict_type:
        legacy_update_fields: list[str] = []
        if legacy_dict_type.parent_id != system_catalog.id:
            legacy_dict_type.parent_id = system_catalog.id
            legacy_update_fields.append("parent_id")
        legacy_meta = dict(legacy_dict_type.meta or {})
        if legacy_meta.get("hideInMenu") is not True:
            legacy_meta["hideInMenu"] = True
            legacy_dict_type.meta = legacy_meta
            legacy_update_fields.append("meta")
        if legacy_dict_type.active_path != expected_dict_path:
            legacy_dict_type.active_path = expected_dict_path
            legacy_update_fields.append("active_path")
        if legacy_update_fields:
            await legacy_dict_type.save(update_fields=legacy_update_fields)

    # 字典类型按钮权限点（挂载到 SystemDict 菜单下）
    system_dict_type_create = await _get_or_create_menu(
        name="SystemDictTypeCreate",
        parent=system_dict,
        defaults={
            "type": "button",
            "auth_code": "System:DictType:Create",
            "meta": {"title": "common.create"},
            "status": 1,
        },
    )
    if system_dict_type_create.parent_id != system_dict.id:
        system_dict_type_create.parent_id = system_dict.id
        await system_dict_type_create.save(update_fields=["parent_id"])
    system_dict_type_edit = await _get_or_create_menu(
        name="SystemDictTypeEdit",
        parent=system_dict,
        defaults={
            "type": "button",
            "auth_code": "System:DictType:Edit",
            "meta": {"title": "common.edit"},
            "status": 1,
        },
    )
    if system_dict_type_edit.parent_id != system_dict.id:
        system_dict_type_edit.parent_id = system_dict.id
        await system_dict_type_edit.save(update_fields=["parent_id"])
    system_dict_type_delete = await _get_or_create_menu(
        name="SystemDictTypeDelete",
        parent=system_dict,
        defaults={
            "type": "button",
            "auth_code": "System:DictType:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )
    if system_dict_type_delete.parent_id != system_dict.id:
        system_dict_type_delete.parent_id = system_dict.id
        await system_dict_type_delete.save(update_fields=["parent_id"])

    # 字典数据（隐藏菜单，仅用于跳转与路由注册）
    system_dict_data = await _get_or_create_menu(
        name="SystemDictData",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/dict/data",
            "component": "/system/dict/data/list",
            "active_path": expected_dict_path,
            "auth_code": "System:DictData:List",
            "meta": {
                "icon": "carbon:data-blob",
                "title": "system.dict.data.title",
                "hideInMenu": True,
            },
            "status": 1,
        },
    )
    dict_data_update_fields: list[str] = []
    if system_dict_data.parent_id != system_catalog.id:
        system_dict_data.parent_id = system_catalog.id
        dict_data_update_fields.append("parent_id")
    if system_dict_data.active_path != expected_dict_path:
        system_dict_data.active_path = expected_dict_path
        dict_data_update_fields.append("active_path")
    dict_data_meta = dict(system_dict_data.meta or {})
    if dict_data_meta.get("hideInMenu") is not True:
        dict_data_meta["hideInMenu"] = True
    if dict_data_meta.get("title") != "system.dict.data.title":
        dict_data_meta["title"] = "system.dict.data.title"
    if dict_data_meta.get("icon") != "carbon:data-blob":
        dict_data_meta["icon"] = "carbon:data-blob"
    if dict_data_meta != (system_dict_data.meta or {}):
        system_dict_data.meta = dict_data_meta
        dict_data_update_fields.append("meta")
    if dict_data_update_fields:
        await system_dict_data.save(update_fields=dict_data_update_fields)

    system_dict_data_create = await _get_or_create_menu(
        name="SystemDictDataCreate",
        parent=system_dict_data,
        defaults={
            "type": "button",
            "auth_code": "System:DictData:Create",
            "meta": {"title": "common.create"},
            "status": 1,
        },
    )
    if system_dict_data_create.parent_id != system_dict_data.id:
        system_dict_data_create.parent_id = system_dict_data.id
        await system_dict_data_create.save(update_fields=["parent_id"])
    system_dict_data_edit = await _get_or_create_menu(
        name="SystemDictDataEdit",
        parent=system_dict_data,
        defaults={
            "type": "button",
            "auth_code": "System:DictData:Edit",
            "meta": {"title": "common.edit"},
            "status": 1,
        },
    )
    if system_dict_data_edit.parent_id != system_dict_data.id:
        system_dict_data_edit.parent_id = system_dict_data.id
        await system_dict_data_edit.save(update_fields=["parent_id"])
    system_dict_data_delete = await _get_or_create_menu(
        name="SystemDictDataDelete",
        parent=system_dict_data,
        defaults={
            "type": "button",
            "auth_code": "System:DictData:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )
    if system_dict_data_delete.parent_id != system_dict_data.id:
        system_dict_data_delete.parent_id = system_dict_data.id
        await system_dict_data_delete.save(update_fields=["parent_id"])

    # 参数配置
    system_config = await _get_or_create_menu(
        name="SystemConfig",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/config",
            "component": "/system/config/list",
            "auth_code": "System:Config:List",
            "meta": {"icon": "carbon:settings-services", "title": "system.config.title"},
            "status": 1,
        },
    )
    system_config_create = await _get_or_create_menu(
        name="SystemConfigCreate",
        parent=system_config,
        defaults={
            "type": "button",
            "auth_code": "System:Config:Create",
            "meta": {"title": "common.create"},
            "status": 1,
        },
    )
    system_config_edit = await _get_or_create_menu(
        name="SystemConfigEdit",
        parent=system_config,
        defaults={
            "type": "button",
            "auth_code": "System:Config:Edit",
            "meta": {"title": "common.edit"},
            "status": 1,
        },
    )
    system_config_delete = await _get_or_create_menu(
        name="SystemConfigDelete",
        parent=system_config,
        defaults={
            "type": "button",
            "auth_code": "System:Config:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )

    # 菜单管理
    system_menu = await _get_or_create_menu(
        name="SystemMenu",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/menu",
            "component": "/system/menu/list",
            "auth_code": "System:Menu:List",
            "meta": {"icon": "mdi:menu", "title": "system.menu.title"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemMenuCreate",
        parent=system_menu,
        defaults={
            "type": "button",
            "auth_code": "System:Menu:Create",
            "meta": {"title": "common.create"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemMenuEdit",
        parent=system_menu,
        defaults={
            "type": "button",
            "auth_code": "System:Menu:Edit",
            "meta": {"title": "common.edit"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemMenuDelete",
        parent=system_menu,
        defaults={
            "type": "button",
            "auth_code": "System:Menu:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )

    # 角色管理
    system_role = await _get_or_create_menu(
        name="SystemRole",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/role",
            "component": "/system/role/list",
            "auth_code": "System:Role:List",
            "meta": {"icon": "mdi:account-group", "title": "system.role.title"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemRoleCreate",
        parent=system_role,
        defaults={
            "type": "button",
            "auth_code": "System:Role:Create",
            "meta": {"title": "common.create"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemRoleEdit",
        parent=system_role,
        defaults={
            "type": "button",
            "auth_code": "System:Role:Edit",
            "meta": {"title": "common.edit"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemRoleDelete",
        parent=system_role,
        defaults={
            "type": "button",
            "auth_code": "System:Role:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )

    # 部门管理（模板示例）
    system_dept = await _get_or_create_menu(
        name="SystemDept",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/dept",
            "component": "/system/dept/list",
            "auth_code": "System:Dept:List",
            "meta": {"icon": "mdi:source-branch", "title": "system.dept.title"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemDeptCreate",
        parent=system_dept,
        defaults={
            "type": "button",
            "auth_code": "System:Dept:Create",
            "meta": {"title": "common.create"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemDeptEdit",
        parent=system_dept,
        defaults={
            "type": "button",
            "auth_code": "System:Dept:Edit",
            "meta": {"title": "common.edit"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemDeptDelete",
        parent=system_dept,
        defaults={
            "type": "button",
            "auth_code": "System:Dept:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )

    # 用户管理
    system_user = await _get_or_create_menu(
        name="SystemUser",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/user",
            "component": "/system/user/list",
            "auth_code": "System:User:List",
            "meta": {"icon": "mdi:account", "title": "system.user.title"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemUserCreate",
        parent=system_user,
        defaults={
            "type": "button",
            "auth_code": "System:User:Create",
            "meta": {"title": "common.create"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemUserEdit",
        parent=system_user,
        defaults={
            "type": "button",
            "auth_code": "System:User:Edit",
            "meta": {"title": "common.edit"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemUserDelete",
        parent=system_user,
        defaults={
            "type": "button",
            "auth_code": "System:User:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemUserResetPassword",
        parent=system_user,
        defaults={
            "type": "button",
            "auth_code": "System:User:ResetPassword",
            "meta": {"title": "system.user.resetPassword"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemUserImport",
        parent=system_user,
        defaults={
            "type": "button",
            "auth_code": "System:User:Import",
            "meta": {"title": "system.user.import"},
            "status": 1,
        },
    )
    await _get_or_create_menu(
        name="SystemUserExport",
        parent=system_user,
        defaults={
            "type": "button",
            "auth_code": "System:User:Export",
            "meta": {"title": "system.user.export"},
            "status": 1,
        },
    )

    # 在线用户/会话管理
    system_session = await _get_or_create_menu(
        name="SystemSession",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/session",
            "component": "/system/session/list",
            "auth_code": "System:Session:List",
            "meta": {"icon": "carbon:user-activity", "title": "system.session.title", "order": 30},
            "status": 1,
        },
    )
    system_session_kick = await _get_or_create_menu(
        name="SystemSessionKick",
        parent=system_session,
        defaults={
            "type": "button",
            "auth_code": "System:Session:Kick",
            "meta": {"title": "system.session.kick"},
            "status": 1,
        },
    )

    # 文件/附件管理
    system_file = await _get_or_create_menu(
        name="SystemFile",
        parent=system_catalog,
        defaults={
            "type": "menu",
            "path": "/system/file",
            "component": "/system/file/list",
            "auth_code": "System:File:List",
            "meta": {
                "icon": "carbon:document-attachment",
                "title": "system.file.title",
                "order": 25,
            },
            "status": 1,
        },
    )
    system_file_upload = await _get_or_create_menu(
        name="SystemFileUpload",
        parent=system_file,
        defaults={
            "type": "button",
            "auth_code": "System:File:Upload",
            "meta": {"title": "system.file.upload"},
            "status": 1,
        },
    )
    system_file_download = await _get_or_create_menu(
        name="SystemFileDownload",
        parent=system_file,
        defaults={
            "type": "button",
            "auth_code": "System:File:Download",
            "meta": {"title": "system.file.download"},
            "status": 1,
        },
    )
    system_file_delete = await _get_or_create_menu(
        name="SystemFileDelete",
        parent=system_file,
        defaults={
            "type": "button",
            "auth_code": "System:File:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )

    # 消息通知：发送权限（仅管理员/超级管理员使用）
    notice_send = await _get_or_create_menu(
        name="NoticeSend",
        parent=notice_menu,
        defaults={
            "type": "button",
            "auth_code": "System:Notice:Send",
            "meta": {"title": "system.notice.send"},
            "status": 1,
        },
    )

    # 日志审计：操作日志
    expected_operation_log_path = "/system/monitor/operation-log"
    monitor_operation_log = await _get_or_create_menu(
        name="MonitorOperationLog",
        parent=monitor_catalog,
        defaults={
            "type": "menu",
            "path": expected_operation_log_path,
            "component": "/monitor/operation-log/list",
            "auth_code": "Monitor:OperationLog:List",
            "meta": {"icon": "carbon:task-tools", "title": "monitor.operationLog.title"},
            "status": 1,
        },
    )
    # 兼容旧数据：迁移 /monitor/operation-log 到 /system/monitor/operation-log
    operation_log_update_fields: list[str] = []
    if monitor_operation_log.parent_id != monitor_catalog.id:
        monitor_operation_log.parent_id = monitor_catalog.id
        operation_log_update_fields.append("parent_id")
    if monitor_operation_log.path != expected_operation_log_path:
        conflict = await Menu.get_or_none(path=expected_operation_log_path)
        if not conflict or conflict.id == monitor_operation_log.id:
            monitor_operation_log.path = expected_operation_log_path
            operation_log_update_fields.append("path")
    if operation_log_update_fields:
        await monitor_operation_log.save(update_fields=operation_log_update_fields)
    monitor_operation_log_delete = await _get_or_create_menu(
        name="MonitorOperationLogDelete",
        parent=monitor_operation_log,
        defaults={
            "type": "button",
            "auth_code": "Monitor:OperationLog:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )

    # 日志审计：登录日志
    expected_login_log_path = "/system/monitor/login-log"
    monitor_login_log = await _get_or_create_menu(
        name="MonitorLoginLog",
        parent=monitor_catalog,
        defaults={
            "type": "menu",
            "path": expected_login_log_path,
            "component": "/monitor/login-log/list",
            "auth_code": "Monitor:LoginLog:List",
            "meta": {"icon": "carbon:login", "title": "monitor.loginLog.title"},
            "status": 1,
        },
    )
    # 兼容旧数据：迁移 /monitor/login-log 到 /system/monitor/login-log
    login_log_update_fields: list[str] = []
    if monitor_login_log.parent_id != monitor_catalog.id:
        monitor_login_log.parent_id = monitor_catalog.id
        login_log_update_fields.append("parent_id")
    if monitor_login_log.path != expected_login_log_path:
        conflict = await Menu.get_or_none(path=expected_login_log_path)
        if not conflict or conflict.id == monitor_login_log.id:
            monitor_login_log.path = expected_login_log_path
            login_log_update_fields.append("path")
    if login_log_update_fields:
        await monitor_login_log.save(update_fields=login_log_update_fields)
    monitor_login_log_delete = await _get_or_create_menu(
        name="MonitorLoginLogDelete",
        parent=monitor_login_log,
        defaults={
            "type": "button",
            "auth_code": "Monitor:LoginLog:Delete",
            "meta": {"title": "common.delete"},
            "status": 1,
        },
    )

    # 默认角色：user
    user_role, _ = await Role.get_or_create(code="user", defaults={"name": "普通用户"})
    if user_role.data_scope != "self":
        user_role.data_scope = "self"
        await user_role.save(update_fields=["data_scope"])
    await user_role.menus.add(workspace, analytics, notice_menu)

    # 默认角色：admin（可选）
    admin_role, _ = await Role.get_or_create(code="admin", defaults={"name": "管理员"})
    if admin_role.data_scope != "all":
        admin_role.data_scope = "all"
        await admin_role.save(update_fields=["data_scope"])
    await admin_role.menus.add(
        workspace,
        analytics,
        notice_menu,
        notice_publish_menu,
        notice_send,
        system_menu,
        system_role,
        system_dept,
        system_user,
        system_session,
        system_session_kick,
        system_file,
        system_file_upload,
        system_file_download,
        system_file_delete,
        system_dict,
        system_dict_data,
        system_dict_type_create,
        system_dict_type_edit,
        system_dict_type_delete,
        system_dict_data_create,
        system_dict_data_edit,
        system_dict_data_delete,
        system_config,
        system_config_create,
        system_config_edit,
        system_config_delete,
        monitor_operation_log,
        monitor_login_log,
        monitor_operation_log_delete,
        monitor_login_log_delete,
        system_tools_form_generator,
    )

    # 兼容旧授权：若历史角色授权过 SystemDictType，则同步授予新的 SystemDict（保证合并菜单后仍可见）
    if legacy_dict_type:
        legacy_roles = await Role.filter(menus__id=legacy_dict_type.id).all()
        for role in legacy_roles:
            if not await role.menus.filter(id=system_dict.id).exists():
                await role.menus.add(system_dict)

    # 示例部门数据：仅当 sys_dept 为空时初始化
    if await Dept.all().count() == 0:
        root = await Dept.create(name="总部", status=1, remark="根部门")
        await Dept.create(name="技术部", status=1, remark="示例部门", parent=root)
        await Dept.create(name="运营部", status=1, remark="示例部门", parent=root)

    # 内置字典（按需补齐，尽量幂等）
    yes_no, _ = await DictType.get_or_create(
        code="sys_yes_no",
        defaults={"name": "是否选项", "status": 1},
    )
    await DictData.get_or_create(
        type_code=yes_no.code,
        value="0",
        defaults={"label": "否", "sort": 0, "status": 1},
    )
    await DictData.get_or_create(
        type_code=yes_no.code,
        value="1",
        defaults={"label": "是", "sort": 1, "status": 1},
    )

    common_status, _ = await DictType.get_or_create(
        code="sys_common_status",
        defaults={"name": "通用状态", "status": 1},
    )
    await DictData.get_or_create(
        type_code=common_status.code,
        value="0",
        defaults={"label": "禁用", "sort": 0, "status": 1},
    )
    await DictData.get_or_create(
        type_code=common_status.code,
        value="1",
        defaults={"label": "启用", "sort": 1, "status": 1},
    )

    # 内置系统配置（按需补齐，尽量幂等）
    await Config.get_or_create(
        key="site_name",
        defaults={
            "name": "站点名称",
            "value": "Admin Template",
            "status": 1,
            "is_builtin": True,
        },
    )

    # 内置系统配置：登录模式（single=单端登录，multi=多端登录）
    await Config.get_or_create(
        key="auth.login.mode",
        defaults={
            "name": "登录模式",
            "value": "multi",
            "status": 1,
            "is_builtin": True,
            "remark": "single=单端登录，multi=多端登录",
        },
    )


async def seed_superuser() -> None:
    """
    初始化超级管理员账号（仅开发环境建议启用）。

    说明：
    - 由环境变量控制是否启用：INIT_SUPERUSER=true
    - 密码必须通过环境变量提供：SUPERUSER_PASSWORD=...
    - 该逻辑会尽量保持幂等：重复启动不会创建重复数据
    """

    if not settings.DEBUG:
        return
    if not settings.INIT_SUPERUSER:
        return
    if not settings.SUPERUSER_PASSWORD:
        return

    role, _ = await Role.get_or_create(
        code=settings.SUPERUSER_ROLE_CODE,
        defaults={"name": settings.SUPERUSER_ROLE_NAME},
    )
    if role.data_scope != "all":
        role.data_scope = "all"
        await role.save(update_fields=["data_scope"])

    user = await User.get_or_none(username=settings.SUPERUSER_USERNAME)
    if not user:
        user = await User.create(
            username=settings.SUPERUSER_USERNAME,
            password_hash=get_password_hash(settings.SUPERUSER_PASSWORD),
            real_name=settings.SUPERUSER_REAL_NAME,
            avatar=settings.SUPERUSER_AVATAR,
            home_path=settings.SUPERUSER_HOME_PATH,
            is_active=True,
        )

    # 确保用户具备超级管理员角色
    if not await user.roles.filter(id=role.id).exists():
        await user.roles.add(role)

    # 初始化系统菜单与默认角色授权（仅首次）
    await seed_system_menus_and_roles()
