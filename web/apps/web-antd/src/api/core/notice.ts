import { requestClient } from '#/api/request';

export namespace NoticeApi {
  export type NoticeType = 1 | 2 | 3;

  export interface InboxItem {
    id: number;
    title: string;
    message: string;
    content?: string;
    type: NoticeType;
    link?: string | null;
    isRead: boolean;
    createTime: string;
    readTime?: string | null;
  }

  export interface InboxListParams {
    page: number;
    pageSize: number;
    keyword?: string;
    readStatus?: 'all' | 'read' | 'unread';
    type?: NoticeType;
  }

  export interface InboxListResult {
    items: InboxItem[];
    total: number;
  }

  export interface UnreadCountResult {
    unread: number;
    bellUnread: number;
  }

  export type SendScope = 'all' | 'dept' | 'user' | 'mixed' | 'unknown';

  export interface OutboxItem {
    id: number;
    title: string;
    message: string;
    type: NoticeType;
    link?: string | null;
    sendScope: SendScope;
    receiverCount: number;
    createTime: string;
  }

  export interface OutboxDetail extends OutboxItem {
    content: string;
    sendAll: boolean;
    deptIds: number[];
    userIds: number[];
    deptNames?: string[];
    userNames?: string[];
  }

  export interface OutboxListParams {
    page: number;
    pageSize: number;
    keyword?: string;
    type?: NoticeType;
  }

  export interface OutboxListResult {
    items: OutboxItem[];
    total: number;
  }

  export interface SendNoticeParams {
    title: string;
    content: string;
    message?: string;
    type?: NoticeType;
    link?: string;
    sendAll: boolean;
    deptIds: number[];
    userIds: number[];
  }

  export interface TargetDept {
    id: number | string;
    pid?: number | string;
    name: string;
    children?: TargetDept[];
  }

  export interface TargetUserOption {
    id: number | string;
    name: string;
    username?: string;
    realName?: string;
  }
}

/**
 * 获取铃铛未读消息列表（仅未读且未隐藏）
 */
export async function getBellNoticesApi() {
  return requestClient.get<NoticeApi.InboxItem[]>('/notice/bell');
}

/**
 * 清空铃铛列表（隐藏铃铛内所有消息，不改变已读状态）
 */
export async function clearBellNoticesApi() {
  return requestClient.post<boolean>('/notice/bell/clear');
}

/**
 * 铃铛全部已读（仅作用于铃铛当前展示的未读消息）
 */
export async function readAllBellNoticesApi() {
  return requestClient.post<boolean>('/notice/bell/read-all');
}

/**
 * 获取未读统计
 */
export async function getUnreadCountApi() {
  return requestClient.get<NoticeApi.UnreadCountResult>('/notice/unread-count');
}

/**
 * 获取收件箱列表（分页）
 */
export async function getInboxNoticesApi(params: NoticeApi.InboxListParams) {
  return requestClient.get<NoticeApi.InboxListResult>('/notice/inbox', {
    params,
  });
}

/**
 * 获取消息详情
 */
export async function getInboxNoticeDetailApi(id: number) {
  return requestClient.get<NoticeApi.InboxItem>(`/notice/inbox/${id}`);
}

/**
 * 标记单条消息已读
 */
export async function markInboxNoticeReadApi(id: number) {
  return requestClient.post<boolean>(`/notice/inbox/${id}/read`);
}

/**
 * 批量标记已读
 */
export async function markInboxNoticeReadBatchApi(ids: number[]) {
  return requestClient.post<number>('/notice/inbox/read-batch', { ids });
}

/**
 * 全部标记已读
 */
export async function markInboxNoticeReadAllApi() {
  return requestClient.post<number>('/notice/inbox/read-all');
}

/**
 * 删除单条消息
 */
export async function deleteInboxNoticeApi(id: number) {
  return requestClient.delete<boolean>(`/notice/inbox/${id}`);
}

/**
 * 批量删除消息
 */
export async function deleteInboxNoticeBatchApi(ids: number[]) {
  return requestClient.post<number>('/notice/inbox/delete-batch', { ids });
}

/**
 * 发布消息（需要发送权限）
 */
export async function sendNoticeApi(data: NoticeApi.SendNoticeParams) {
  return requestClient.post<number>('/system/notice/send', data);
}

/**
 * 获取我发布的消息列表（分页）
 */
export async function getOutboxNoticesApi(params: NoticeApi.OutboxListParams) {
  return requestClient.get<NoticeApi.OutboxListResult>('/system/notice/outbox', {
    params,
  });
}

/**
 * 获取我发布的消息详情
 */
export async function getOutboxNoticeDetailApi(id: number) {
  return requestClient.get<NoticeApi.OutboxDetail>(`/system/notice/outbox/${id}`);
}

/**
 * 获取消息发布可选部门树（需要发送权限）
 */
export async function getNoticeTargetDeptsApi() {
  return requestClient.get<NoticeApi.TargetDept[]>('/system/notice/targets/depts');
}

/**
 * 获取消息发布可选用户列表（需要发送权限）
 */
export async function getNoticeTargetUsersApi(arg?: any) {
  const kw =
    typeof arg === 'string'
      ? arg
      : typeof arg?.keyword === 'string'
        ? arg.keyword
        : undefined;

  return requestClient.get<NoticeApi.TargetUserOption[]>(
    '/system/notice/targets/users',
    {
      params: kw ? { keyword: kw } : {},
    },
  );
}
