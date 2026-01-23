import type { Recordable } from '@vben/types';

import { requestClient } from '#/api/request';

export namespace SystemDictApi {
  export interface DictType {
    [key: string]: any;
    id: string;
    name: string;
    code: string;
    status: 0 | 1;
    remark?: string;
    createTime?: string;
  }

  export interface DictData {
    [key: string]: any;
    id: string;
    typeCode: string;
    label: string;
    value: string;
    sort: number;
    status: 0 | 1;
    style?: string;
    remark?: string;
    createTime?: string;
  }

  export interface DictOptionItem {
    label: string;
    value: string;
    style?: string;
  }
}

// -----------------------------
// 字典类型
// -----------------------------

export async function getDictTypeList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<SystemDictApi.DictType>;
    total: number;
  }>('/system/dict/type/list', { params });
}

export async function getDictTypeOptions() {
  return requestClient.get<
    Array<Pick<SystemDictApi.DictType, 'id' | 'name' | 'code' | 'status'>>
  >('/system/dict/type/options');
}

export async function createDictType(data: Omit<SystemDictApi.DictType, 'id'>) {
  return requestClient.post('/system/dict/type', data);
}

export async function updateDictType(
  id: string,
  data: Partial<Omit<SystemDictApi.DictType, 'id'>>,
) {
  return requestClient.put(`/system/dict/type/${id}`, data);
}

export async function deleteDictType(id: string) {
  return requestClient.delete(`/system/dict/type/${id}`);
}

// -----------------------------
// 字典数据
// -----------------------------

export async function getDictDataList(params: Recordable<any>) {
  return requestClient.get<{
    items: Array<SystemDictApi.DictData>;
    total: number;
  }>('/system/dict/data/list', { params });
}

export async function createDictData(data: Omit<SystemDictApi.DictData, 'id'>) {
  return requestClient.post('/system/dict/data', data);
}

export async function updateDictData(
  id: string,
  data: Partial<Omit<SystemDictApi.DictData, 'id'>>,
) {
  return requestClient.put(`/system/dict/data/${id}`, data);
}

export async function deleteDictData(id: string) {
  return requestClient.delete(`/system/dict/data/${id}`);
}

export async function getDictOptions(typeCode: string) {
  return requestClient.get<Array<SystemDictApi.DictOptionItem>>(
    `/system/dict/data/options/${typeCode}`,
  );
}
