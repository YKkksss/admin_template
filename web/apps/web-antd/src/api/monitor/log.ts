import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace MonitorLogApi {
  export interface OperationLog {
    [key: string]: any;
    id: string;
    userId?: string;
    username?: string;
    module?: string;
    action?: string;
    method: string;
    url: string;
    ip?: string;
    requestData?: string;
    responseData?: string;
    status?: 0 | 1;
    duration?: number;
    createTime?: string;
  }

  export interface LoginLog {
    [key: string]: any;
    id: string;
    userId?: string;
    username?: string;
    ip?: string;
    location?: string;
    browser?: string;
    os?: string;
    status?: 0 | 1;
    message?: string;
    createTime?: string;
  }
}

export async function getOperationLogList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<MonitorLogApi.OperationLog>;
    total: number;
  }>('/monitor/operation-log/list', { params });
}

export async function deleteOperationLog(id: string) {
  return requestClient.delete(`/monitor/operation-log/${id}`);
}

export async function batchDeleteOperationLogs(ids: string[]) {
  return requestClient.post('/monitor/operation-log/batch-delete', { ids });
}

export async function clearOperationLogs() {
  return requestClient.post('/monitor/operation-log/clear');
}

export async function getLoginLogList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<MonitorLogApi.LoginLog>;
    total: number;
  }>('/monitor/login-log/list', { params });
}

export async function deleteLoginLog(id: string) {
  return requestClient.delete(`/monitor/login-log/${id}`);
}

export async function batchDeleteLoginLogs(ids: string[]) {
  return requestClient.post('/monitor/login-log/batch-delete', { ids });
}

export async function clearLoginLogs() {
  return requestClient.post('/monitor/login-log/clear');
}

