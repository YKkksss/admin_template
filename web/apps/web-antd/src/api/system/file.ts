import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace SystemFileApi {
  export interface SysFile {
    [key: string]: any;
    id: string;
    originalName: string;
    fileName: string;
    ext?: string;
    mime?: string;
    size: number;
    storage: string;
    objectKey: string;
    remark?: string;
    creatorId?: string;
    creatorName?: string;
    deptId?: string;
    deptName?: string;
    createTime?: string;
  }
}

/**
 * 获取文件列表（分页）
 */
export async function getFileList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<SystemFileApi.SysFile>;
    total: number;
  }>('/system/file/list', { params });
}

/**
 * 上传文件
 */
export async function uploadFile(file: File, remark?: string) {
  const formData = new FormData();
  formData.append('file', file);
  if (remark) {
    formData.append('remark', remark);
  }
  return requestClient.post<SystemFileApi.SysFile>('/system/file/upload', formData);
}

/**
 * 删除单个文件
 */
export async function deleteFile(id: string) {
  return requestClient.delete(`/system/file/${id}`);
}

/**
 * 批量删除文件
 */
export async function batchDeleteFiles(ids: string[]) {
  return requestClient.post<number>('/system/file/batch-delete', {
    ids: ids.map((v) => Number(v)).filter(Boolean),
  });
}

