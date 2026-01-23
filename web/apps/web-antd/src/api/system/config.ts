import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace SystemConfigApi {
  export interface SystemConfig {
    [key: string]: any;
    id: string;
    configName: string;
    configKey: string;
    configValue: string;
    status: 0 | 1;
    remark?: string;
    isBuiltin?: boolean;
    createTime?: string;
  }
}

/**
 * 获取系统配置列表
 */
export async function getConfigList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<SystemConfigApi.SystemConfig>;
    total: number;
  }>('/system/config/list', { params });
}

/**
 * 创建系统配置
 */
export async function createConfig(
  data: Omit<SystemConfigApi.SystemConfig, 'id' | 'createTime'>,
) {
  return requestClient.post('/system/config', data);
}

/**
 * 更新系统配置
 */
export async function updateConfig(
  id: string,
  data: Partial<Omit<SystemConfigApi.SystemConfig, 'id' | 'createTime'>>,
) {
  return requestClient.put(`/system/config/${id}`, data);
}

/**
 * 删除系统配置
 */
export async function deleteConfig(id: string) {
  return requestClient.delete(`/system/config/${id}`);
}

