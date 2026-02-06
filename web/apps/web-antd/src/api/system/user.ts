import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace SystemUserApi {
  export interface SystemUser {
    [key: string]: any;
    id: string;
    username: string;
    realName: string;
    status: 0 | 1;
    deptId?: number | string | null;
    deptName?: string | null;
    roleIds: Array<number | string>;
    roleNames?: string[];
    avatar?: string | null;
    homePath?: string | null;
    createTime?: string;
  }

  export interface ImportErrorItem {
    row: number;
    message: string;
    column?: string | null;
  }

  export interface ImportResult {
    total: number;
    success: number;
    failed: number;
    errors: ImportErrorItem[];
  }
}

/**
 * 获取用户列表数据
 */
async function getUserList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<SystemUserApi.SystemUser>;
    total: number;
  }>('/system/user/list', { params });
}

/**
 * 创建用户
 */
async function createUser(data: Recordable<any>) {
  return requestClient.post('/system/user', data);
}

/**
 * 更新用户
 */
async function updateUser(id: string, data: Recordable<any>) {
  return requestClient.put(`/system/user/${id}`, data);
}

/**
 * 删除用户
 */
async function deleteUser(id: string) {
  return requestClient.delete(`/system/user/${id}`);
}

/**
 * 重置用户密码
 */
async function resetUserPassword(id: string, password: string) {
  return requestClient.post(`/system/user/${id}/reset-password`, { password });
}

/**
 * 获取用户选项（用于下拉选择）
 */
async function getUserOptions(arg?: any) {
  const kw =
    typeof arg === 'string'
      ? arg
      : typeof arg?.keyword === 'string'
        ? arg.keyword
        : undefined;

  return requestClient.get<Array<{ id: string; name: string }>>(
    '/system/user/options',
    {
      params: kw ? { keyword: kw } : {},
    },
  );
}

/**
 * 批量导入用户（Excel）
 */
async function importUsers(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  return requestClient.post<SystemUserApi.ImportResult>(
    '/system/user/import',
    formData,
  );
}

export {
  createUser,
  deleteUser,
  getUserList,
  getUserOptions,
  importUsers,
  resetUserPassword,
  updateUser,
};
