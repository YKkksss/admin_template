import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace SystemSessionApi {
  export interface Session {
    [key: string]: any;
    id: number;
    username: string;
    ip?: string;
    browser?: string;
    os?: string;
    loginTime?: string;
    lastActiveTime?: string;
    expireTime?: string;
    status?: 0 | 1;
    revokeReason?: string;
    isCurrent?: boolean;
  }
}

export async function getSessionList(params: Recordable<any>) {
  return requestClient.get<{ items: Array<SystemSessionApi.Session>; total: number }>(
    '/system/session/list',
    { params },
  );
}

export async function kickSession(id: number, reason?: string) {
  return requestClient.delete(`/system/session/${id}`, {
    params: reason ? { reason } : undefined,
  });
}

export async function batchKickSessions(ids: number[], reason?: string) {
  return requestClient.post<number>('/system/session/batch-kick', { ids, reason });
}

