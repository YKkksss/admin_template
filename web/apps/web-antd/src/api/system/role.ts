import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace SystemRoleApi {
  export type RoleDataScope =
    | 'all'
    | 'custom'
    | 'dept'
    | 'dept_and_children'
    | 'self';

  export interface SystemRole {
    [key: string]: any;
    id: string;
    name: string;
    permissions: Array<number | string>;
    dataScope?: RoleDataScope;
    deptIds?: Array<number | string>;
    remark?: string;
    status: 0 | 1;
    createTime?: string;
  }

  export interface SystemRoleOption {
    [key: string]: any;
    id: string;
    name: string;
    code: string;
    status: 0 | 1;
  }
}

/**
 * 获取角色列表数据
 */
async function getRoleList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<SystemRoleApi.SystemRole>;
    total: number;
  }>('/system/role/list', { params });
}

/**
 * 创建角色
 * @param data 角色数据
 */
async function createRole(data: Omit<SystemRoleApi.SystemRole, 'id'>) {
  return requestClient.post('/system/role', data);
}

/**
 * 更新角色
 *
 * @param id 角色 ID
 * @param data 角色数据
 */
async function updateRole(
  id: string,
  data: Partial<Omit<SystemRoleApi.SystemRole, 'id'>>,
) {
  return requestClient.put(`/system/role/${id}`, data);
}

/**
 * 删除角色
 * @param id 角色 ID
 */
async function deleteRole(id: string) {
  return requestClient.delete(`/system/role/${id}`);
}

/**
 * 获取角色选项（用于下拉选择）
 */
async function getRoleOptions() {
  return requestClient.get<Array<SystemRoleApi.SystemRoleOption>>(
    '/system/role/options',
  );
}

export { createRole, deleteRole, getRoleList, getRoleOptions, updateRole };
